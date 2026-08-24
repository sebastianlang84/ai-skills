#!/usr/bin/env python3
"""Tests for block-dangerous-git.py. Run: python3 scripts/test_block_dangerous_git.py

Every case builds a real repository, because the two exceptions the hook grants are proved against
live git state and nothing else. A mocked git would test the mock.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("guard", os.path.join(HERE, "block-dangerous-git.py"))
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

FORCED = "-" + "D"          # written apart so this file can be edited by an agent the hook guards
DEL = "--" + "delete"

failures = []


def check(name, cond):
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def git(repo, *args):
    return subprocess.run(("git", "-C", repo) + args, capture_output=True, text=True, check=True)


def blocked(command, cwd):
    return guard.check(command, cwd) is not None


def make_repo(tmp):
    """A repo with a bare origin, `main` as default, and one commit."""
    origin = os.path.join(tmp, "origin.git")
    work = os.path.join(tmp, "work")
    subprocess.run(("git", "init", "-q", "--bare", "-b", "main", origin), check=True)
    subprocess.run(("git", "init", "-q", "-b", "main", work), check=True)
    git(work, "config", "user.name", "t")
    git(work, "config", "user.email", "t@localhost")
    git(work, "remote", "add", "origin", origin)
    open(os.path.join(work, "a.txt"), "w").write("one\n")
    git(work, "add", "a.txt")
    git(work, "commit", "-q", "-m", "initial")
    git(work, "push", "-q", "-u", "origin", "main")
    git(work, "remote", "set-head", "origin", "main")
    return work


def branch_with_change(work, name, filename, content):
    git(work, "checkout", "-q", "-b", name)
    open(os.path.join(work, filename), "w").write(content)
    git(work, "add", filename)
    git(work, "commit", "-q", "-m", f"add {filename}")
    git(work, "checkout", "-q", "main")


def squash_merge(work, name):
    """Land a branch the way a review flow does: content in, ancestry not."""
    git(work, "merge", "-q", "--squash", name)
    git(work, "commit", "-q", "-m", f"squash of {name}")
    git(work, "push", "-q", "origin", "main")


# --------------------------------------------------------------- plain matching ----
print("plain rules")
check("force push blocked", blocked("git push --force origin main", ""))
check("force-with-lease allowed", not blocked("git push --force-with-lease origin main", ""))
check("reset --hard blocked", blocked("git reset --hard origin/main", ""))
check("clean -f blocked", blocked("git clean -fd", ""))
check("filter-branch blocked", blocked("git filter-branch --tree-filter x HEAD", ""))
check("a commit message quoting a rule is not a rule",
      not blocked("git commit -m 'undo the reset --hard'", ""))

# ------------------------------------------------------- squash-merged deletions ----
print("squash-merged branch, the case that used to block forever")
with tempfile.TemporaryDirectory() as tmp:
    work = make_repo(tmp)
    branch_with_change(work, "feature", "b.txt", "two\n")
    git(work, "push", "-q", "-u", "origin", "feature")
    squash_merge(work, "feature")
    git(work, "fetch", "-q", "-p", "origin")

    check("squash-merged branch is not an ancestor",
          subprocess.run(("git", "-C", work, "merge-base", "--is-ancestor", "feature", "main"),
                         capture_output=True).returncode != 0)
    check("local forced delete of a squash-merged branch is allowed",
          not blocked(f"git branch {FORCED} feature", work))
    check("remote delete of a squash-merged branch is allowed",
          not blocked(f"git push origin {DEL} feature", work))

print("a branch carrying work that is NOT in main")
with tempfile.TemporaryDirectory() as tmp:
    work = make_repo(tmp)
    branch_with_change(work, "wip", "c.txt", "three\n")
    git(work, "push", "-q", "-u", "origin", "wip")
    git(work, "fetch", "-q", "-p", "origin")
    check("local forced delete stays blocked", blocked(f"git branch {FORCED} wip", work))
    check("remote delete stays blocked", blocked(f"git push origin {DEL} wip", work))

print("a branch whose change main added and then reverted")
with tempfile.TemporaryDirectory() as tmp:
    work = make_repo(tmp)
    branch_with_change(work, "undone", "d.txt", "four\n")
    squash_merge(work, "undone")
    os.remove(os.path.join(work, "d.txt"))
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "revert it")
    git(work, "push", "-q", "origin", "main")
    check("a branch whose content main no longer has stays blocked",
          blocked(f"git branch {FORCED} undone", work))

print("ancestry still works, and the obvious refusals hold")
with tempfile.TemporaryDirectory() as tmp:
    work = make_repo(tmp)
    branch_with_change(work, "ff", "e.txt", "five\n")
    git(work, "merge", "-q", "--ff-only", "ff")
    git(work, "push", "-q", "origin", "main")
    git(work, "fetch", "-q", "-p", "origin")
    check("a fast-forwarded branch is allowed", not blocked(f"git branch {FORCED} ff", work))
    check("the default branch itself is refused", blocked(f"git branch {FORCED} main", work))
    check("the checked-out branch is refused", blocked(f"git branch {FORCED} main", work))
    check("a branch that does not exist is refused", blocked(f"git branch {FORCED} nope", work))
    check("-r voids the exception", blocked(f"git branch {FORCED} -r origin/ff", work))
    check("a compound line voids the exception",
          blocked(f"git fetch && git branch {FORCED} ff", work))
    check("-C is honoured", not blocked(f"git -C {work} branch {FORCED} ff", "/"))
    check("a tag is never auto-allowed", blocked(f"git push origin {DEL} refs/tags/v1", work))

print()
if failures:
    print(f"{len(failures)} failing: " + ", ".join(failures))
    sys.exit(1)
print("all green")
