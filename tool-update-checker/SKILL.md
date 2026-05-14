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
   - local-changed
   - missing / error
   - info entries that need `current` to compare
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

### `skill-local`
Validates an installed local skill folder without checking a remote source.

Required fields:
- `name`
- `kind = "skill-local"`
- `path` to the skill folder, unless it is `~/.pi/agent/skills/<name>`

Optional fields:
- `skill` or `expected_name` when the display name differs from the frontmatter `name`
- `groups = ["..."]`

Checks:
- folder exists
- `SKILL.md` frontmatter exists
- frontmatter `name` matches the folder/expected skill name
- frontmatter `description` exists
- local uncommitted changes when the folder is inside a Git repo

### `skill-git`
Validates a local skill folder and compares its source Git repo with a remote branch.

Required fields:
- `name`
- `kind = "skill-git"`
- `path` to the installed skill folder

Optional fields:
- `repo_path` when the installed skill folder is not inside the source Git checkout
- `remote` (default `origin`)
- `branch` (defaults to current branch)
- `source_path` (defaults to the skill path relative to the repo root; set it when `repo_path` is separate)
- `skill` or `expected_name`
- `groups = ["..."]`

Notes:
- remote comparison is repo-level; `source_path` scopes local dirty checks and output labels, not remote diffing

Good for:
- the global ai-skills checkout
- personal GitHub-hosted skills installed from local clones

### `skills-sh`
Validates a local skill folder and checks the latest source commit advertised by skills.sh.

Required fields:
- `name`
- `kind = "skills-sh"`
- `path` to the installed skill folder
- `source = "owner/repo/skill-name"`, for example `mattpocock/skills/improve-codebase-architecture`

Optional fields:
- `repo_url` to skip scraping the skills.sh page for its GitHub source; prefer setting it when the page format is unstable
- `branch` to compare a named branch instead of remote `HEAD`
- `current` source commit SHA installed locally; without it the result is informational
- `skill` or `expected_name`
- `groups = ["..."]`

Good for:
- external skills.sh skills copied into the local skill store

## Pi-specific guidance

- For pi packages installed via `pi install`, inspect `~/.pi/agent/settings.json` first.
- npm-based pi packages can usually be tracked as `npm-global` entries.
- Auto-discovered local extensions in `~/.pi/agent/extensions/` only become update-checkable when you know their package name or upstream repository.

## Editing policy

- Prefer updating the operator config in `~/.config/tool-update-checker/tools.toml` over editing the script.
- Keep the script dependency-free beyond Python standard library, `git`, and `npm`.
- Do not add auto-update behavior unless the user explicitly asks for a separate update workflow.
