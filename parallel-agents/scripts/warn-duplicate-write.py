#!/usr/bin/env python3
"""PreToolUse hook: say so when another session already has the file you are about to create.

WHAT IT IS FOR
Three to five agents run on this machine at once, in sibling git worktrees of one repo. Worktree
isolation prevents *interference* — two agents disturbing each other's working tree — and does
nothing about *duplication*. Two sessions creating the same new file is invisible to Git, because an
add/add divergence does not exist until both sides do; it surfaces at merge, after both sides have
paid for the work. That happened on 2026-08-14 in ~/dev/brain: two sessions independently wrote
preferences/structural-search-first.md and preferences/tools-are-part-of-the-work.md.

WHY A HOOK AND NOT A RULE
The rule exists (`git worktree list` before substantial work) and a rule is not what failed. On this
same machine, instructions to prefer ast-grep and CodeMap over grep sat in AGENTS.md for months and
were routinely skipped — the gap was habit, not knowledge. A probe that must be remembered gets
forgotten; this one runs at the moment it matters and costs nothing to ignore.

WHAT IT IS NOT
Not a gate. It emits no permission decision, so the normal permission flow is untouched and no write
is ever blocked or auto-approved — it only adds context the model can act on or dismiss. That is
deliberate: a file existing elsewhere is evidence, not proof, and a check that blocks on evidence
teaches people to route around it. So it reports where the file is and how old that work is, and
lets the agent judge.

The one thing it can do that no git command can: a sibling worktree's working directory is readable
on disk, so this sees **uncommitted** files in another live session. The written rule admits it
cannot close that window.

FAILING OPEN
Any error at all exits 0 silently. A hook that breaks Write is worse than no hook, and this one is
an advisory — there is no failure mode where refusing to run should stop the operator's work.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

TIMEOUT = 5  # seconds for the whole hook; a slow probe is not worth a slow Write


def git(repo: str, *args: str) -> str | None:
    """Run a read-only git command, returning None on any failure."""
    try:
        out = subprocess.run(
            ("git", "-C", repo, *args),
            capture_output=True, text=True, timeout=TIMEOUT, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def worktrees(repo: str) -> list[tuple[str, str]]:
    """Every worktree of this repo as (path, branch). Empty when git cannot say."""
    porcelain = git(repo, "worktree", "list", "--porcelain")
    if not porcelain:
        return []
    found, path = [], None
    for line in porcelain.splitlines():
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if payload.get("tool_name") != "Write":
        return 0

    raw = (payload.get("tool_input") or {}).get("file_path")
    if not raw:
        return 0
    target = Path(os.path.join(payload.get("cwd") or os.getcwd(), raw)).resolve()

    # Only new files. An existing path is an edit, and editing a file two sessions share is a
    # different problem — one Git can and does report, at merge, as a normal content conflict.
    if target.exists():
        return 0

    repo = git(str(target.parent if target.parent.exists() else Path.cwd()),
               "rev-parse", "--show-toplevel")
    if not repo:
        return 0
    try:
        rel = target.relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        return 0
    # Never report on git internals or on a sibling's checkout seen from inside another worktree.
    if rel.startswith(".git/") or "/.claude/worktrees/" in f"/{rel}":
        return 0

    trees = worktrees(repo)
    # Scope: only a repo that actually has parallel checkouts. Without this, the history probe below
    # fires in every repo on the machine whenever anyone recreates a deleted file — a different
    # feature, un-asked-for, and a steady source of noise in exactly the tool whose credibility
    # depends on not crying wolf. Two sessions sharing ONE checkout are not missed by dropping this:
    # there the file is already in the working tree, and the `target.exists()` check above returns.
    if len(trees) < 2:
        return 0

    here = str(Path(repo).resolve())
    notes: list[str] = []

    for path, branch in trees:
        resolved = str(Path(path).resolve())
        # `git rev-parse --show-toplevel` run from inside a worktree returns THAT worktree's root,
        # so `here` is our own checkout and is the one to skip.
        if resolved == here:
            continue
        candidate = Path(path) / rel
        if candidate.exists():
            state = "committed" if git(path, "ls-files", "--error-unmatch", rel) is not None \
                    else "UNCOMMITTED — it exists only in that session's working tree"
            notes.append(f"  - {candidate} (branch {branch}, {state})")

    # One bounded call: has any ref in this repo ever carried this path?
    if not notes:
        touched = git(repo, "log", "--all", "--format=%h %cr", "--max-count=1", "--", rel)
        if touched:
            sha, _, when = touched.partition(" ")
            branches = git(repo, "branch", "-a", "--contains", sha, "--format=%(refname:short)")
            where = ", ".join(branches.split("\n")[:4]) if branches else "another ref"
            notes.append(f"  - already exists in this repo's history ({sha}, {when}) on: {where}")

    if not notes:
        return 0

    message = (
        f"Another session may already have done this work. `{rel}` does not exist in your working "
        f"tree, but it was found here:\n" + "\n".join(notes) + "\n\n"
        "This is information, not a refusal — the write proceeds. But read that version before "
        "writing a second one: two sessions creating the same file is invisible to Git until merge, "
        "and it has already cost this machine a hand-resolved merge once. If another session is "
        "live, `ListAgents` names it and `SendMessage` reaches it; agreeing who owns the file is "
        "cheaper than reconciling two versions of it."
    )
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": message,
    }}, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — advisory hook, never break a Write
        sys.exit(0)
