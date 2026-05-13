# ai-skills

Reusable AI/agent skills. This repository is laid out as the active Pi global skill store.

On this machine, the canonical checkout/runtime path is:

```text
~/.pi/agent/skills
```

Do not keep a second global skill store. Repo-local skills, when needed, belong under a consuming repo's `.agents/skills/` directory.

## Layout

```text
<skill-name>/
  SKILL.md        # required entry point
  assets/         # optional templates/resources
  references/     # optional deeper guidance
  scripts/        # optional deterministic helpers
```

Treat each `<skill-name>/` directory as the portable artifact. Pi discovers global skills directly from this repo root when it is checked out at `~/.pi/agent/skills`.

Validate a skill after edits:

```bash
python3 ~/.pi/agent/skills/skill-creator/scripts/quick_validate.py <skill-name>
```

## Current skills

This list should match the immediate subdirectories in the repo root.

- `audit-manager`
- `claude-api`
- `doc-coauthoring`
- `git-workflow`
- `grill-me`
- `grill-with-docs`
- `improve-codebase-architecture`
- `managing-agent-context`
- `mcp-builder`
- `newsletter-delivery`
- `pdf`
- `pi-extension-packaging`
- `secrets-env`
- `skill-creator`
- `subagent-workflow`
- `tdd`
- `tool-update-checker`
- `to-prd`
- `write-docker-compose`
- `write-dockerfile`

## Scope notes

Global skills should be broadly reusable across repos. Project-specific workflows should live with their consuming project under `.agents/skills/`.
