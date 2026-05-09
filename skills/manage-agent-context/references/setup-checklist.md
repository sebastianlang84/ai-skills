# Agentic Repo Bootstrap Checklist

Use this as the end-to-end checklist when aligning a target repo.

## 1. Preflight

- State goal, scope, and assumptions.
- Confirm whether the user wants immediate edits or a plan first.
- Check for dirty worktree and unrelated changes.
- Identify whether deletion/renaming is in scope. If not, do not delete.

## 2. Read-only diagnosis

Inspect:

- root file tree
- existing docs and templates
- build/package/deploy files
- existing agent files such as `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.roo/*`, `.agents/*`
- global/repo skills referenced by the repo, especially `git-workflow` for Git lifecycle and repo-local skills for overrides
- optional Pi extensions or scripts used for context checks, memory, code search, TODOs, or release gates
- README project description, install, usage, and license
- TODO/backlog conventions

Look for:

- duplicate authority sources
- stale docs contradicted by code/config
- missing setup/verification commands
- secrets or sensitive values in docs
- overgrown memory/task history files

## 3. Design the target context system

Default root files and state stores:

- `README.md`
- `AGENTS.md`
- agent/harness memory (Pi: pi-memory tools)
- `TODO.md`
- `CHANGELOG.md`

Optional only when justified:

- `docs/adr/*`
- `docs/runbooks/*`
- `docs/plans/*`
- `.agents/skills/*`
- repo scripts, hooks, GitHub Actions, or Pi extensions for machine-checkable context gates

Decide whether `TODO.md` should use exactly one of:

- `assets/todo-roadmap-template.md` for future SemVer roadmap sections, or
- `assets/todo-priority-template.md` for `P0/P1/P2` priority buckets.

Do not keep both unless the repo truly needs both and the roles are explicit.

## 4. Implement

For each baseline file:

- add compact frontmatter, except for `README.md` files
- preserve valid repo-specific content
- remove placeholders that can be filled from verified facts
- leave explicit placeholders only when facts are unknown
- avoid broad rewrites when targeted edits are enough

Recommended order:

1. concise `README.md` from actual project facts: project description, install, usage, and license
2. `AGENTS.md` with routing, gates, closeout order, and repo-specific overrides
3. agent/harness memory with stable current truth only (Pi: pi-memory tools)
4. `TODO.md` with open work only and clear cleanup expectations
5. `CHANGELOG.md` with current unreleased/release history and SemVer expectations
6. optional hooks/CI/scripts for enforceable gates such as changelog presence or release/version checks

## 5. Verify

- Re-read changed files.
- Ensure each non-README maintained Markdown file's frontmatter matches its content; ensure `README.md` files have no frontmatter.
- Ensure no file contains information routed elsewhere.
- Ensure `AGENTS.md` bootstrap references files that exist.
- Ensure durable memory in the agent/harness store has no rules/backlog/secrets; if a legacy `MEMORY.md` remains, ensure it is intentionally kept and gitignored unless the repo explicitly versions it.
- Ensure `TODO.md` has no completed history and explains how completed items are closed/removed if the repo needs that policy.
- Ensure `CHANGELOG.md` has only user/operator-relevant changes and its update trigger aligns with SemVer/release policy.
- Ensure closeout/push gates are not merely chat promises: binding rules are in AGENTS.md, workflows in skills, and enforceable checks in hooks/CI/tools when needed.
- Run repo-specific checks if setup/operation instructions changed.

## 6. Report

Summarize:

- files created/changed
- assumptions/placeholders left
- verification performed
- follow-up recommendations
