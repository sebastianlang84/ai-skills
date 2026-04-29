---
name: skill-manager
description: Find, install, update, and remove locally available skills. Use this skill whenever the user mentions skills, SKILL.md files, skill availability, installing/removing/updating a skill, or asks about agent capabilities.
---

# Skill Manager

Use this skill to inspect and manage skills on this machine.

## Local skill layout on this system

Canonical locations:
- **Global:** `~/.pi/agent/skills/<skill-name>/`
- **Repo-local:** `<repo>/.agents/skills/<skill-name>/`

Do **not** use `~/.agents/skills/` as a second global store on this machine.

## Default workflow

1. Check which skills already exist:
   ```bash
   ls ~/.pi/agent/skills/
   ls .agents/skills/ 2>/dev/null
   ```
2. If the user asks whether a skill exists locally, answer from the filesystem first.
3. If the user asks for external availability, use `npx skills find <term>` or inspect `https://skills.sh/`.
4. If the user wants a new global skill, place it under `~/.pi/agent/skills/<skill-name>/`.
5. If a third-party installer writes to `~/.agents/skills/`, relocate the installed skill into `~/.pi/agent/skills/` and remove the duplicate store.

## Manual creation

```bash
mkdir -p ~/.pi/agent/skills/<skill-name>
# write SKILL.md there
```

## `npx skills` notes

Useful commands:
```bash
npx skills find [term]
npx skills list
npx skills check
npx skills update
```

Caution:
- some third-party skill tooling assumes `~/.agents/skills/`
- on this machine, global skills should end up in `~/.pi/agent/skills/`
- after such installs, relocate the skill if needed instead of keeping two global stores

## What to report back

Summarize clearly:
- which skills are installed globally
- which are repo-local
- what is missing
- what can be installed externally
- whether any relocation/cleanup is needed to keep the single global store rule intact
