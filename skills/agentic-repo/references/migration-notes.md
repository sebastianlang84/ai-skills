# Migration Notes

Use these notes when a repo already has ad-hoc or oversized agent documentation.

## Safe migration principle

Prefer consolidation before deletion. Do not remove files with possible user-owned value unless the user approves or the repo policy clearly allows it.

## Common source files

You may encounter:

- `CLAUDE.md`
- `.cursorrules`
- `.cursor/rules/*`
- `.roo/*`
- `AGENTS.md`
- `agents/`, `.agents/`, `.claude/`
- `docs/policies/*`
- `docs/adr/*` or `adr/*`
- memory/session folders

## Recommended handling

### Existing `AGENTS.md`

Align in place. Preserve repo-specific guardrails. Remove duplication only when safe.

### Existing `CLAUDE.md` or runtime-specific files

Do not blindly delete. Options:

1. keep as a thin adapter pointing to `AGENTS.md`,
2. merge durable rules into `AGENTS.md` and ask before deletion,
3. leave untouched if the runtime requires it.

### Existing memory/session logs

Do not import diaries into `MEMORY.md`. Extract only stable current truth and durable non-normative context. Active work goes to `TODO.md`; history remains in git or archive if needed.

### Existing policy docs

If a policy is short and operational, it may belong in `AGENTS.md`. If it is long reference material, keep it under `docs/` with frontmatter and link only when useful. Avoid making every policy file mandatory-read.

### Existing ADR trees

Prefer `docs/adr/*` as the durable ADR location. If another ADR tree exists, ask before moving. Do not create a second tree.

### Existing task files

Consolidate active work into `TODO.md`. Do not keep completed checklists as active TODOs. Preserve detailed active plans under `docs/plans/*` if useful.

## Adapter pattern

When a tool requires a special file, keep it tiny and point to the canonical source.

Example:

```markdown
# CLAUDE.md

Follow `AGENTS.md` for repo rules. Read `MEMORY.md` and `TODO.md` as instructed there.
```

Only use this pattern if the tool actually reads that adapter file.
