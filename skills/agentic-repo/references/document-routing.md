# Document Routing

Use this routing model to avoid duplicate sources of truth.

## Ground truth order

1. Code, config, tests, generated schemas, executable checks
2. Runtime/deploy manifests and environment examples
3. Root baseline docs
4. Deeper docs under `docs/`
5. Git history for historical details

Do not put technical facts in docs that contradict code/config.

## Root baseline

### `README.md`

Human/operator entry point.

Belongs here:

- what the repo is
- why it exists
- project structure
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
- gates
- document routing overview
- completion expectations

Does not belong here:

- project state
- task history
- long runbooks
- detailed service design
- verbose policy documents

### `MEMORY.md`

Reset-resilient context for the next agent.

Belongs here:

- stable current truth
- concise handoff state
- durable non-normative context
- latest 3 completed tasks max

Does not belong here:

- rules or binding constraints
- active work backlog
- diary logs
- detailed completed task history
- secrets

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

### `CHANGELOG.md`

Outward-facing user/operator-relevant history.

Belongs here:

- added/changed/fixed/removed/deprecated/security/breaking entries
- released version sections if releases exist

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
