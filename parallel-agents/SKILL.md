---
name: parallel-agents
description: Coordinate concurrent agents in shared repositories and the Brain. Check observed ownership, assign file scopes, isolate workers, and acquire write leases. Use before parallel edits or Brain writes, when worktree ownership is unclear, or when the Claude duplicate-write hook refuses a creation.
---

# Coordinate concurrent agents

## Check ownership before editing

Run these helpers; they provide evidence, not permission:

```bash
git worktree list
python3 ~/.agents/skills/parallel-agents/scripts/ownership.py --json
python3 ~/.agents/skills/parallel-agents/scripts/ownership.py --all --json
```

`ownership.py` observes **Claude session records only**, checked against live process IDs and
recorded start times when available. A missing owner means **unknown**, including for Codex and Pi.
It cannot establish that a worktree is free. Its JSON rows expose coverage and ownership status;
`--all` lists only observed Claude sessions.

Combine it with the current harness's agent list, worktree changes, and direct coordination.
An agent list may cover only the current team, not independent sessions or other harnesses.
Do not mutate a live owner's branch. If relevant ownership remains unresolved, isolate your work
and resolve ownership before integration. Git approval and history rules belong to `git-workflow`.

## Assign work and integrate

- Give each worker an explicit repository, absolute CWD, file scope and expected result. One writer
  owns each file; agree shared contracts before concurrent edits.
- Use an isolated worktree for overlapping scopes. Shared-directory workers must own disjoint files.
  Workers do not merge or push the base branch; the coordinator handles integration.
- Check what a spawned worker receives. If it starts from HEAD, commit authorized prerequisites
  first; a stash does not make them available. Read-only workers need no extra checkout.
- Coordinate through the current harness's messaging tools when they reach the relevant session.
  A printed session name is not proof that a messaging tool can reach it.
- Require a handoff with files, changes, checks, branch/commit if applicable, and unresolved issues.
  Recheck upstream and ownership, inspect the integrated diff, and run the affected checks.
- Remove only completed, task-owned worktrees and safely delete merged task branches.

## Lease Brain files before writing

Claim all affected concept files, indexes and `log.md` together:

```bash
python3 ~/.agents/skills/parallel-agents/scripts/brain-lock.py acquire concept.md index.md log.md
python3 ~/.agents/skills/parallel-agents/scripts/brain-lock.py status
# Before expiry, if work needs more time:
python3 ~/.agents/skills/parallel-agents/scripts/brain-lock.py renew TOKEN --ttl 900
# After edits, validation and integration:
python3 ~/.agents/skills/parallel-agents/scripts/brain-lock.py release TOKEN
```

These are cooperative leases: writers must use the helper. Default lifetime is 15 minutes,
maximum one hour per acquisition or renewal. **Expiry releases the lock even if you are still
working.** Renew before expiry and require success before continuing. If renewal fails or the
lease expires, stop writing, reacquire and inspect intervening changes before resuming. Do not
silently assume ownership survives a long tool call. A blocked acquisition means another lease
holds that path; inspect `status` and coordinate. `using-brain` owns content routing and validation.

## Claude duplicate-write hook

`warn-duplicate-write.py` is a Claude `PreToolUse/Write` and `PostToolUse/Read` adapter. It must be
registered in that harness; it does not enforce Codex/Pi writes. A repository opts in with:

```bash
git config --local agents.duplicate-write-guard true
```

The hook refuses a new file only when an observed live Claude session holds the same new path
in an attached sibling worktree. Failed Git queries provide no collision evidence. On refusal,
read the named sibling file, then coordinate or reuse the work. Reading records a content marker;
changed content requires another read. A blind retry does not clear the refusal.

Limits: existing-file edits, shell writes, simultaneous creations and differently named duplicate
work are not protected. The read marker fingerprints the file after the Read event; it cannot
prove that every byte was returned or understood. The Git probes share a 250 ms budget; this is
not a hard deadline on every filesystem operation. Treat the hook as an additional check, not a
substitute for file ownership or Brain leases.
