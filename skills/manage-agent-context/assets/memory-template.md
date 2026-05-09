---
role: Pi-memory capture checklist for follow-up agent sessions
contains: Suggested durable facts, decisions, preferences, todos, and handoff fields for pi-memory tools
not-contains: Repo-local memory file content, diary-style history, procedural how-tos, rules, secrets
write-when: The pi-memory capture policy or field guidance changes
---

# Pi-memory capture checklist

Use pi-memory tools instead of creating or expanding repo-local memory files.

## Durable fact / decision / preference

- Kind: fact | decision | preference
- Scope: repo | project | global | session
- Title: [short searchable title]
- Summary: [stable current truth; no secrets]
- Tags: [repo/project/topic]

## Active todo

- Kind: todo
- Scope: repo | project | session
- Summary: [open work only; link files/issues if useful]

## Handoff

Use `memory_handoff_save` with:

- Goal
- Current state
- Next steps
- Done
- Changed/relevant files
- Verification
- Blockers/open questions/risks

Do not store rules here; put normative behavior in `AGENTS.md`.
