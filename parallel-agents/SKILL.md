---
name: parallel-agents
description: Coordinating several agent sessions working the same repo at once — detecting that another session is already on your topic, claiming work, and the PreToolUse hook that reports a file another worktree already has. Use when several sessions run in parallel, when a merge turns up duplicate work, or when deciding whether to start on something another agent may already hold.
---

# Parallel agents on one repo

Three to five sessions run on this machine at once, in sibling worktrees of the same repo. The
failure mode is not what the isolation rules address.

**Worktrees prevent interference. They do not prevent duplication.** Two sessions creating the same
new file is invisible to Git — an add/add divergence does not exist until both sides do — so it
surfaces at merge, after both sides have paid. That has happened once here, to two sessions that
were each following the isolation rules perfectly.

The argument, the incident and the list of what still has no rule live in
`~/.agents/brain/preferences/parallel-agents-git.md`.

## Before substantial work

```bash
git worktree list                              # sibling checkouts of this repo
git branch -a --sort=-committerdate | head     # who has been working, and on what
git fetch && git log --oneline -5 origin/<base>   # did the base move under you
```

`ListAgents` names the live sessions, and is the only probe that sees a session which has not
committed anything yet. When one of them is in your repo, say which files you are taking
(`SendMessage`) before writing, and answer in kind when someone tells you.

Re-check the base **before merging**, not only before starting.

## The hook

`scripts/warn-duplicate-write.py` runs as a `PreToolUse` hook on `Write` (registered in
`~/.claude/settings.json`). When the file you are about to create does not exist in your working
tree but does exist in a sibling worktree, or anywhere in the repo's history, it says so and names
where.

It reads a sibling worktree's **working directory**, so it sees uncommitted files in another live
session — the one thing no git command can do, and precisely the window the written rule admits it
cannot close.

It is advisory by construction:

- it emits **no permission decision**, so the normal permission flow is untouched and no write is
  ever blocked or auto-approved — it only adds context;
- a file existing elsewhere is evidence, not proof (the worktree may be abandoned, or the path may
  legitimately exist on the base), so it reports the facts and lets the agent judge;
- **any error exits 0 silently.** A hook that breaks `Write` is worse than no hook.

Why a hook rather than another paragraph: the rule already existed and rules were not what failed.
Instructions to prefer `ast-grep` and CodeMap over `grep` sat in `AGENTS.md` for months and were
routinely skipped. A probe that has to be remembered gets forgotten; this one runs at the moment it
matters and costs nothing to ignore.

Test it without waiting for a real collision:

```bash
echo '{"tool_name":"Write","cwd":"<repo>","tool_input":{"file_path":"<path>"}}' \
  | python3 ~/.agents/skills/parallel-agents/scripts/warn-duplicate-write.py
```

Silence means no collision found. It costs roughly 100 ms, nearly all of it Python start-up.
