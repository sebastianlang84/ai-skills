# Document Routing

Principle: as little as necessary, as much as needed — one clear home per kind of information.

## Conflict rule

- Technical facts must match code, config, tests, schemas, and deploy manifests. Fix docs that contradict them.
- Binding agent rules belong in active instructions, agent instruction files, skills, tools, hooks, or CI; not in memory, README, or chat promises.
- Loaded skills provide task-specific procedures, but must not silently override higher-priority instructions unless that override is explicit and intended.

## Routing table

| Information | Put it here | Avoid |
| --- | --- | --- |
| Project purpose, setup, usage, verification, support, license | `README.md` | Backlog, agent rules, ADR history, memory |
| Normative agent behavior, bootstrap/read order, hard constraints, stop conditions, repo-specific gates | `AGENTS.md`, `CLAUDE.md`, or equivalent active agent instruction file | Project state, task history, long runbooks, verbose policy docs |
| Reusable task-family workflow | Skill `SKILL.md` | One-off project facts, large examples, unrelated policies |
| Detailed skill examples/templates/domain notes | Skill `references/` or `assets/` | Always-loaded instruction files |
| Durable non-normative facts, preferences, decisions, handoff state | The repo's chosen memory system | Rules, backlog, changelog, diaries, secrets |
| Active open work | TODO system or issue tracker | Completed-work archive, changelog, session notes |
| User/operator-visible release history | `CHANGELOG.md` | Internal notes, every commit, task diary |
| Durable decisions | `docs/adr/*` | README bloat, chat-only decisions |
| Repeatable procedures | `docs/runbooks/*` | Agent instruction bloat |
| Detailed active plans | `docs/plans/*`, linked from TODO/issue | Permanent backlog history |
| Repo-specific reusable agent workflows | `.agents/skills/*` | Generic/global workflows |

## Add-file test

Before adding a long-lived doc, all should be true:

1. It does not fit better in code, config, git history, or an existing file.
2. It will be reused.
3. It is stable enough to maintain.
4. Its update trigger is clear.
5. Humans or agents are likely to find and use it.
