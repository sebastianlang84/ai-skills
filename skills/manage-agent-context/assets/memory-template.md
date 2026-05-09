# Memory capture checklist

Choose one memory system of record for durable agent context. Do not maintain parallel harness and repo-local memory unless the user explicitly accepts that cost.

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
