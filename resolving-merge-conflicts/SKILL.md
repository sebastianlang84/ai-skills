---
name: resolving-merge-conflicts
description: Resolve an in-progress git merge or rebase conflict hunk by hunk, by tracing each side's original intent. Use when a merge, rebase, or cherry-pick has stopped with conflicts.
---

# Resolving Merge Conflicts

Resolve by **intent**, not by picking whichever side looks tidier. Follow `git-workflow` for approval gates: resolving conflicts in the working tree is repair work, but finishing the operation (commit, `--continue`, `--abort`) is a mutating Git action and needs explicit user approval.

## Process

1. **See the current state.** Which operation is in progress (`git status`), which commits are involved, which files conflict. Report this before touching anything.

2. **Find the primary source for each side.** Understand *why* each change was made and what the original intent was: commit messages, PR description, linked issue, surrounding history (`git log -p` on each side of the hunk). A conflict resolved without knowing both intents is a guess.

3. **Resolve each hunk.** Preserve both intents where possible. Where they are genuinely incompatible, pick the one matching the stated goal of the merge and record the trade-off in your report. Do **not** invent new behaviour while resolving — a conflict resolution is not the place for a refactor.

4. **Run the project's automated checks.** Discover them first (test/typecheck/lint/format scripts, CI config), then run them. Fix what the merge broke — and only that.

5. **Report, then ask.** State: files resolved, which intent won in each incompatible hunk and why, check results, and anything you could not resolve confidently. Then propose the exact finishing command (`git merge --continue`, `git rebase --continue`, or the commit) and wait for approval.

**Never `--abort` on your own initiative.** Aborting throws away the resolution work and is the user's call. If the conflict cannot be resolved responsibly, say so and hand back the analysis.
