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
python3 ~/.pi/agent/skills/tool-update-checker/scripts/check_updates.py
```

Useful flags:

```bash
python3 ~/.pi/agent/skills/tool-update-checker/scripts/check_updates.py --format json
python3 ~/.pi/agent/skills/tool-update-checker/scripts/check_updates.py --group pi
python3 ~/.pi/agent/skills/tool-update-checker/scripts/check_updates.py --config /path/to/tools.toml
```

3. Summarize only the actionable results:
   - up to date
   - update available
   - remote changed
   - missing / error
4. Stay read-only unless the user explicitly asks to perform updates.

## Supported tool kinds

### `npm-global`
Checks a globally installed npm package against the npm registry.

Required fields:
- `name`
- `kind = "npm-global"`
- `package`

Good for:
- `@mariozechner/pi-coding-agent`
- pi packages installed globally from npm

### `git-repo`
Checks a local Git repository against a remote branch head using `git ls-remote`.

Required fields:
- `name`
- `kind = "git-repo"`
- `path`

Optional fields:
- `remote` (default `origin`)
- `branch` (defaults to current branch)
- `groups = ["..."]`

Good for:
- local clones like `~/openclaw`
- local clones like `~/hermes`
- GitHub-based extensions you keep as local repos

### `github-release`
Checks the latest GitHub release, or falls back to the newest tag when no release exists.

Required fields:
- `name`
- `kind = "github-release"`
- `repo = "owner/name"`

Optional fields:
- `current` to compare a tracked installed version/tag
- `groups = ["..."]`

Good for:
- GitHub-hosted tools without a local clone
- extensions where you only want release visibility

## Pi-specific guidance

- For pi packages installed via `pi install`, inspect `~/.pi/agent/settings.json` first.
- npm-based pi packages can usually be tracked as `npm-global` entries.
- Auto-discovered local extensions in `~/.pi/agent/extensions/` only become update-checkable when you know their package name or upstream repository.

## Editing policy

- Prefer updating the operator config in `~/.config/tool-update-checker/tools.toml` over editing the script.
- Keep the script dependency-free beyond Python standard library, `git`, and `npm`.
- Do not add auto-update behavior unless the user explicitly asks for a separate update workflow.
