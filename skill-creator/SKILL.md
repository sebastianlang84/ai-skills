---
name: skill-creator
description: Create, audit, validate, repair, and improve portable agent skills. Use when designing a new skill, reviewing or simplifying a SKILL.md, improving trigger metadata, restructuring scripts/references/assets, or making a skill less runtime-specific. Do not use for unrelated package management or routine local inventory unless skill quality is the task.
---

# Skill Creator

Use this skill to create and improve skills as durable, portable artifacts. Keep `SKILL.md` concise: it should route, instruct, and point to deeper files instead of becoming a knowledge dump.

Do not read the large best-practice references by default. Read them only for `skill-creator` self-edits, deep audits, or when the user explicitly asks for their extra rigor.

When editing `skill-creator` itself, first read these ground-truth references from this skill folder and use them as the quality bar:

- `references/anthropic_skill_best_practices.md`
- `references/progressive_skill_best_practices_supabase_workshop.md`

## Mental model

```text
SKILL.md      = operational index: trigger, workflow, safety checks, links
references/   = deeper guidance, examples, domain detail
scripts/      = deterministic local helpers and validators
MCP/tools     = external access, remote APIs, authenticated actions
AGENTS.md     = stable project policy and routing rules
```

A skill folder contains:

- required `SKILL.md`
- optional `scripts/`
- optional `references/`
- optional `assets/`

Use the smallest structure that solves the recurring task.

## Canonical locations

Default to:

- global: `~/.pi/agent/skills/<skill-name>/`
- repo-local: `<repo>/.agents/skills/<skill-name>/`

Treat other runtime-specific entrypoints, symlinks, metadata files, or discovery hooks as adapter glue unless the user explicitly chooses them as source of truth.

## When to use

Use this skill when the user wants to:

- create a new skill
- audit, validate, repair, simplify, or restructure an existing skill
- rewrite or review `SKILL.md`
- improve trigger/frontmatter language
- add, remove, or reorganize `scripts/`, `references/`, or `assets/`
- make a skill more portable across agents
- decide whether guidance belongs in a skill, script, MCP/tool, AGENTS.md, or memory

For simple inventory or installation checks, inspect files directly; do not invent a large workflow.

Useful local inventory commands:

```bash
find ~/.pi/agent/skills .agents/skills -maxdepth 2 -name SKILL.md 2>/dev/null
rg '^name:|^description:' ~/.pi/agent/skills .agents/skills 2>/dev/null
```

Optional third-party discovery commands may help when requested and trusted; `npx` can fetch/execute external code, so get user approval before running it:

```bash
npx skills find <term>
npx skills list
npx skills check
npx skills update
```

On this machine the canonical global store is `~/.pi/agent/skills/`; if tooling writes to `~/.agents/skills/`, relocate rather than maintain two global stores.

## Required workflow

### 1. Audit before changing existing skills

Inspect the skill folder first. Check:

- trigger accuracy and likely false positives/negatives
- role and scope boundaries
- portability versus runtime lock-in
- whether `SKILL.md` is an index or a knowledge dump
- whether repeated fragile steps should be scripts
- whether referenced files exist and are directly discoverable
- whether validation exists for meaningful edits

Prefer targeted repairs over rewrites unless the structure is unsalvageable.

### 2. Clarify the job

Identify:

- task family covered by the skill
- user wording that should trigger it
- nearby tasks that should not trigger it
- required outputs or artifacts
- target runtime, if any
- risk level and needed strictness

### 3. Choose structure by need

Use only what the skill needs:

- `SKILL.md` for compact workflow, safety rules, and routing
- `references/` for long guidance, schemas, examples, or domain notes
- `scripts/` for deterministic checks, transformations, validators, or repeated commands
- `assets/` for templates, starter files, fonts, images, or other output resources

Avoid empty directories. Link important references directly from `SKILL.md`; avoid deep reference chains. Give long references a short table of contents.

### 4. Write `SKILL.md`

Frontmatter and naming requirements:

- `name`: lowercase letters, numbers, and hyphens only; max 64 characters; no XML tags; avoid reserved runtime names such as `anthropic` or `claude`
- Prefer gerund names (`verb-ing-noun`, e.g. `managing-databases`) for new skills because they describe the capability; noun phrases and action-oriented names are acceptable when established or clearer
- Keep naming patterns consistent within a skill collection; avoid vague names such as `helper`, `utils`, or `tools`
- `description`: non-empty; max 1024 characters; no XML tags

For Pi skills, use `SKILL.md` as the canonical file name even when imported references mention `skill.md`.

The description should say what the skill does and when to use it, using concrete trigger terms without becoming a catalog of every example.

In the body:

- assume the agent is capable; include only reusable task-specific guidance
- state required order for fragile or destructive work
- put large or conditional detail in references
- state whether scripts should be executed or read as reference
- isolate runtime-specific instructions under clear adapter labels

### 5. Keep the core portable

Default to agent-agnostic guidance. If the user targets Claude, Codex, Cursor, Pi, or another runtime, add adapter notes without making them the universal workflow.

Read `references/agent_adapters.md` when adding runtime-specific adapters or deciding portability trade-offs.

### 6. Validate after meaningful edits

Run:

```bash
python3 /home/wasti/.pi/agent/skills/skill-creator/scripts/quick_validate.py <path/to/skill-folder>
```

This checks structure and frontmatter; it does not prove the skill is useful. For important skills, also test realistic tasks and compare behavior before/after the skill.

## Quality bar

A good skill has precise trigger metadata, a compact operational body, progressive disclosure for detail, explicit safety checks when risk is high, scripts for repeated deterministic work, adapter separation, and structural validation.

Avoid giant `SKILL.md` files, duplicate guidance, vague “be careful” rules, runtime assumptions in the core, optional tooling presented as mandatory, and extra README/CHANGELOG/process diary files unless explicitly needed.

## Layer boundary

Use the right layer: skills for reusable workflow and safety rules; `scripts/` for deterministic local helpers; MCP/tools for remote services or authenticated actions; AGENTS.md for stable policy visible before skills trigger. A skill may explain when to use a tool, but the tool should provide the capability.

## Self-improvement loop

For substantial changes, identify real failures, choose realistic scenarios, compare behavior with/without the skill when practical, adjust the smallest failing part, and validate again. Prefer deterministic checks first; use LLM-as-judge only for softer qualities.

## Bundled resources

Read extra resources only when the task needs them. Do not load the large best-practice references for routine skill creation or light edits. For `skill-creator` self-edits, the first two references are mandatory:

- `references/anthropic_skill_best_practices.md`: structure, descriptions, progressive disclosure, scripts, evaluation loops
- `references/progressive_skill_best_practices_supabase_workshop.md`: Skill vs MCP/CLI boundaries, production/security-sensitive skills, progressive context strategy, eval-driven improvement; translate examples to Pi conventions
- `references/agent_adapters.md`: adapter policy and portability trade-offs
- `references/schemas.md`: JSON shapes used by bundled evaluation tools
- `scripts/quick_validate.py`: neutral structural validator; execute it after meaningful edits
- other `scripts/`, `agents/`, and `eval-viewer/`: optional or legacy adapter/evaluation tooling; use only for explicit adapter or evaluation work

## Editing rules

When changing an existing skill:

- preserve the user's actual intent
- remove dead complexity before adding sections
- keep diffs reviewable
- prefer moving detail to references over expanding `SKILL.md`
- stop and ask if adapter behavior, legacy eval tooling, or source-of-truth location is ambiguous

When creating a new skill, start with the smallest viable folder and validate before adding optimization machinery.
