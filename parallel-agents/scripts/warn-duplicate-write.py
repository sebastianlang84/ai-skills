#!/usr/bin/env python3
"""Hook: refuse to create a file another live session already has, until you have read theirs.

Registered twice in ~/.claude/settings.json and dispatching on `hook_event_name`:
  PreToolUse  / Write  — deny a colliding creation, naming the file to read first
  PostToolUse / Read   — record that the sibling version was read, which lifts the denial

WHAT IT IS FOR
Three to five agents run on this machine at once, in sibling git worktrees of one repo. Worktree
isolation prevents *interference* — two agents disturbing each other's working tree — and does
nothing about *duplication*. Two sessions creating the same new file is invisible to Git, because an
add/add divergence does not exist until both sides do; it surfaces at merge, after both sides have
paid. That happened on 2026-08-14 in ~/dev/brain to two sessions each following the isolation rules
perfectly.

WHY IT DENIES RATHER THAN WARNS
The first version of this hook allowed the write and attached a note saying "read that version
first". A cross-vendor review pointed out that this is temporally impossible, and a live test
confirmed it: the write completes, and the model only sees the note on its next turn, next to the
tool result. The merge risk was caught; the duplicated file and the duplicated work — the actual
costs — were not. So a high-confidence collision is refused.

Denying costs the operator nothing. Exit-style denial cancels one tool call and hands the reason
back to the model, which can act on it unattended; it is not a permission prompt and does not wake
anyone. The unlock is deliberately NOT "the model tried again": a blind retry stays denied. It is a
successful Read of the named sibling file, which is the thing we actually wanted to happen.

WHY ONLY HIGH-CONFIDENCE EVIDENCE
An earlier draft also searched the whole history (`git log --all -- <path>`). That is worthless as
evidence and was removed: it reports a file deleted two years ago forever, and the branch list it
printed came from `--contains <commit>`, which says a branch contains the commit that touched the
path — not that the branch tip has the file. Now the only evidence that gates is a path that exists
in an *attached sibling worktree*, is a *new addition* there relative to the merge base, and that
worktree is held by a **live session** — a fact from ownership.py (pid alive, start time still
matching what the session recorded), not the file-mtime guess an earlier version used. An abandoned
worktree therefore never blocks a legitimate recreation. Everything weaker is silent, because a
check that cries wolf gets routed around.

KNOWN GAPS, not papered over
- A millisecond-wide check-then-write race remains: two hooks can both see absence before either
  write lands. Closing it needs an O_EXCL reservation with expiry; the real incident was minutes
  wide, so that complexity is not bought yet.
- Files created by Bash (`>`, `tee`, `cp`) bypass this entirely — `Write` is the only deterministic
  event that knows the intended path.
- Two sessions appending to the same existing file (`log.md`) is untouched: the path exists, so this
  never fires. That collision is Git's ordinary content conflict and it does surface at merge.
- Choosing different filenames for the same work defeats it completely. This is an exact-path last
  line of defence, not a solution to semantic duplication — that stays with cross-session messaging.

FAILING OPEN, EXCEPT WHERE IT MATTERS
Every internal error, timeout or unreadable state exits 0 and allows the write. This is advisory
coordination, not protection from destruction, and a hook that breaks `Write` is worse than no hook.
Only a *detected* high-confidence collision fails closed.

OPT-IN PER REPOSITORY
Silent unless the repo enables it:  git config --local agents.duplicate-write-guard true
Local config lives in the common git dir, so every linked worktree of that repo inherits it, and no
repository policy is hardcoded into a machine-wide hook.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ownership  # noqa: E402 — sibling module, same directory

BUDGET = 0.25  # hard ceiling for the whole hook, not per subprocess
STATE = Path.home() / ".agents" / "state" / "parallel-agents"
STATE_TTL = 7 * 24 * 3600
FINGERPRINT_MAX = 1 << 20  # hash contents below this; fall back to size+mtime above it


class Deadline:
    """One monotonic budget for the whole hook. Each git call gets what is left, never a fresh 5s."""

    def __init__(self, seconds: float) -> None:
        self.until = time.monotonic() + seconds

    def left(self) -> float:
        return self.until - time.monotonic()

    def expired(self) -> bool:
        return self.left() <= 0.01


def git(repo: str, dl: Deadline, *args: str) -> str | None:
    if dl.expired():
        return None
    try:
        out = subprocess.run(("git", "-C", repo, *args), capture_output=True, text=True,
                             timeout=max(0.02, dl.left()), check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def fingerprint(path: Path) -> str | None:
    """Identify the exact bytes that were offered for reading, so a later change re-arms the gate."""
    try:
        st = path.stat()
        if st.st_size < FINGERPRINT_MAX:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        return f"size:{st.st_size}:mtime:{st.st_mtime_ns}"
    except OSError:
        return None


def marker(session: str, path: Path, fp: str) -> Path:
    """State filename is a digest, never an agent-supplied path — that would be a traversal."""
    key = f"{session}\0{path}\0{fp}".encode()
    return STATE / hashlib.sha256(key).hexdigest()


def sweep() -> None:
    cutoff = time.time() - STATE_TTL
    try:
        for f in STATE.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
    except OSError:
        pass


def repo_of(path: Path, dl: Deadline) -> str | None:
    probe = path if path.exists() else path.parent
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    return git(str(probe), dl, "rev-parse", "--show-toplevel")


def attached_worktrees(repo: str, dl: Deadline) -> list[tuple[str, str]]:
    porcelain = git(repo, dl, "worktree", "list", "--porcelain")
    if not porcelain:
        return []
    out, path = [], None
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch ") and path:
            out.append((path, line[len("branch "):].removeprefix("refs/heads/")))
            path = None
        elif not line.strip() and path:
            out.append((path, "HEAD"))
            path = None
    if path:
        out.append((path, "HEAD"))
    return out


def collisions(repo: str, rel: str, dl: Deadline) -> list[dict]:
    """Sibling worktrees that hold this path as recent, newly added work. Highest signal first."""
    here = str(Path(repo).resolve())
    trees = attached_worktrees(repo, dl)
    paths = [p for p, _ in trees]
    sessions: list[dict] | None = None  # read lazily: most Writes collide with nothing
    found = []
    for wt, branch in trees:
        if dl.expired():
            break
        if str(Path(wt).resolve()) == here:
            continue
        candidate = Path(wt) / rel
        if not candidate.exists():
            continue

        tracked = git(wt, dl, "ls-files", "--error-unmatch", rel) is not None
        if not tracked:
            kind, rank = "uncommitted — it exists only in that session's working tree", 0
        else:
            # Tracked: only interesting if it is NEW on that branch. A file both of us inherited
            # from the merge base is not duplicated work, it is shared history.
            base = git(repo, dl, "merge-base", "HEAD", branch) or ""
            if base and git(repo, dl, "cat-file", "-e", f"{base}:{rel}") is not None:
                continue
            kind, rank = f"added on branch {branch}, not present at the merge base", 1

        # Only a LIVE session gates. An abandoned worktree must never block a legitimate
        # recreation, and "the directory exists" was never evidence that anyone is coming back —
        # the previous version guessed at this with the file's mtime, which is a proxy for activity,
        # not for a session. ownership.py answers it as a fact: pid alive, and its start time still
        # matching what the session recorded, so a recycled pid cannot masquerade as its predecessor.
        if sessions is None:
            sessions = ownership.live_sessions()
        owner = ownership.owner_of(wt, sessions, paths)
        if owner is None:
            continue
        try:
            age_min = int((time.time() - candidate.stat().st_mtime) // 60)
        except OSError:
            age_min = -1
        found.append({"path": candidate, "branch": branch, "kind": kind, "rank": rank,
                      "age_min": age_min, "session": owner.get("name") or "?"})
    return sorted(found, key=lambda c: (c["rank"], c["age_min"]))


def pre_tool_use(payload: dict, dl: Deadline) -> int:
    if payload.get("tool_name") != "Write":
        return 0
    raw = (payload.get("tool_input") or {}).get("file_path")
    if not raw:
        return 0
    target = Path(os.path.join(payload.get("cwd") or os.getcwd(), raw))
    try:
        target = target.resolve()
    except OSError:
        return 0
    if target.exists():
        return 0  # an edit, not a creation — Git reports that collision itself, at merge

    repo = repo_of(target, dl)
    if not repo:
        return 0
    if git(repo, dl, "config", "--get", "agents.duplicate-write-guard") != "true":
        return 0
    try:
        rel = target.relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        return 0
    if rel.startswith(".git/") or "/.claude/worktrees/" in f"/{rel}":
        return 0

    hits = collisions(repo, rel, dl)
    if not hits:
        return 0

    session = payload.get("session_id") or "?"
    top = hits[0]
    fp = fingerprint(top["path"])
    if fp and marker(session, top["path"], fp).exists():
        return 0  # already read this exact version — proceed deliberately

    where = "\n".join(
        f"  - {h['path']}\n    held by live session {h['session']} ({h['kind']};"
        f" touched {h['age_min']} min ago)" for h in hits)
    reason = (
        f"Another live session is already working on `{rel}`. Refused so the work is not done "
        f"twice:\n{where}\n\n"
        f"Read {top['path']} first. This refusal lifts as soon as you have read it — a plain retry "
        f"stays refused, because retrying is not reading.\n\n"
        f"Then decide deliberately: extend their version, or agree who owns the file. "
        f"`SendMessage` to `{top['session']}` reaches that session directly. Two sessions creating "
        f"the same file is invisible to Git until merge, and it has already cost this machine a "
        f"hand-resolved merge once."
    )
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, sys.stdout)
    return 0


def post_tool_use(payload: dict) -> int:
    """Record that a file was read, with the bytes that were read. This is what lifts a denial."""
    if payload.get("tool_name") != "Read":
        return 0
    raw = (payload.get("tool_input") or {}).get("file_path")
    session = payload.get("session_id")
    if not raw or not session:
        return 0
    try:
        path = Path(os.path.join(payload.get("cwd") or os.getcwd(), raw)).resolve()
    except OSError:
        return 0
    fp = fingerprint(path)
    if not fp:
        return 0
    STATE.mkdir(parents=True, exist_ok=True)
    sweep()
    marker(session, path, fp).write_text("", encoding="utf-8")
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    event = payload.get("hook_event_name")
    if event == "PostToolUse":
        return post_tool_use(payload)
    if event == "PreToolUse":
        return pre_tool_use(payload, Deadline(BUDGET))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — advisory hook, never break a tool call
        sys.exit(0)
