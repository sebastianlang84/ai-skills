# Workflow: Initialize

Run this workflow once to bootstrap agent-governance in a repo from scratch or from an ad-hoc state. Load `references/setup-checklist.md` and tick off each item as you go.

## Step 1 — Preflight

- State goal, scope, and assumptions explicitly.
- Confirm whether the user wants immediate edits or a plan first.
- Check git status and note dirty worktree or unrelated changes.
- Confirm deletion and rename scope. If not explicitly approved, do not delete anything.

## Step 2 — Diagnose

Read only what is needed:

- root file tree
- existing `README.md`, `AGENTS.md`, `TODO.md`, `CHANGELOG.md` if present
- memory system if present, e.g. `MEMORY.md`, SQLite/vector extension, or other declared memory layer
- build, package, deploy, and CI files that reveal actual operation
- `.agents/`, `.cursor/`, `.roo/`, `.claude/`, or similar agent-runtime folders when present
- `docs/` contents when present

Identify:

- which baseline files are missing vs. exist but need alignment
- duplicate authority sources
- stale docs contradicted by code or config
- secrets or sensitive values in docs

Stop and ask if conflicts require deletion, rename, ownership change, or behavioral change.

## Step 3 — Choose the baseline shape

Default: root `README.md`, `AGENTS.md`, `TODO.md`, `CHANGELOG.md`, plus whichever memory system is present or intentionally chosen.

Add optional directories only when clearly needed:

- `docs/adr/*` — durable architectural decisions
- `docs/runbooks/*` — repeatable operational procedures
- `docs/plans/*` — detailed plans tied to active work
- `.agents/skills/*` — repo-local skills

Do not create by default: episodic memory folders, session snapshots, policy catalogs, large doc indexes, or runtime adapter files no tool reads.

For `TODO.md`, use `assets/todo-template.md` unless the repo already has an issue tracker convention.

## Step 4 — Implement

Recommended order:

1. `README.md` — actual project facts; use `assets/readme-template.md` as scaffold.
2. `AGENTS.md` — routing, hard rules, bootstrap order; use `assets/agents-template.md`.
3. Memory layer — stable current truth only; use `assets/memory-template.md` when scaffolding file-based memory.
4. `TODO.md` — open work only.
5. `CHANGELOG.md` — user/operator-visible history.

For each file:

- preserve valid project-specific content
- fill placeholders from verified facts
- leave explicit `TODO:` markers only where facts are unknown
- prefer targeted edits over broad rewrites

File content rules:

- `AGENTS.md` — short, normative, operational; no setup instructions hidden here alone.
- Memory — present-tense stable facts; no rules, backlog, diary, or secrets.
- `TODO.md` — active open work only; no completed-work archive.
- `CHANGELOG.md` — Keep a Changelog categories; SemVer when the repo versions releases.

## Step 5 — Verify

- Re-read changed files for consistency.
- Check that file roles do not overlap; load `references/document-routing.md` if unclear.
- Check that `AGENTS.md` bootstrap references point to files that exist.
- Check that memory contains no rules, backlog, or secrets.
- Check that `TODO.md` contains no completed history.
- Run repo-specific checks if setup or operation instructions changed.
- Check git status and summarize only changed files.
- Confirm no secrets were introduced.

## Step 6 — Report

Summarize:

- files created or changed
- important choices made and why
- assumptions or `TODO:` placeholders left
- verification performed
- recommended follow-up
