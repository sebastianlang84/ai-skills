#!/usr/bin/env python3
"""PreToolUse hook: block irreversible git commands, allow their safe variants.

Reads a Claude Code hook payload on stdin. Exit 2 blocks the tool call and
sends the stderr message back to the model; exit 0 allows it.

Principle: block the force variant, allow the guarded one. Anything that only
becomes dangerous once pushed (rebase, commit --amend) stays allowed, because
force-push itself is blocked.

One rule earns an exception because it can be *proved* harmless rather than
judged: deleting a remote branch whose every commit is already contained in the
remote's default branch destroys nothing — the commits live on in the base, and
the ref is recreatable from it. See `deletion_is_provably_merged`, which proves
that against the live remote and fails closed on anything it cannot verify.
"""
import json
import os
import re
import shlex
import subprocess
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
     "ask the operator to delete it, or delete only branches already contained "
     "in the remote's default branch (that case is allowed automatically, but "
     "every named ref must qualify and the remote-tracking refs must be current "
     "— run git fetch --prune first)"),
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
DELETE_RULE = 2  # index into RULES — the one rule that can be proved safe

# Commit/tag messages quote arbitrary prose, so "git commit -m 'undo reset --hard'"
# must not read as a reset. Blank the message argument before matching.
MESSAGE_ARG = re.compile(r"""(-m|--message)(=|\s+)('[^']*'|"[^"]*"|\S+)""")

# Anything that can compose, redirect or expand defeats single-command parsing, so the
# deletion exception is never attempted on such a line — it stays blocked.
SHELL_META = set(";&|<>`$()\n\\\"'")
# Push options that cannot widen what gets deleted. Everything else (--mirror, --all,
# --tags, --force…) voids the exception.
INERT_PUSH_OPTS = {"-q", "--quiet", "--porcelain", "--dry-run", "-n", "--no-verify",
                   "--verbose", "-v", "--progress", "--no-progress", "--atomic"}
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


def _git(repo, *args, timeout=15):
    """Run git in `repo`; return stdout on success, None on any failure."""
    try:
        p = subprocess.run(("git", "-C", repo) + args, capture_output=True,
                           text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def _parse_push_delete(command: str):
    """(repo_rel_dirs, remote, [refs]) for a plain `git push` deletion, else None."""
    if any(ch in command for ch in SHELL_META):
        return None
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens or os.path.basename(tokens[0]) != "git":
        return None

    dirs, i = [], 1
    while i < len(tokens) and tokens[i] != "push":
        t = tokens[i]
        if t == "-C" and i + 1 < len(tokens):
            dirs.append(tokens[i + 1]); i += 2
        elif t.startswith("-C") and len(t) > 2:
            dirs.append(t[2:]); i += 1
        elif t == "-c" and i + 1 < len(tokens):
            i += 2                       # -c key=value: config, not a ref selector
        else:
            return None                  # unrecognised global option — no exception
    if i >= len(tokens):
        return None
    i += 1                               # step past "push"

    explicit_delete, positional = False, []
    for t in tokens[i:]:
        if t in ("--delete", "-d"):
            explicit_delete = True
        elif t in INERT_PUSH_OPTS:
            continue
        elif t.startswith("-"):
            return None
        else:
            positional.append(t)
    if not positional:
        return None

    remote, rest = positional[0], positional[1:]
    if not SAFE_REF.match(remote) or "/" in remote or ":" in remote:
        return None                      # a URL remote has no remote-tracking refs to check
    if explicit_delete:
        refs = rest
    else:                                # `git push origin :branch` refspec form
        if not rest or not all(r.startswith(":") for r in rest):
            return None
        refs = [r[1:] for r in rest]

    cleaned = []
    for ref in refs:
        if ref.startswith("refs/tags/") or ref.startswith("refs/remotes/"):
            return None                  # a tag is not a branch; never auto-allowed
        cleaned.append(ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref)
    if not cleaned or not all(SAFE_REF.match(r) for r in cleaned):
        return None
    return dirs, remote, cleaned


def deletion_is_provably_merged(command: str, cwd: str) -> bool:
    """True only if every named branch is demonstrably contained in the remote's default branch.

    Deliberately strict — every unknown answers "no":
      * the sha is read from the LIVE remote (`ls-remote`), not from a possibly stale
        remote-tracking ref, so a branch someone pushed to since the last fetch cannot be
        deleted on the strength of an old view;
      * containment is `merge-base --is-ancestor` against the remote's default branch. A
        squash merge is NOT an ancestor and so stays blocked, even though the change landed;
      * the default branch itself, tags, wildcard remotes and unparsable command lines are
        never eligible.
    """
    parsed = _parse_push_delete(command)
    if not parsed:
        return False
    dirs, remote, refs = parsed

    repo = cwd or os.getcwd()
    for d in dirs:                       # -C is cumulative and may be relative
        d = os.path.expanduser(d)        # the shell resolves ~ before git sees it
        repo = d if os.path.isabs(d) else os.path.join(repo, d)
    if not os.path.isdir(repo):
        return False

    base = _git(repo, "symbolic-ref", "-q", "--short", f"refs/remotes/{remote}/HEAD")
    if not base:
        for cand in (f"{remote}/main", f"{remote}/master"):
            if _git(repo, "rev-parse", "-q", "--verify", cand):
                base = cand
                break
    if not base:
        return False
    base_branch = base.split("/", 1)[1] if "/" in base else base

    for ref in refs:
        if ref == base_branch:
            return False                 # never the default branch itself
        out = _git(repo, "ls-remote", "--heads", remote, f"refs/heads/{ref}")
        if not out:
            return False                 # gone, ambiguous, or the probe failed
        lines = [l for l in out.splitlines() if l.strip()]
        if len(lines) != 1:
            return False
        sha = lines[0].split()[0]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            return False
        if _git(repo, "cat-file", "-e", f"{sha}^{{commit}}") is None:
            return False                 # not fetched locally — cannot prove anything
        if _git(repo, "merge-base", "--is-ancestor", sha, base) is None:
            return False
    return True


def check(command: str, cwd: str = ""):
    command = MESSAGE_ARG.sub(r"\1\2MSG", command)
    for idx, (pattern, why, alt) in enumerate(COMPILED):
        if not pattern.search(command):
            continue
        if idx == DELETE_RULE and deletion_is_provably_merged(command, cwd):
            continue                     # proved harmless; other rules still apply
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
    hit = check(command, payload.get("cwd") or "")
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
