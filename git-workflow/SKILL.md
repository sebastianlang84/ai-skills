---
name: git-workflow
description: Use for Git safety, branch/worktree choice, commits, version/changelog impact, merge/push approval, and task closeout.
---

# Git Workflow

Portable default for Git decisions and task closeout. Follow repository-local policy first; use this skill for safe execution when policy is absent or incomplete.

## Core safety rules

- Check branch and working-tree state before writing, committing, merging, rebasing, or pushing.
- Without explicit user approval, run only read-only Git commands such as `git status`, `git diff`, `git log`, branch listing, and remote inspection.
- Never run mutating Git commands without explicit approval: commit, push, merge, rebase, checkout/switch, branch/tag creation or deletion, reset, restore, stash, pull, or similar state-changing operations.
- Treat `git pull` as mutating and approval-gated.
- Stop and ask when the current branch, target branch, ownership, or merge/push policy is unclear.
- Do not mix unrelated changes in one commit, branch, push, or handoff.
- Prefer small, verified, reviewable checkpoints over large unverified batches.
- When work changes files, proactively propose the next Git operation instead of only saying nothing was committed or pushed.

## Repository policy

Each repo should declare its Git method in `AGENTS.md` or contribution policy. If no method is declared, infer conservatively from branches, tags, CI/release docs, and package layout; stop and ask before creating integration branches, rebasing shared branches, or pushing.

Policy should define: primary branch, integration branch if any, allowed branch types, merge/rebase style, canonical version source(s), changelog/release-notes location, tag convention, and required verification before push.

Common models:

- **Trunk-based**: short-lived feature/fix branches merge to the primary branch after verification; releases usually come from trunk or tags.
- **GitFlow**: use declared `develop`, `release/*`, and `hotfix/*` rules; never invent missing GitFlow branches.
- **Monorepo scoped**: scope branch, checks, version, changelog, and tags to affected packages/services unless releases are lockstep.
- **Protected-primary direct flow**: direct work on the primary branch only when policy allows it, the change is small, verified, and explicitly approved.

## Branch and worktree choice

Stay on the current branch when all are true:
- task is small and self-contained
- no parallel work needs independent history
- change is low-risk and easy to review
- repo policy allows direct work there

Create or switch to a branch when any apply:
- work is risky, experimental, or rollback-prone
- work must survive across sessions before integration
- parallel tasks, collaborators, or sub-agents need isolation
- repo policy forbids direct work on the current branch

Use the current worktree when it is clean enough and only one write task is active.

Create a separate worktree when:
- the current worktree has unrelated dirty changes
- multiple write tasks or agents run in parallel
- merge/rebase/conflict work needs isolation
- clean review boundaries matter

Follow repo naming rules. If none exist, use `<type>/<scope>/<topic>`. Rule of thumb: branch separates history; worktree separates active workspace.

## Release impact checklist

Use Semantic Versioning 2.0.0 unless repository policy explicitly overrides it.

For each commit, merge, or push decision, state one impact:
- `patch`: backward-compatible bug fix, docs/operator fix tied to existing behavior, or small hardening change
- `minor`: backward-compatible feature or meaningful new operator/user capability
- `major`: breaking API/config/data/operational behavior, migration, or removed compatibility
- `no bump`: internal, unreleased, or non-user-facing change when repo policy allows it

When the impact is `patch`, `minor`, or `major`, explicitly propose the concrete next version bump from the current version before pushing or closing out, unless the user has already deferred releasing. Do not leave release-relevant work only under `Unreleased` without calling out the missing bump/tag step.

When release-relevant:
- update canonical version source(s) for the affected package/service
- update `CHANGELOG.md`, scoped changelog, or equivalent release notes
- use the repo's tag convention; in monorepos prefer scoped tags like `<service>-vX.Y.Z` when unscoped tags are ambiguous
- treat a committed version bump plus fixed changelog section as a release state; the matching annotated tag is required unless the user explicitly says tagging is deferred or this repo does not tag releases
- create annotated release tags only after tag approval; a user request to release/bump and push a specific version may count as approval only after you state the exact tag name and push target before executing
- never push tags when the tag name, remote, or approval is ambiguous

This checklist is a gate: do not commit, merge, push, tag, or declare completion for release-relevant changes until the version bump/release-note update and tag decision are resolved, or a clear `no bump`/deferred-release/deferred-tag rationale is stated. If the version/changelog/tag policy is unknown, stop and ask or inspect repo policy before mutating history.

If no version or changelog update is needed, state why.

## Commit, merge, rebase, push

Commit only when a coherent slice is complete, testable, and worth preserving. Before committing, inspect `git status`, ensure only intended files are included, run the smallest relevant verification, follow the repo's commit style, and apply the release impact checklist including changelog/version decision.

Avoid commits for random snapshots, mixed unrelated changes, or known-broken states unless explicitly requested.

Rebase only when policy allows it and it will not surprise other users of the branch.

Merge only after explicit user approval and only when source, target, strategy, verification, release impact, and changelog/version decision are clear.

Push only after explicit user approval and according to repo policy. Before pushing, state: target remote/branch/tags, verification result, release impact, changelog/version/tag decision, and whether push approval has been given. If version metadata was bumped, do not push only the branch while silently omitting the matching release tag; either include the exact tag in the push plan or explicitly mark tag creation/push as deferred. Never push from a side context if ownership or target is unclear.

## Sub-agent isolation

Read-only sub-agents usually need no Git isolation. For write-capable or parallel agents, define allowed files, branch/worktree ownership, and review/integration path before dispatch. Use a separate worktree when scopes overlap or clean review boundaries matter.

## Task closeout

Before declaring a coding or documentation task complete:

1. Re-check branch and `git status`.
2. Protect unrelated changes; stop if ownership, branch, or target is unsafe.
3. Update repo task-tracking or planning artifacts only when their file roles require it. Do not create or update repo-local memory files unless explicitly required by repo policy/user instruction.
4. Run the smallest relevant tests/checks and state what passed or was not run.
5. Apply the release impact checklist: patch / minor / major / no bump, changelog/release notes, version metadata, and tags.
6. If changes remain uncommitted, propose a commit message, included files, SemVer impact, and changelog/version/tag decision; for patch/minor/major, include the concrete next version number and expected tag name.
7. If commits are local and ready, propose the exact push target, whether a version bump commit should happen first, and the exact tag push or deferred-tag rationale.
8. Merge, push, tag, branch-switch, or other mutating Git operations only when policy, target, verification, and explicit user approval are clear.

Final handoff should state: changed files, verification, version impact/tag, commit/merge/push status, and remaining risks or next steps.
