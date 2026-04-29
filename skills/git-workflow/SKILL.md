---
name: git-workflow
description: "Use this skill for Git workflow and task closeout: branch/worktree choice, commits, merges, pushes, rebases, sub-agent isolation, verification, handoff, and repo-policy checks."
---

# Git Workflow

Portable default for Git decisions and task closeout. Repository-local policy (`AGENTS.md`, contribution docs, maintainer instructions) always wins.

## Core rules

- Check branch and working-tree state before writing, committing, merging, rebasing, or pushing.
- Do not mix unrelated changes in one commit or handoff.
- Stop and ask when the current branch, target branch, ownership, or merge/push policy is unclear.
- Prefer small, verified, reviewable checkpoints over large unverified batches.

## Branch vs current branch

Stay on the current branch when all are true:
- the task is small and self-contained
- no parallel work needs independent history
- the change is low-risk and easy to review
- repo policy allows direct work there

Create or switch to a branch when any apply:
- work is risky, experimental, or rollback-prone
- work must survive across sessions before integration
- parallel tasks, collaborators, or sub-agents need isolation
- repo policy forbids direct work on the current branch

Follow repo naming rules. If none exist, use `<type>/<scope>/<topic>`.

## Worktree choice

Use the current worktree when it is clean enough and only one write task is active.

Create a separate worktree when:
- the current worktree has unrelated dirty changes
- multiple write tasks or agents run in parallel
- merge/rebase/conflict work needs isolation
- you need clean reviewable output from a sub-agent

Rule of thumb: branch separates history; worktree separates active workspace.

## Commits

Commit when a coherent slice is complete, testable, and worth preserving.

Before committing:
- inspect `git status`
- ensure only intended files are included
- run the smallest relevant verification
- use the repo's commit style if defined

Avoid commits for random snapshots, mixed unrelated changes, or known-broken states unless explicitly requested.

## Sync, rebase, merge, push

Rebase only when policy allows it and it will not surprise other users of the branch.

Merge only when:
- the source work is complete enough to integrate
- relevant verification passed or skipped verification is explicitly stated
- the target branch and merge strategy are clear

Push according to repo policy:
- push primary branches only after required verification
- push working branches when backup, review, or handoff matters
- never push from a side context if ownership or target is unclear

## Sub-agent isolation

Read-only sub-agents usually do not need Git isolation.

For write-capable sub-agents, decide before dispatch:
- allowed files and scope
- branch/worktree ownership
- how their output will be reviewed and integrated

Use a separate worktree when scopes overlap, multiple writers run in parallel, or clean review boundaries matter.

## Task closeout

Before declaring a coding or documentation task complete:

1. Re-check branch and `git status`.
2. Update continuity docs when affected (`MEMORY.md`, `TODO.md`, `CHANGELOG.md`, ADRs, plans, runbooks).
3. Run the smallest relevant tests/checks and state what passed or was not run.
4. Commit if the task changed files and repo policy expects commits.
5. Merge or push only when policy, target, and verification are clear.

Final handoff should state: changed files, verification, commit/merge/push status, and remaining risks or next steps.
