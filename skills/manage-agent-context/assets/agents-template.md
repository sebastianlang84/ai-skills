---
role: Normative repo-local agent behavior, routing, and overrides
contains: Repo-specific role, hard rules, document routing, Git workflow choice, verification and release policy
not-contains: Global agent defaults, long procedures, detailed runbooks, project state, task history
write-when: Repo-specific behavior, routing, gate, or policy changes
---

# AGENTS.md

<!-- Target length: <=45 lines. Keep global defaults in global AGENTS.md and skills; put only repo-local overrides here. Remove comments and unknown rows before finalizing. -->

## 1) Role & Behaviour
<!-- Repo-specific behavior only; omit generic global defaults unless overriding them. -->
- Role:
- Change posture: <!-- conservative maintenance | production safety first | fast prototyping | library/API stability | research/exploration | automation/tooling -->

## 2) Rules
<!-- Repo-specific hard rules and stop conditions; do not duplicate global Git/coding procedures. -->
- Read first:
- Scope boundaries:
- Verification:
- Subagents: use for context-heavy scouting/review when it keeps main context smaller.
- Secrets/data:
- Stop and ask when:

## 3) Document Roles
<!-- Only list files this repo actually uses. Use agent/harness memory for durable non-normative context when available. -->
| File | Role | Write when |
| --- | --- | --- |
| `README.md` | Human/operator guide | Setup, usage, operation, or support changes |
| `TODO.md` | Active open work only | Work or priorities change |
| `CHANGELOG.md` | User/operator-facing change history | Release-relevant change is introduced |
| `.agents/skills/*` | Repo-local skills only | A reusable repo-specific workflow is needed |

## 4) Repo
<!-- Repo facts and local Git/release policy. Details stay in git-workflow unless this repo overrides them. -->
- Purpose:
- Main components:
- Git workflow:
- Primary/integration branches:
- Versioning/changelog:
