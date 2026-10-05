# Review Checklist

Principle: as little as necessary, as much as needed.

Use before considering a repo context alignment complete.

## Required shape

- Baseline files exist only where useful and match `references/document-routing.md`.
- Agent instruction file is short, normative, and operational. Global instructions cover universal rules; repo instructions cover repo-specific overrides.
- Extra docs have clear reuse, owner/update trigger, and discovery path.

## Routing checks

- No source contains information routed elsewhere by `document-routing.md`.
- No setup instructions are hidden only in agent instructions.
- References point to existing files/systems.

## Agent usability checks

- Bootstrap/read order, stop-and-ask conditions, verification, secrets handling, and dirty-worktree protection are explicit.
- Closeout/push gates are explicit when relevant.
- Relevant skills are referenced by name/path instead of duplicating full procedures.
- Skill descriptions trigger intended tasks and avoid nearby false positives.
- Enforceable gates use hooks, CI, scripts, tools, or extensions.
- The repository freshness contract is explicit: maintained docs/context artifacts have clear update triggers, and release/user-visible changes route to changelog, README, TODO, ADRs, or canonical docs as appropriate.
- Normal tasks do not require reading a large policy corpus.
