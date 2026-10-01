---
name: tool-update-checker
description: Check whether locally installed tools, pi packages/extensions, npm globals, Git repositories, and GitHub-hosted tools have upstream updates available. Use this skill when the user asks to check for updates, newer versions, releases, tags, or remote changes for tools such as pi-coding-agent, pi packages, GitHub-based extensions, Hermes, OpenClaw, or similar local utilities.
---

# Tool Update Checker

Use this skill to perform fast, read-only update checks for operator-selected tools.

## Default approach

1. Read the config file at `~/.config/tool-update-checker/tools.toml` unless the user names another config.
2. Run the checker script:

```bash
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py
```

Useful flags:

```bash
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py --format json
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py --group pi
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py --actionable-only
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py --actionable-only --exit-code
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py --actionable-only --notify
python3 ~/.agents/skills/tool-update-checker/scripts/check_updates.py --config /path/to/tools.toml
```

3. Summarize only the actionable results:
   - up to date
   - update available
   - remote changed
   - local-changed
   - missing / error
   - info entries that need `current` to compare
4. For scheduled checks, prefer `--actionable-only --exit-code` so cron/systemd can report only when attention is needed.
5. Use `--notify` only for local desktop notifications via `notify-send`; no scheduler or remote notification is configured by this skill.
6. Stay read-only unless the user explicitly asks to perform updates.

## Supported tool kinds

Kinds: `npm-global`, `git-repo`, `github-release`, `skill-local`, `skill-git`, `skills-root-git`, `skills-sh`.
Read [references/tool-kinds.md](references/tool-kinds.md) for required and optional fields only when adding or changing a config entry.

## Pi-specific guidance

- For pi packages installed via `pi install`, inspect `~/.pi/agent/settings.json` first.
- Use `npm-global` for an npm-based pi package only after confirming a global install (`npm -g ls <package> --depth=0`). `pi install npm:<package>` installs into `~/.pi/agent/npm/`, which `npm-global` does not read; a Pi-local package needs a checker for that install prefix, otherwise it is reported `missing` or compared against an unrelated global copy.
- Skills are not auto-discovered today; add explicit `skill-git`, `skills-root-git`, or `skills-sh` entries for every managed skill source.
- Auto-discovered local extensions in `~/.pi/agent/extensions/` only become update-checkable when you know their package name or upstream repository.

## Editing policy

- Prefer updating the operator config in `~/.config/tool-update-checker/tools.toml` over editing the script.
- Keep the script dependency-free beyond Python standard library, `git`, and `npm`.
- Do not add auto-update behavior unless the user explicitly asks for a separate update workflow.
