# Document Routing

Use this routing model to avoid duplicate sources of truth.

## Ground truth order

For technical facts:

1. Code, config, tests, generated schemas, executable checks
2. Runtime/deploy manifests and environment examples
3. Root baseline docs
4. Deeper docs under `docs/`
5. Git history for historical details

For agent behavior and context routing:

1. Active system/developer/user instructions
2. Repo-local `AGENTS.md` and contribution/release policy
3. Global `AGENTS.md`
4. Loaded skills and skill references
5. Agent/harness memory for durable facts/preferences/handoffs, not rules
6. README/docs for human-facing project facts

Do not put technical facts in docs that contradict code/config. Do not rely on memory or chat promises for binding agent rules; encode them in AGENTS.md, skills, tools, hooks, or CI.

## Root baseline

### `README.md`

Human/operator entry point.

Belongs here:

- what the repo is
- why it exists
- lightweight project structure when it helps operators
- setup and usage
- verification commands
- troubleshooting/support
- status/license

Does not belong here:

- active task backlog
- agent behavior rules
- detailed ADR history
- durable agent memory

### `AGENTS.md`

Normative agent operating rules.

Belongs here:

- role and behavior
- hard constraints
- bootstrap/read order
- gates, including closeout/push gates when repo-specific
- document routing overview
- completion expectations
- SemVer/changelog/TODO cleanup expectations when they differ from global defaults

Does not belong here:

- project state
- task history
- long runbooks
- detailed service design
- verbose policy documents

### Agent/harness memory (Pi: pi-memory tools)

Reset-resilient context for the next agent. Prefer this over repo-local `MEMORY.md` when available.

Belongs here:

- stable current truth
- durable non-normative context
- concise active handoff state

Does not belong here:

- rules or binding constraints
- active work backlog better kept in `TODO.md`
- diary logs
- detailed completed task history
- secrets

### Repo-local `MEMORY.md` (legacy/compatibility only)

Use only when explicitly required by repo policy, compatibility, or user instruction. Keep it compact, ignore it from Git unless the repo intentionally versions it, and migrate durable context to the agent/harness memory system where possible.

### `TODO.md`

Active open work only.

Belongs here:

- current priorities
- open tasks
- links to detailed plans when needed

Does not belong here:

- completed tasks
- changelog entries
- session notes
- detailed implementation plans

During wrap-up and before push readiness, completed items should be removed or checked off according to repo policy. Avoid using TODO.md as a completed-work archive.

### `CHANGELOG.md`

Outward-facing user/operator-relevant history.

Belongs here:

- added/changed/fixed/removed/deprecated/security/breaking entries
- released version sections if releases exist
- SemVer-relevant release notes for patch/minor/major decisions

Does not belong here:

- internal-only notes
- every commit
- task diaries
- standing defaults

## Optional docs

### `docs/adr/*`

Use for durable decisions: context, decision, consequences, alternatives when useful.

### `docs/runbooks/*`

Use for repeatable procedures humans or agents will follow.

### `docs/plans/*`

Use for detailed execution plans rooted in active TODO items. Remove or archive when no longer active if the repo policy says so.

### `.agents/skills/*`

Use only for curated repo-local skills and closely related skill assets.

## Add-file test

Before adding a new doc, all should be true:

1. It does not fit better in code, config, git history, or an existing baseline file.
2. It will be reused.
3. It is stable enough to maintain.
4. Its update trigger is clear.
5. Humans or agents are likely to find and use it.
