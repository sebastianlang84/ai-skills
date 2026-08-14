#!/usr/bin/env python3
"""Who holds which worktree and branch right now — derived, never stored.

WHY THERE IS NO REGISTRY FILE
`git-workflow` makes unclear ownership a stop condition three times and tells you to "define
branch/worktree ownership before dispatch", but there was nothing to consult. The obvious fix is a
registry agents write to when they start work. That is the wrong shape: a registry has to be
written, refreshed, and cleaned up, and every one of those steps is a way for it to lie. A stale
claim is worse than no claim, because it blocks work with the authority of a fact.

Everything needed is already on disk and maintained by something other than us:

    git worktree list          worktree -> branch, maintained by git
    ~/.claude/sessions/*.json  pid -> {sessionId, cwd, name, socket}, written by the harness
    kill(pid, 0)               liveness, maintained by the kernel

Joining those three answers the question with no state of our own. Nothing to garbage-collect,
nothing to go stale, and it is correct the instant a session dies rather than after a timeout.

PID REUSE IS CHECKED, NOT ASSUMED AWAY
A recycled pid would report a dead session as live, and this is the one place where being wrong
means blocking real work. The session file records `procStart`, which is field 22 of
/proc/<pid>/stat — the process start time in clock ticks since boot. If the running process does not
carry the same value, the pid was reused and the session is dead. Verified against a live session
before this was relied on.

Used as a library by the duplicate-write hook (liveness beats the mtime guess it used before), and
runnable on its own:

    ownership.py [PATH] [--json] [--all]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SESSIONS = Path.home() / ".claude" / "sessions"


def _proc_start(pid: int) -> str | None:
    """Field 22 of /proc/<pid>/stat. The comm field can contain spaces and parentheses, so the
    split has to happen after the LAST ')' — splitting on whitespace alone misreads any process
    whose name contains a space."""
    try:
        after = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return None
    return after[19] if len(after) > 19 else None


def live_sessions() -> list[dict]:
    """Every Claude session alive right now, newest first. Never raises."""
    out: list[dict] = []
    try:
        files = sorted(SESSIONS.glob("*.json"))
    except OSError:
        return out
    for path in files:
        try:
            info = json.loads(path.read_text(encoding="utf-8"))
            pid = int(info.get("pid") or path.stem)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        try:
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError, OSError):
            continue
        recorded = info.get("procStart")
        if recorded and _proc_start(pid) != str(recorded):
            continue  # pid reused since the session registered — that session is gone
        info["pid"] = pid
        out.append(info)
    out.sort(key=lambda i: i.get("startedAt", 0), reverse=True)
    return out


def worktrees(repo: str, timeout: float = 2.0) -> list[tuple[str, str]]:
    """(path, branch) for every worktree attached to this repo. Empty when git cannot say."""
    try:
        res = subprocess.run(("git", "-C", repo, "worktree", "list", "--porcelain"),
                             capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    if res.returncode != 0:
        return []
    found, path = [], None
    for line in res.stdout.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch ") and path:
            found.append((path, line[len("branch "):].removeprefix("refs/heads/")))
            path = None
        elif not line.strip() and path:
            found.append((path, "(detached)"))
            path = None
    if path:
        found.append((path, "(detached)"))
    return found


def owner_of(worktree: str, sessions: list[dict] | None = None,
             worktree_paths: list[str] | None = None) -> dict | None:
    """The live session working in this worktree, or None.

    `worktree_paths` — every worktree of the repo — is not optional in practice, and leaving it out
    is a real bug rather than a lost optimisation. Worktrees NEST: the harness puts them under
    `<repo>/.claude/worktrees/*`, so a session sitting in one has a cwd that is also beneath the
    main checkout. Prefix matching alone therefore credits the main checkout with every worktree's
    session, and a caller asking "is anyone live in the main checkout?" gets a confident yes when
    nobody is there. A session belongs to the DEEPEST worktree containing its cwd, and to no other.
    (Found by a test: a file present only in the main checkout was reported as held by the session
    working two directories below it.)"""
    sessions = live_sessions() if sessions is None else sessions
    try:
        target = Path(worktree).resolve()
    except OSError:
        return None
    for s in sessions:
        cwd = s.get("cwd")
        if not cwd or not _contains(str(target), cwd):
            continue
        if worktree_paths:
            deepest = max((p for p in worktree_paths if _contains(p, cwd)),
                          key=lambda p: len(str(Path(p).resolve())), default=None)
            if deepest and Path(deepest).resolve() != target:
                continue
        return s
    return None


def survey(repo: str) -> list[dict]:
    """Every worktree of this repo with its branch and its live owner, if any."""
    sessions = live_sessions()
    trees = worktrees(repo)
    paths = [p for p, _ in trees]
    return [{"worktree": p, "branch": b, "owner": owner_of(p, sessions, paths)} for p, b in trees]


def _contains(parent: str, child: str) -> bool:
    if not child:
        return False
    try:
        p, c = Path(parent).resolve(), Path(child).resolve()
    except OSError:
        return False
    return p == c or p in c.parents


def _age(session: dict) -> str:
    started = session.get("startedAt")
    if not started:
        return ""
    mins = int((time.time() - started / 1000) // 60)
    return f"{mins} min" if mins < 120 else f"{mins // 60} h"


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    show_all = "--all" in argv
    rest = [a for a in argv if not a.startswith("--")]
    start = rest[0] if rest else os.getcwd()

    if show_all:
        rows = [{"session": s.get("name"), "cwd": s.get("cwd"), "id": s.get("sessionId"),
                 "pid": s.get("pid"), "started": _age(s)} for s in live_sessions()]
        print(json.dumps(rows, indent=2) if as_json else
              "\n".join(f"{r['session']:<32} {r['started']:>6} ago  {r['cwd']}" for r in rows))
        return 0

    try:
        repo = subprocess.run(("git", "-C", start, "rev-parse", "--show-toplevel"),
                              capture_output=True, text=True, timeout=2, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        repo = ""
    if not repo:
        print(f"not a git repository: {start}", file=sys.stderr)
        return 2

    rows = survey(repo)
    if as_json:
        print(json.dumps(rows, indent=2))
        return 0
    for r in rows:
        owner = r["owner"]
        who = f"{owner['name']} (live, started {_age(owner)} ago)" if owner else "no live session"
        print(f"{r['branch']:<34} {who:<44} {r['worktree']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
