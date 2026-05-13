# Migration Notes

Use these notes when a repo already has ad-hoc or oversized agent documentation.

## Safe migration principle

As little as necessary, as much as needed. Prefer consolidation before deletion. Do not remove files with possible user-owned value unless the user approves or the repo policy clearly allows it.

## Common source files

You may encounter:

- `AGENTS.md`
- `CLAUDE.md`/`claude.md` adapters for Anthropic models
- other runtime-specific adapter instruction files
- `.cursorrules`
- `.cursor/rules/*`
- `.roo/*`
- `agents/`, `.agents/`, runtime-specific agent folders
- `docs/policies/*`
- `docs/adr/*` or `adr/*`
- memory/session folders

## Recommended handling

### Existing agent instruction files

Align in place. Preserve repo-specific guardrails. Remove duplication only when safe.

### Runtime-specific instruction files

Do not blindly delete. Keep runtime-specific adapter files only when the runtime actually reads them or users rely on them. If the file is only adapter glue, keep it tiny and avoid target-doc references to it unless users need to discover it. Options:

1. keep as a thin adapter pointing to the canonical agent instruction file (`AGENTS.md`, `CLAUDE.md`, or equivalent),
2. merge durable rules into the canonical agent instruction file and ask before deletion,
3. leave untouched if the runtime requires it.

### Existing memory/session logs

Do not import diaries wholesale. Extract only stable current truth; do not copy secrets, credentials, raw chat logs, or personal notes.

### Existing policy docs

If a policy is short and operational, it may belong in the agent instruction file. If it is long reference material, keep it under `docs/` and link only when useful. Avoid making every policy file mandatory-read. If linked from the agent instruction file, state whether the policy is mandatory, advisory, or reference-only.

### Existing task files

Consolidate active work into the repo's chosen TODO system or issue tracker. Preserve detailed active plans under `docs/plans/*` if useful.

## Adapter pattern

When a tool requires a special file, keep it tiny and point to the canonical source. Keep runtime-specific adapter files only when the runtime actually reads them or users rely on them.

Example:

```markdown
# CLAUDE.md

This repo uses `AGENTS.md` as the canonical agent instruction file.

Read and follow `AGENTS.md` for repo rules. Use the repo's chosen memory and TODO systems only when needed.
```

Only use this pattern if the tool actually reads that adapter file. Keep adapter contents minimal and avoid linking it from human docs unless the user explicitly asks.
