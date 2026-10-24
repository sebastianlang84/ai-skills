# Memory capture checklist

Choose one system of record for curated durable knowledge. Harness auto memory (Claude Code `MEMORY.md`, Codex memories) is a separate, bounded layer: audit it for stale or normative entries instead of counting it as a parallel system.

Never store secrets, raw logs/diaries, backlog/history, or binding rules in memory.

## Save durable memory only for

- Stable fact: current truth useful in future sessions.
- Decision: chosen direction plus brief rationale.
- Preference: durable user/project preference.
- Handoff: current task state across context loss.

## Minimal fields

- Kind: fact | decision | preference | handoff
- Scope: repo | project | global | session
- Title: short searchable title
- Summary: stable current truth; no secrets
- Cleanup/update trigger: when this should change or expire

## Handoff fields

- Goal
- Current state
- Next steps
- Done
- Relevant files
- Verification
- Blockers/open questions/risks
