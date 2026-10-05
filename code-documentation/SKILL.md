---
name: code-documentation
description: "Update or review project documentation after code changes. Use when user-visible behavior, APIs, CLI commands, config, schemas, architecture, PRD status/scope, changelog entries, TODO cleanup, or ADR-worthy decisions may need documentation. Do not use for ordinary prose editing or agent-context/memory routing."
---

# Code Documentation

## Goal

Keep project documentation accurate while using each artifact for its intended role, not as a catch-all dumping ground.

If the repo has a PRD (`PRD.md` or `docs/product/`), read [references/prd.md](references/prd.md) before
changing it: a PRD holds intent, scope and status, never the documentation of implemented features.

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
- `AGENTS.md`, skills and memory are agent context, not feature documentation; `context-engineering` decides what goes there.

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

## ADR threshold

Offer an ADR only when **all three** hold:

1. **Hard to reverse** — changing your mind later carries real cost.
2. **Surprising without context** — a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons.

If it is easy to reverse, you will just reverse it. If it is not surprising, nobody will wonder. If there was no alternative, there is nothing to record beyond "we did the obvious thing."

What typically qualifies: architectural shape, integration patterns between components, technology choices carrying lock-in (the ones that would take a quarter to swap, not every library), ownership and scope boundaries — the explicit no's as much as the yes's — deliberate deviations from the obvious path ("manual SQL instead of an ORM because X", which stops the next engineer from "fixing" it), constraints invisible in the code (compliance, a partner's response-time contract), and non-obvious rejected alternatives.

Keep it short. An ADR can be a single paragraph — the value is recording *that* a decision was made and *why*, not filling in sections.

```md
# Use SQLite for local storage

Ruled out Postgres because the tool must run with no service to install.
SQLite's single-writer limit is acceptable: writes only happen during indexing.
```

Add `Status` (`proposed | accepted | deprecated | superseded by ADR-NNNN`) when decisions get revisited, `Considered Options` when the rejected alternatives are worth remembering, and `Consequences` when non-obvious downstream effects need calling out. Most ADRs need none of them.

Number sequentially: scan the ADR directory for the highest number and increment.

## CHANGELOG threshold

Update `CHANGELOG.md` only when the repo maintains one and the change is user/operator-visible. Do not record every commit or purely internal refactor.

## Boundary with context-engineering

If the change concerns agent instructions, skill routing, memory ownership, tool exposure, MCP/extension context policy, hooks/CI enforcement, or context bloat, use the `context-engineering` workflow instead of treating it as ordinary code documentation.

## Output style

Make compact documentation patches. In summaries, state which docs were updated and why. If no documentation changed, state the reason briefly.
