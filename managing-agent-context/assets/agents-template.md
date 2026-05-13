# AGENTS.md

<!-- Principle: as little as necessary, as much as needed. Keep global defaults in global agent instructions and skills; put only repo-local overrides here. Target: <=45 lines. Remove comments and unknown rows before finalizing. -->

## Role & Behaviour
- Role: coding agent for this repo.
- Change posture: <!-- conservative maintenance | production safety first | fast prototyping | library/API stability | research/exploration | automation/tooling -->
- Repo-specific behaviour overrides: <!-- omit if none -->

## Rules
<!-- Repo-specific hard rules and stop conditions; do not duplicate global procedures. -->
- Context principle: as little as necessary, as much as needed — no rule, file, or section without a clear job.
- Verification: <!-- repo's smallest relevant check(s), or where to find them -->
- Worktree safety: <!-- repo-specific generated files, protected paths, or ownership constraints -->
- Stop and ask when: <!-- repo-specific ambiguity/destructive/production/data conditions -->

## Document Roles
<!-- Only list files this repo actually uses. -->
| File | Role | Write when |
| --- | --- | --- |
| `README.md` | Human/operator guide | Setup, usage, operation, or support changes |
| `TODO.md` | Active open work only | Work or priorities change |
| `CHANGELOG.md` | User/operator-facing change history | Release-relevant change is introduced |
| `.agents/skills/*` | Repo-local skills only | A reusable repo-specific workflow is needed |

## Repo Facts
- Purpose: <!-- one verified sentence -->
- Primary stack: <!-- verified from code/config -->
- Main verification command: <!-- command -->
