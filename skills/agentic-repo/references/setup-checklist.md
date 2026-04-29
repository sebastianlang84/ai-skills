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
- README/setup commands
- TODO/backlog conventions

Look for:

- duplicate authority sources
- stale docs contradicted by code/config
- missing setup/verification commands
- secrets or sensitive values in docs
- overgrown memory/task history files

## 3. Design the target doc set

Default root files:

- `README.md`
- `AGENTS.md`
- `MEMORY.md`
- `TODO.md`
- `CHANGELOG.md`

Optional only when justified:

- `docs/adr/*`
- `docs/runbooks/*`
- `docs/plans/*`
- `.agents/skills/*`

Decide whether `TODO.md` should use exactly one of:

- `assets/todo-roadmap-template.md` for future SemVer roadmap sections, or
- `assets/todo-priority-template.md` for `P0/P1/P2` priority buckets.

Do not keep both unless the repo truly needs both and the roles are explicit.

## 4. Implement

For each baseline file:

- add compact frontmatter
- preserve valid repo-specific content
- remove placeholders that can be filled from verified facts
- leave explicit placeholders only when facts are unknown
- avoid broad rewrites when targeted edits are enough

Recommended order:

1. `README.md` from actual project facts
2. `AGENTS.md` with routing and gates
3. `MEMORY.md` with stable current truth only
4. `TODO.md` with open work only
5. `CHANGELOG.md` with current unreleased/release history

## 5. Verify

- Re-read changed files.
- Ensure each file's frontmatter matches its content.
- Ensure no file contains information routed elsewhere.
- Ensure `AGENTS.md` bootstrap references files that exist.
- Ensure `MEMORY.md` has no rules/backlog/secrets.
- Ensure `TODO.md` has no completed history.
- Ensure `CHANGELOG.md` has only user/operator-relevant changes.
- Run repo-specific checks if setup/operation instructions changed.

## 6. Report

Summarize:

- files created/changed
- assumptions/placeholders left
- verification performed
- follow-up recommendations
