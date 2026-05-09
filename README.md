# ai-skills

Reusable AI/agent skills collected for installation into coding-agent runtimes.

This repository is the source/archive for portable skills. It is separate from:

- `sebastianlang84/pi-ext-*`: Pi extensions and packages.
- `sebastianlang84/pi-config`: private Pi runtime configuration for one machine/user.
- `~/.pi/agent/skills`: the active local Pi runtime skill directory.

## Layout

```text
skills/<skill-name>/
  SKILL.md        # required entry point
  assets/         # optional templates/resources
  references/     # optional deeper guidance
  scripts/        # optional deterministic helpers
```

Treat each `skills/<skill-name>/` directory as the portable artifact. Install or copy selected skills into the target agent's runtime-specific skill directory. On this machine, the canonical global Pi skill store is:

```text
~/.pi/agent/skills/
```

Example Pi install/update:

```bash
cp -a skills/manage-agent-context ~/.pi/agent/skills/
```

Validate a skill after edits:

```bash
python3 ~/.pi/agent/skills/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

## Current skills

This list should match the immediate subdirectories under `skills/`.

- `audit-manager`
- `browser-use`
- `claude-api`
- `dispatching-parallel-agents`
- `doc-coauthoring`
- `documentation-writer`
- `executing-plans`
- `git-workflow`
- `macrolens`
- `manage-agent-context`
- `mcp-builder`
- `newsletter-delivery`
- `pdf`
- `pi-extension-packaging`
- `secrets-env`
- `skill-creator`
- `skill-manager`
- `subagent-driven-development`
- `subagent-workflow`
- `systematic-debugging`
- `test-driven-development`
- `tool-update-checker`
- `verification-before-completion`
- `webapp-testing`
- `write-docker-compose`
- `write-dockerfile`
- `writing-plans`

## Scope notes

This repo may contain skills that are useful as source material but are not installed globally by default. Domain-specific workflow skills should live with their consuming project when they are not generally reusable.
