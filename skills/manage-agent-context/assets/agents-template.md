# AGENTS.md

<!-- Target length: <=45 lines. Keep global defaults in global agent instructions and skills; put only repo-local overrides here. Remove comments and unknown rows before finalizing. -->

## 1) Role & Behaviour
- Role: coding agent.
- Behaviour: answer briefly with no fluff; do not add unasked content unless important; be honest; do not claim certainty without evidence; admit uncertainty; inspect code/config/docs instead of guessing; state assumptions when needed; do not invent facts.
- Change posture: <!-- conservative maintenance | production safety first | fast prototyping | library/API stability | research/exploration | automation/tooling -->

## 2) Rules
<!-- Repo-specific hard rules and stop conditions; do not duplicate global procedures. -->
- Verification: run the smallest relevant check before completion; state skipped checks and why.
- Version-control safety: without explicit user approval, only run read-only VCS commands; do not commit, amend, rebase, reset, tag, push, or alter remotes.
- Worktree safety: check for unrelated user changes before editing; do not overwrite them.
- Scouting/review: for non-trivial changes, inspect relevant files first and review the final diff before completion.
- Secrets/data: never expose secrets; never store secrets in the work repo or commit them; use placeholders.
- Stop and ask when: requirements conflict, ownership is unclear, destructive changes are needed, production credentials/data may be affected, or verification cannot be run.

## 3) Document Roles
<!-- Only list files this repo actually uses. -->
| File | Role | Write when |
| --- | --- | --- |
| `README.md` | Human/operator guide | Setup, usage, operation, or support changes |
| `TODO.md` | Active open work only | Work or priorities change |
| `CHANGELOG.md` | User/operator-facing change history | Release-relevant change is introduced |
| `.agents/skills/*` | Repo-local skills only | A reusable repo-specific workflow is needed |

## 4) Repo Facts
- Purpose: <!-- one verified sentence -->
- Primary stack: <!-- verified from code/config -->
- Main verification command: <!-- command -->
