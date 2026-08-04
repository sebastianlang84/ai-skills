#!/usr/bin/env python3
"""PreToolUse hook: block irreversible git commands, allow their safe variants.

Reads a Claude Code hook payload on stdin. Exit 2 blocks the tool call and
sends the stderr message back to the model; exit 0 allows it.

Principle: block the force variant, allow the guarded one. Anything that only
becomes dangerous once pushed (rebase, commit --amend) stays allowed, because
force-push itself is blocked.
"""
import json
import re
import sys

# (pattern, what it destroys, what to do instead)
RULES = [
    (r"\bgit\b[^;&|]*\bpush\b(?=[^;&|]*(?:\s--force\b|\s-f\b))(?![^;&|]*--force-with-lease)",
     "force-push overwrites remote history that others may already have",
     "use --force-with-lease, which refuses if the remote moved"),
    (r"\bgit\b[^;&|]*\bpush\b[^;&|]*\s\+[A-Za-z0-9_./-]*:",
     "a leading + in a refspec is a force-push in disguise",
     "use --force-with-lease, which refuses if the remote moved"),
    (r"\bgit\b[^;&|]*\bpush\b[^;&|]*(?:\s--delete\b|\s:[A-Za-z0-9_./-]+)",
     "deleting a remote branch or tag",
     "ask the operator to delete it, or confirm the ref is already merged"),
    (r"\bgit\b[^;&|]*\breset\b[^;&|]*\s--hard\b",
     "reset --hard discards every uncommitted change in the working tree",
     "use git stash, or git reset without --hard to keep the changes"),
    (r"\bgit\b[^;&|]*\bclean\b[^;&|]*\s-[A-Za-z]*f",
     "git clean -f permanently deletes untracked files, including ones never staged",
     "run git clean -n first and show the operator what would be deleted"),
    (r"\bgit\b[^;&|]*\b(?:checkout|restore)\b[^;&|]*\s(?:--\s+)?\.(?:\s|$)",
     "discarding all working-tree changes at once",
     "restore specific paths instead, so unrelated edits survive"),
    (r"\bgit\b[^;&|]*\bstash\b[^;&|]*\s(?:drop|clear)\b",
     "dropping stashed work, which is not recoverable",
     "use git stash list and git stash pop to inspect it first"),
    (r"\bgit\b[^;&|]*\bbranch\b[^;&|]*\s-[A-Za-z]*D\b",
     "branch -D deletes a branch even when it holds unmerged commits",
     "use git branch -d, which refuses to delete unmerged work"),
    (r"\bgit\b[^;&|]*\b(?:filter-branch|filter-repo)\b",
     "rewriting the entire history of the repository",
     "do this by hand, outside the agent, with a backup"),
]

COMPILED = [(re.compile(p), why, alt) for p, why, alt in RULES]

# Commit/tag messages quote arbitrary prose, so "git commit -m 'undo reset --hard'"
# must not read as a reset. Blank the message argument before matching.
MESSAGE_ARG = re.compile(r"""(-m|--message)(=|\s+)('[^']*'|"[^"]*"|\S+)""")


def check(command: str):
    command = MESSAGE_ARG.sub(r"\1\2MSG", command)
    for pattern, why, alt in COMPILED:
        if pattern.search(command):
            return why, alt
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never break the session on a malformed payload
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command:
        return 0
    hit = check(command)
    if not hit:
        return 0
    why, alt = hit
    print(
        f"BLOCKED by block-dangerous-git: {why}.\n"
        f"You do not have authority to run this. Instead: {alt}.\n"
        f"If the operator truly wants it, they run it themselves.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
