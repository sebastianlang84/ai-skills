# Agent Adapters

`skill-creator` treats the skill folder itself as the primary artifact and any runtime-specific integration as an adapter.

## Default rule

Keep the canonical skill in:

- `~/.pi/agent/skills/<skill-name>/`
- `<repo>/.agents/skills/<skill-name>/`

Anything else is adapter glue.

## What counts as an adapter

Examples:

- symlinks into another tool's skill directory
- runtime-specific discovery hooks
- trigger-evaluation harnesses
- UI metadata used by only one agent
- wrapper config files

## Current state of this skill folder

This skill still ships some legacy Claude-oriented helper scripts:

- `scripts/run_eval.py`
- `scripts/run_loop.py`
- `scripts/improve_description.py`
- `scripts/generate_report.py`

These scripts are optional and runtime-specific. They should be used only when the target environment is Claude and the user wants trigger-eval or description-optimization behavior for that runtime.

## Authoring rule

When editing or creating a skill:

1. write the portable core first
2. validate the folder structure
3. add adapter-specific notes only if needed
4. keep adapter-specific behavior clearly labeled

## Design smell

It is a design smell if:

- the core `SKILL.md` assumes one runtime without saying so
- the default storage path is runtime-specific
- runtime-specific eval tooling is described as mandatory

If you see those patterns, move them out of the core workflow or label them as adapter-only behavior.
