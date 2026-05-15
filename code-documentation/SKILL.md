---
name: code-documentation
description: "Update or review project documentation after code changes. Use when user-visible behavior, APIs, CLI commands, config, schemas, architecture, PRD status/scope, changelog entries, TODO cleanup, or ADR-worthy decisions may need documentation. Do not use for ordinary prose editing or agent-context/memory routing."
---

# Code Documentation

## Goal

Keep project documentation accurate while using each artifact for its intended role, not as a catch-all dumping ground.

## Core rule

Do not use the PRD as general feature documentation.

PRDs describe product intent, scope, requirements, acceptance criteria, constraints, and implementation status. Implemented behavior belongs in the canonical user or developer docs, with short PRD links when useful.

Example:

```md
Feature: Hybrid Search
Status: implemented in v0.4.0
User docs: docs/user/features/search.md
API docs: docs/developer/api.md
```

## Required workflow

1. Inspect the actual changed behavior, not only the diff summary.
2. Follow the repository's existing documentation layout first.
3. Decide the canonical destination for each documentation update.
4. Prefer one canonical explanation plus short cross-links elsewhere.
5. Keep README as an entry point, not full documentation.
6. Keep PRD concise; use status and links for implemented features.
7. If no docs should change, say why in the final summary.

## Documentation routing

Use the existing repo conventions before adding new files. Do not create new top-level docs just because they are listed here. Add or restructure docs only when the file has a clear owner, update trigger, expected reuse, and no better existing home.

Common homes:

- `README.md` — short project entry point: what it is, setup, key commands, links.
- `docs/product/` or `PRD.md` — product intent, scope, requirements, acceptance criteria, product-level constraints, feature status.
- `docs/user/` — user-facing behavior, workflows, examples, CLI usage, configuration, troubleshooting.
- `docs/developer/` — architecture, APIs, schemas, tests, local development, deployment, internals.
- `docs/adr/` — durable architectural decisions with lasting consequences.
- `CHANGELOG.md` — user/operator-visible release history, if the repo maintains one.
- `TODO.md` or issue tracker — active open work only; remove or archive completed items.
- `AGENTS.md` or equivalent — active agent rules, stop conditions, and repo-specific gates only; not feature documentation.
- Memory systems — durable non-normative context such as preferences, prior decisions, progress notes, or handoffs; not canonical docs, not rules, not backlog, not changelog, and not enforcement.

## Decision heuristic

Ask after meaningful code changes:

1. Can a user see or use this?
   - Update user docs and changelog if maintained.
2. Did an API, CLI, config, schema, file format, or tool contract change?
   - Update developer docs and references.
3. Did intended product behavior, scope, acceptance criteria, or feature status change?
   - Update the PRD or product docs.
4. Is there a lasting architectural decision future maintainers must understand?
   - Add or update an ADR.
5. Is this active unfinished work?
   - Track it in TODO/issue system, not changelog or PRD prose.
6. Is this only an implementation detail?
   - Prefer no docs change; add code comments only when the reason is not obvious.

## PRD handling

Use PRDs for:

- problem statement
- product goals
- scope and non-scope
- requirements
- user stories
- acceptance criteria
- product-level constraints
- feature status and links to canonical docs

Avoid using PRDs for:

- implementation details
- every small code change
- full API reference
- bugfix history
- internal class/function explanations
- release notes

## ADR threshold

Create or update an ADR only for decisions with lasting consequences, such as storage choices, public contracts, major dependencies, security boundaries, deployment model, data model, or architecture direction.

Minimal ADR shape:

```md
# ADR-0001: Use SQLite for local storage

## Status
Accepted

## Context
...

## Decision
...

## Consequences
...
```

## CHANGELOG threshold

Update `CHANGELOG.md` only when the repo maintains one and the change is user/operator-visible. Do not record every commit or purely internal refactor.

Example:

```md
## 0.4.0

### Added
- Added `codemap_context` for file-centered retrieval.

### Changed
- Improved FTS ranking for path matches.
```

## Code comments

Comment why, not obvious what.

Good:

```ts
// Keep this deterministic so repeated agent runs produce stable retrieval order.
```

Bad:

```ts
// Increment i by 1.
i++;
```

## Boundary with managing-agent-context

If the change concerns agent instructions, skill routing, memory ownership, tool exposure, MCP/extension context policy, hooks/CI enforcement, or context bloat, use the `managing-agent-context` workflow instead of treating it as ordinary code documentation.

## Avoid

- Duplicating the same explanation across PRD, README, changelog, and feature docs.
- Recording completed work in TODO.
- Adding ADRs for routine implementation choices.
- Putting feature documentation in `AGENTS.md`.
- Treating memory as canonical product, user, developer, changelog, TODO, or enforcement documentation.
- Creating new documentation structures when existing repo conventions are sufficient.

## Output style

Make compact documentation patches. In summaries, state which docs were updated and why. If no documentation changed, state the reason briefly.
