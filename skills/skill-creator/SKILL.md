---
name: skill-creator
description: Create new skills and improve existing ones in an agent-agnostic way. Use this skill when the user wants to design, rewrite, review, validate, or simplify a SKILL.md, improve a skill's trigger description or structure, add or refine scripts, references, or assets, or make an existing skill more portable across agents. Do not use this skill just to list, locate, install, update, or remove skills.
---

# Skill Creator

Use this skill to author and improve skills as portable artifacts, not as one-off prompts for a single runtime.

## Core model

A skill is a folder that teaches an agent how to perform a class of tasks through:

- a required `SKILL.md`
- optional `scripts/`
- optional `references/`
- optional `assets/`

Treat the skill itself as the durable artifact. Agent-specific wiring, discovery hooks, and trigger tests are secondary adapters.

## Storage model

Default to the shared skill stores:

- global: `~/.pi/agent/skills/<skill-name>/`
- repo-local: `<repo>/.agents/skills/<skill-name>/`

If another agent needs a different entrypoint such as a symlink, config file, or metadata file, treat that as adapter glue. Do not make agent-specific locations the primary source of truth unless the user explicitly asks for that.

## When to use this skill

Use this skill when the user wants to:

- create a new skill
- rewrite or review an existing `SKILL.md`
- improve a skill's triggering language
- simplify or restructure a skill
- add or remove `scripts/`, `references/`, or `assets/`
- make a skill more portable across agents
- validate that a skill folder is coherent and maintainable

Do not use this skill when the task is only to:

- discover which skills exist
- install, update, or remove a skill
- identify where a skill was installed from

Those belong to a skill inventory or lifecycle workflow such as `skill-manager`.

## Working style

Prefer the smallest change that makes the skill clearer, more reusable, and less runtime-specific.

Bias toward:

- concise frontmatter
- explicit scope
- clear trigger language
- lean instructions in `SKILL.md`
- detailed material moved into `references/`
- deterministic repeated actions moved into `scripts/`

Avoid:

- runtime-specific assumptions in the core skill unless required
- giant monolithic `SKILL.md` files
- duplicating the same guidance in `SKILL.md` and `references/`
- extra docs like `README.md`, `CHANGELOG.md`, or process diaries inside the skill folder

## Default workflow

### 1. Understand the skill's job

Clarify:

- what task family the skill should cover
- what user wording should trigger it
- what should not trigger it
- what outputs or artifacts matter
- whether the skill should stay general or target a specific environment

If there is already a draft skill, read it before proposing changes.

### 2. Choose the simplest useful structure

Every skill needs `SKILL.md`.

Add `scripts/` when:

- the same code would otherwise be rewritten repeatedly
- reliability matters more than improvisation
- a deterministic helper is cheaper than prompt tokens

Add `references/` when:

- the skill needs large domain material
- only some use cases need the details
- the material would bloat `SKILL.md`

Add `assets/` when:

- the skill needs templates, fonts, images, starter projects, or other output resources

Do not create empty directories just because they are available.

### 3. Write or rewrite `SKILL.md`

The frontmatter is the trigger surface. Be precise.

Required fields:

- `name`
- `description`

Write `description` so it captures:

- what the skill helps with
- which user intents should trigger it
- important file types or contexts
- nearby cases that should not trigger it, when confusion is likely

The body should tell another agent how to use the skill well after it triggers. Keep runtime-neutral guidance in the body. Put agent-specific details in clearly marked adapter notes or references.

### 4. Keep the skill agent-agnostic by default

Assume the skill may be consumed by multiple agents.

That means:

- store the canonical skill in `~/.pi/agent/skills` or `<repo>/.agents/skills`
- avoid describing one agent's discovery mechanism as if it were universal
- avoid runtime-specific defaults unless the user names a target runtime
- keep adapter-specific instructions behind an explicit label such as `Claude adapter`, `Codex adapter`, or `Cursor adapter`

If the user explicitly targets one runtime, you may add adapter-specific instructions, but keep the core skill understandable without them.

See `references/agent_adapters.md` for the current adapter policy in this skill.

### 5. Validate

Run the basic validator after meaningful changes:

```bash
python3 scripts/quick_validate.py <path/to/skill-folder>
```

Validation here means:

- frontmatter parses
- required fields exist
- naming rules are sane
- the folder layout is coherent

This is structural validation, not proof that the skill works well.

### 6. Improve using realistic tasks

The best improvement loop is usually:

1. read the current skill
2. choose a few realistic user requests
3. inspect where the skill causes confusion, wasted work, or under-triggering
4. adjust the skill
5. validate again

Use lightweight manual review by default. Only reach for heavier benchmark or trigger-eval tooling when the user wants that rigor or the skill is important enough to justify it.

## Review checklist

When reviewing a skill, check:

- Is the `description` broad enough to trigger when useful but narrow enough to avoid obvious false positives?
- Does the body teach reusable behavior rather than narrate one example?
- Are scripts only included when they save real repeated effort?
- Are references discoverable from `SKILL.md`?
- Are agent-specific assumptions clearly separated from the core guidance?
- Is the skill small enough that another agent can actually use it reliably?

## Trigger-description guidance

Good descriptions usually:

- name the task family first
- mention concrete triggers or contexts
- mention important file types if relevant
- use direct language such as "Use this skill when..."
- stay comfortably under length limits

Bad descriptions usually:

- read like marketing copy
- describe implementation details instead of user intent
- enumerate dozens of examples
- rely on body sections for trigger logic

## Optional adapter tooling

Some workflows need runtime-specific tooling such as trigger evaluation, metadata generation, or discovery hooks. Treat those as optional adapters, not as the definition of the skill itself.

Current bundled scripts in this skill folder include some legacy Claude-oriented evaluation helpers. They are still useful when the target runtime is Claude, but they are not the default workflow for general skill authoring.

Use adapter-specific tooling only when one of these is true:

- the user explicitly targets that runtime
- the bug only appears in that runtime's discovery or trigger behavior
- the user asks for runtime-specific benchmarking

## Bundled resources in this skill

- `references/schemas.md`: JSON shapes used by the bundled evaluation tools
- `references/agent_adapters.md`: how to think about runtime-specific adapters
- `scripts/quick_validate.py`: neutral structural validation
- other scripts in `scripts/`: optional tooling, some of which are runtime-specific

## Editing guidance

When changing an existing skill:

- preserve the user's actual intent
- reduce accidental runtime lock-in
- remove dead complexity before adding new sections
- keep diffs reviewable
- prefer moving details out of `SKILL.md` over endlessly expanding it

When creating a new skill:

- start with the smallest viable structure
- create only the folders you truly need
- validate before adding optimization machinery

## Minimal skill template

```text
my-skill/
├── SKILL.md
├── scripts/        # only if needed
├── references/     # only if needed
└── assets/         # only if needed
```

Minimal frontmatter:

```yaml
---
name: my-skill
description: Use this skill when the user wants to ...
---
```

## Escalation rule

If the user asks for a runtime-specific implementation, keep the core skill portable and isolate the runtime-specific parts. If that is not possible, say so explicitly and explain what portability is being traded away.
