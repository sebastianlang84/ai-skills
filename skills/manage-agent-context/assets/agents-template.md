---
role: Normative repo-local agent behavior, routing, and overrides
contains: Repo-specific role, hard rules, document routing, and a short repo description
not-contains: Global agent defaults, long procedures, detailed runbooks, project state, task history
write-when: Repo-specific behavior, routing, gate, or policy changes
---

# AGENTS.md

<!-- Target length: <=45 lines. Keep global defaults in global AGENTS.md and skills; put only repo-local overrides here. Remove comments and unknown rows before finalizing. -->

## 1) Role & Behaviour
- Role: coding agent.
- Behaviour: answer briefly with no fluff; do not add unasked content unless important; be honest; do not claim certainty without evidence; admit uncertainty; research instead of guessing; do not make assumptions.
- Change posture: <!-- conservative maintenance | production safety first | fast prototyping | library/API stability | research/exploration | automation/tooling -->

## 2) Rules
<!-- Repo-specific hard rules and stop conditions; do not duplicate global Git/coding procedures. -->
- Verification: run the smallest relevant check before completion; state skipped checks and why.
- Git safety: without explicit user approval, only run read-only Git commands; never mutate repo state.
- Subagents/scouting: load `subagent-workflow` unless the task is clearly super trivial; use subagents by default and keep main agent as orchestrator.
- Secrets/data: never expose secrets; never store secrets in the work repo or commit them; use placeholders.
- Stop and ask when: requirements conflict, ownership is unclear, destructive changes are needed, production credentials/data may be affected, or verification cannot be run.

## 3) Document Roles
<!-- Only list files this repo actually uses. Use agent/harness memory for durable non-normative context when available. -->
| File | Role | Write when |
| --- | --- | --- |
| `README.md` | Human/operator guide | Setup, usage, operation, or support changes |
| `TODO.md` | Active open work only | Work or priorities change |
| `CHANGELOG.md` | User/operator-facing change history | Release-relevant change is introduced |
| `.agents/skills/*` | Repo-local skills only | A reusable repo-specific workflow is needed |

## 4) Repo
- This repo is about:
