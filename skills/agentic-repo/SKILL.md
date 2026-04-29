---
name: agentic-repo
description: Use this skill when the user wants to make a repository agentic-coding-ready; set up, align, review, or maintain AGENTS.md, MEMORY.md, TODO.md, README.md, CHANGELOG.md; add document-role frontmatter; or migrate from ad-hoc agent docs to a compact repo-first baseline. Do not use for generic documentation writing unless repo agent governance or memory/routing files are in scope.
---

# Agentic Repo

Use this skill to set up, align, review, or maintain a repository so coding agents can work in it reliably with a small, maintainable document surface.

## Core outcome

Prefer the minimal repo-first baseline:

- `README.md` — human/operator entry point
- `AGENTS.md` — normative agent behavior, guardrails, bootstrap, routing, and gates
- `MEMORY.md` — stable current truth, durable non-normative context, and tiny recent-task handoff window
- `TODO.md` — active open work only
- `CHANGELOG.md` — curated outward-facing change history

Use compact frontmatter on maintained Markdown files:

```yaml
---
role: ...
contains: ...
not-contains: ...
write-when: ...
---
```

## When to trigger

Trigger for requests such as:

- "make this repo agent-ready"
- "create AGENTS.md / MEMORY.md / TODO.md"
- "standardize repo docs for agents"
- "bootstrap agentic coding docs"
- "add memory and routing docs"
- "turn this repo into an agentic-coding repo"
- "use templates for README, AGENTS, MEMORY, TODO, CHANGELOG"

Do not trigger for:

- ordinary prose editing with no repo governance angle
- app architecture design unrelated to agent docs
- one-off README copyediting unless baseline alignment is requested
- creating a skill itself; use `skill-creator` for that

## Required working rules

1. Inspect before writing.
2. Preserve existing project truth; do not overwrite useful repo-specific content with generic templates.
3. Keep the baseline small. Add extra docs only when they provide durable value and have a clear update trigger.
4. Treat code, config, tests, and executable checks as technical ground truth.
5. Treat git history as history; do not duplicate it into memory or changelog.
6. Never put secrets in generated docs.
7. Keep changes reviewable and scoped to the user's requested alignment.

## Default workflow

### 1. Diagnose the target repo

Read or inspect, as available:

- file tree and root docs
- existing `README.md`, `AGENTS.md`, `MEMORY.md`, `TODO.md`, `CHANGELOG.md`
- package/build/deploy files that reveal actual operation
- existing docs under `docs/`
- git status before editing

Decide whether the repo needs:

- new baseline files
- alignment of existing files
- frontmatter only
- cleanup of duplicate/obsolete agent docs
- a migration plan before edits

Stop and ask if existing docs conflict in a way that could change behavior or if deletion/rollback would be needed.

### 2. Choose the baseline shape

Default to the five root files. Add optional directories only when needed:

- `docs/adr/*` for durable decisions
- `docs/runbooks/*` for procedural how-to
- `docs/plans/*` for detailed plans rooted in active work
- `.agents/skills/*` for curated repo-local skills

Avoid default creation of:

- episodic memory folders
- duplicate ADR trees outside `docs/`
- broad policy catalogs
- session snapshot directories
- large root documentation indexes

### 3. Apply templates carefully

Templates live in `assets/`:

- `agents-template.md`
- `memory-template.md`
- `todo-template.md` — chooser explaining the two supported TODO structures
- `todo-roadmap-template.md` — SemVer release roadmap backlog
- `todo-priority-template.md` — P0/P1/P2 priority backlog
- `readme-template.md`
- `changelog-template.md`

Use them as scaffolds, not as blind overwrites.

For existing files:

- keep valid project-specific content
- add or correct frontmatter
- remove only clearly obsolete duplication when approved or obviously safe
- align section roles and update triggers
- keep `AGENTS.md` short and operative
- keep `MEMORY.md` compact; avoid diaries
- keep `TODO.md` as open work only
- keep `CHANGELOG.md` outward-facing

### 4. Populate each file by role

Use `references/document-routing.md` for details.

Minimum expectations:

- `README.md`: what the repo is, why it exists, setup, usage, verification, troubleshooting/support, license/status
- `AGENTS.md`: role/behavior, hard rules, bootstrap/read order, document roles, gates/completion rules
- `MEMORY.md`: current stable truth, long-term non-normative context, latest 3 completed tasks max
- `TODO.md`: active work only; no completed history; no checked-off archive
- `CHANGELOG.md`: Keep a Changelog categories and SemVer when the repo versions releases

### 5. Add frontmatter to maintained Markdown

Use the four fields consistently:

- `role`: what the file is for
- `contains`: what belongs here
- `not-contains`: what must not be stored here
- `write-when`: the update trigger

See `references/frontmatter.md`.

### 6. Verify

After edits:

- re-read changed files for consistency
- check that file roles do not overlap unnecessarily
- check that bootstrap/routing references match actual files
- run relevant repo checks if docs affect setup or commands
- check git status and summarize only changed files

If no durable project truth changed outside the new docs, say so; do not invent `MEMORY.md` content.

## Recommended outputs

When proposing or completing work, report:

- files created/changed
- important choices made
- any assumptions left in placeholders
- verification performed
- suggested next cleanup, if any

## Bundled references

- `assets/`: reusable document templates
- `references/setup-checklist.md`: end-to-end bootstrap checklist
- `references/document-routing.md`: where information belongs
- `references/frontmatter.md`: metadata conventions
- `references/migration-notes.md`: safe migration from larger/ad-hoc structures
- `references/review-checklist.md`: readiness checklist before considering an aligned repo complete

## Provenance and maintenance

This skill was distilled from `/home/wasti/agentic-coding`, with the global skill now treated as the canonical reusable artifact. When source materials conflict, prefer the current minimal repo-first standard captured in this skill over stale historical templates or changelog entries in the source repo.
