---
name: manage-agent-context
description: "Use this skill to initialize, align, review, or audit repository context systems: baseline docs/templates, agent instructions, document routing, skills, optional Pi extensions, TODO/CHANGELOG roles, and memory ownership. Do not use for generic documentation writing or Git operation rules; use git-workflow for branching, commits, merges, pushes, tags, and release flow."
---

# Manage Agent Context

Use this skill to initialize, align, review, or audit a repository so coding agents can work in it reliably with a small, maintainable context surface.

Treat context engineering as a system design task, not as a chat promise. Use this skill when the user asks to improve how agents receive, route, remember, enforce, or verify repository context. This skill audits and designs the context system; `git-workflow` owns the actual rules for branching, committing, merging, pushing, tagging, and release flow.

## Core outcome

Prefer a minimal repo baseline, with durable memory owned by the agent/harness rather than the repository. Reliable agent behavior should be encoded in persistent/contextual layers:

- global `AGENTS.md` — stable cross-repo policy and routing defaults
- repo `AGENTS.md` — repo-specific normative rules, gates, bootstrap, and local overrides
- global/repo skills — reusable workflows and detailed procedures; keep prime/meta workflows here rather than duplicating them into every repo; use `git-workflow` for Git lifecycle rules and this skill for context-system design/audit
- extensions/tools — machine-readable checks and agent affordances, including optional Pi extensions when they make context checks easier or more reliable
- hooks/CI/pipelines — enforcement for rules that must survive agent forgetfulness or human variation
- agent/harness memory — durable non-normative context, decisions, preferences, and handoff state

Use this repo document baseline:

- `README.md` — human/operator entry point
- `AGENTS.md` — normative agent behavior, guardrails, bootstrap, routing, and gates
- agent/harness memory — stable current truth, durable non-normative context, and handoff state; in Pi, use pi-memory tools instead of repo-local memory files
- `TODO.md` — active open work only
- `CHANGELOG.md` — curated outward-facing change history

Do not create or expand repo-local memory files by default when an agent-level memory system is available. Use repo-local memory files only as an explicit compatibility/legacy bridge or when the user asks for repo-contained context; if kept, gitignore them unless the repo explicitly versions them.

Use compact frontmatter on maintained Markdown files except `README.md`. Do not add YAML frontmatter to README files; their role is obvious and the metadata is noise there.

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
- "audit this repo's context engineering"
- "review AGENTS.md / skills / extensions for this repo"
- "create AGENTS.md / TODO.md"
- "standardize repo docs for agents"
- "bootstrap agentic coding docs"
- "add pi-memory and routing docs"
- "migrate repo memory context into agent memory"
- "turn this repo into an agentic-coding repo"
- "use templates for README, AGENTS, TODO, CHANGELOG, and pi-memory capture"

Do not trigger for:

- ordinary prose editing with no repo governance angle
- app architecture design unrelated to agent docs
- one-off README copyediting unless baseline alignment is requested
- creating a skill itself; use `skill-creator` for that
- executing Git operations or deciding branch/commit/merge/push mechanics; use `git-workflow` for those rules

## Required working rules

1. Inspect before writing.
2. Preserve existing project truth; do not overwrite useful repo-specific content with generic templates.
3. Keep the baseline small. Add extra docs only when they provide durable value and have a clear update trigger.
4. Treat code, config, tests, and executable checks as technical ground truth.
5. Treat git history as history; do not duplicate it into memory or changelog.
6. Never put secrets in generated docs.
7. Keep changes reviewable and scoped to the user's requested alignment.
8. Do not rely on promises like “the agent will remember”; encode important behavior in AGENTS.md, skills, extensions, hooks, CI, or memory according to its role.

## Context authority and routing

When sources conflict, apply this order unless repo policy explicitly says otherwise:

1. System/developer/user instructions in the active session.
2. Repo-local `AGENTS.md` and contribution/release policy for the target repo.
3. Global `AGENTS.md` defaults.
4. Loaded skills for the task family, especially prime/meta skills such as this skill and `skill-creator`.
5. Agent/harness memory for durable facts, decisions, preferences, and handoff state; memory is not a rule source.
6. README/docs for human-facing facts and procedures.

Route each rule to the lowest durable layer that can reliably enforce or teach it:

- short binding rule or gate → `AGENTS.md`
- detailed repeatable workflow → skill or bundled skill reference
- machine-checkable condition → extension/tool, script, hook, or CI
- project fact or setup instruction → README/runbook/docs
- current task state, durable preference, or completed TODO archival → agent/harness memory

## Default workflow

### 1. Diagnose the target repo

Read or inspect, as available:

- file tree and root docs
- existing `README.md`, `AGENTS.md`, legacy repo memory files, `TODO.md`, `CHANGELOG.md`
- whether an agent/harness memory system is available, e.g. Pi with the pi-memory extension
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

Default to repo docs plus agent-owned memory. For new baselines, use pi-memory tools when available; prefer recording stable project truth in the agent memory system and referencing that policy from `AGENTS.md` when useful. Add optional directories only when needed:

- `docs/adr/*` for durable decisions
- `docs/runbooks/*` for procedural how-to
- `docs/plans/*` for detailed plans rooted in active work
- `.agents/skills/*` for curated repo-local skills

Avoid default creation of:

- repo-local memory files as the primary durable memory store when agent/harness memory is available
- episodic memory folders
- duplicate ADR trees outside `docs/`
- broad policy catalogs
- session snapshot directories
- large root documentation indexes

### 3. Apply templates carefully

Templates live in `assets/`:

- `agents-template.md`
- `memory-template.md` — pi-memory capture checklist, not a repo file template
- `todo-template.md` — chooser explaining the two supported TODO structures
- `todo-roadmap-template.md` — SemVer release roadmap backlog
- `todo-priority-template.md` — P0/P1/P2 priority backlog
- `readme-template.md`
- `changelog-template.md`

Use them as scaffolds, not as blind overwrites.

For existing files:

- keep valid project-specific content
- add or correct frontmatter, except in `README.md` files
- remove only clearly obsolete duplication when approved or obviously safe
- align section roles and update triggers
- keep `AGENTS.md` short and operative
- if a repo-local memory file already exists and must remain, keep it compact, compatibility-oriented, gitignored unless explicitly versioned, and avoid diaries; otherwise prefer agent/harness memory
- keep `TODO.md` as open work only
- keep `CHANGELOG.md` outward-facing

### 4. Populate each file by role

Use `references/document-routing.md` for details.

Minimum expectations:

- `README.md`: concise project description, install, usage, license, and lightweight verification/troubleshooting when useful; avoid detailed repo-structure, agent-routing, backlog, changelog, and internal architecture sections by default
- `AGENTS.md`: role/behavior, hard rules, bootstrap/read order, document roles, gates/completion rules, and repo-specific overrides of global policy
- agent/harness memory: current stable truth, long-term non-normative context, active handoff state, and durable cross-repo facts/preferences
- optional repo-local memory file: only compatibility/legacy or explicitly repo-contained current truth; keep compact, gitignored unless explicitly versioned, and point agents toward the harness memory when available
- `TODO.md`: active open work only; no completed history; no checked-off archive; close/remove completed items during wrap-up before push readiness
- `CHANGELOG.md`: Keep a Changelog categories and SemVer when the repo versions releases; include user/operator/release-relevant changes before release/push gates when required

### 5. Encode closeout and push gates

When aligning a repo for reliable agents, ensure closeout order and push gates are represented in the context system instead of trusting the active chat. Defer the authoritative Git lifecycle details to `git-workflow`; this skill checks that repos point agents to that workflow and expose repo-specific gates/overrides clearly.

Recommended closeout order to reference from `AGENTS.md` or a repo-local skill:

1. inspect `git status` and branch/worktree state
2. identify unrelated user changes and stop if unsafe
3. update/close durable task state: remove or check off completed `TODO.md` items and archive completed memory todos
4. decide SemVer impact: no bump, patch, minor, or major
5. update `CHANGELOG.md` for release-relevant changes, or document why no changelog entry is needed
6. run the smallest relevant verification
7. commit only after the doc/context cleanup and SemVer decision are complete
8. for release-relevant work, suggest version bump/tag/release steps before push/merge
9. before push, present the push gate result and require explicit push approval

Recommended push gate content:

- TODO cleanup: completed repo TODOs removed/checked off; completed memory todos archived; intentionally open items named
- CHANGELOG/SemVer: changelog entry present when release-relevant; SemVer impact stated
- verification: commands run and result
- target: branch/remote/tag push target stated

Prefer hooks/CI for enforceable checks such as changelog presence or version bump policy. Treat TODO cleanup as a required agent/human checklist unless the repo has a machine-readable TODO format.

### 6. Add frontmatter to maintained Markdown, except README

Do not add YAML frontmatter to `README.md` files. For other maintained Markdown files, use the four fields consistently:

- `role`: what the file is for
- `contains`: what belongs here
- `not-contains`: what must not be stored here
- `write-when`: the update trigger

See `references/frontmatter.md`.

### 7. Verify

After edits:

- re-read changed files for consistency
- check that file roles do not overlap unnecessarily
- check that bootstrap/routing references match actual files and the selected memory ownership model
- run relevant repo checks if docs affect setup or commands
- check git status and summarize only changed files

If no durable project truth changed outside the new docs, say so; do not invent memory content.

## Recommended outputs

When proposing or completing work, report:

- files created/changed
- memory ownership choice made: agent/harness memory vs optional repo-local memory file
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
