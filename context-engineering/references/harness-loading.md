# How harnesses load context

Verified 2026-10-05 against the vendor docs (Codex CLI 0.160, Claude Code 2.1.2xx); compaction,
scoped rules, hooks, memory, subagents and inspection added 2026-10-24 (Claude Code 2.1.3xx). Harness
behaviour changes often: check the sources before relying on a detail, and update this file with
the date.

## Instruction files

**Codex** ([docs](https://developers.openai.com/codex/guides/agents-md))

- Global: one file from the Codex home (`~/.codex`, or `$CODEX_HOME` if set):
  `AGENTS.override.md` if present and non-empty, else `AGENTS.md`. An override silently hides the
  normal file.
- Project: from the repo root down to the working directory, at most one file per directory
  (`AGENTS.override.md`, then `AGENTS.md`, then `project_doc_fallback_filenames`), joined root
  first, so closer files win by coming later. Without a project root (usually the git root) Codex
  checks only the working directory, so an `AGENTS.md` in a non-git parent folder does not apply.
- The chain is built once when Codex starts: an edited file reaches only new sessions.
- No imports. Empty files are skipped; files stop being added once the total reaches
  `project_doc_max_bytes` (32 KiB by default), so oversized instructions are cut silently.

**Claude Code** ([docs](https://code.claude.com/docs/en/memory))

- User level: `~/.claude/CLAUDE.md`. Project level: `CLAUDE.md`, `.claude/CLAUDE.md`,
  `CLAUDE.local.md` in the working directory and above.
- Since v2.1.277 Claude also reads a project's `AGENTS.md` (and `.claude/AGENTS.md`), but by
  default only when no project `CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or
  above. Adding a `CLAUDE.local.md` therefore silently stops `AGENTS.md` from loading. The
  **Project instructions** setting (`/config`, or `pluginConfigs."cc-plugin-agents-md@builtin"` in
  user settings; before v2.1.285 the ID was `agents-md@builtin`) can load both. Claude never reads `AGENTS.override.md`, `AGENTS.local.md`, or a
  user-level `AGENTS.md`.
- `@path` imports pull other files in, up to four levels deep. A relative path resolves from the
  importing file, not the working directory: `.claude/CLAUDE.md` needs `@../AGENTS.md`. A project
  import that points outside the working directory needs a one-time approval; if it is declined,
  the import stays off without further prompts. Imports in user-level files load without approval.
  An `AGENTS.md` that Claude reads natively never asks: its external imports load only if they
  were already approved for the project, otherwise they stay off silently.
- Scoped instructions: `.claude/rules/*.md` without `paths:` load every session like `CLAUDE.md`;
  with `paths:` they load when Claude reads or edits a matching file. Nested `CLAUDE.md` files in
  subdirectories load the same way.
- Inspect what loaded with `/context`; the `InstructionsLoaded` hook logs which files loaded and why.

**After compaction** ([context window](https://code.claude.com/docs/en/context-window),
[Codex hooks](https://learn.chatgpt.com/docs/hooks))

- Claude re-injects the system prompt, project-root `CLAUDE.md`, unscoped rules, auto memory and the
  skill listing. Path-scoped rules and nested `CLAUDE.md` are summarized away and reload only when
  a matching file is touched again. Invoked skill bodies come back cut to their first 5,000 tokens,
  25,000 in total, oldest dropped first. Instructions given only in the conversation may be lost;
  `/compact <focus>` steers what the summary keeps.
- Codex: whether `AGENTS.md` is re-read after compaction is not documented. `compact_prompt` in
  `config.toml` replaces the compaction prompt.
- Both harnesses run `SessionStart` hooks with the `compact` source after compaction and add their
  output to the context: the deterministic way to restore a constraint that must survive.

**Sharing one file across harnesses**

- Claude: an `@` import of the canonical file (`CLAUDE.md` containing only `@AGENTS.md` in a
  project, or the absolute path in `~/.claude/CLAUDE.md`). A project that has no `CLAUDE.md` gets
  `AGENTS.md` natively on current versions; the import also works on older ones.
- Codex has no imports: a symlink connects a file outside the Codex home or repo. Edit only through
  the real path; some edit tools replace a link with a plain file, and the harness then reads a
  stale copy. Inside a repo on Windows, Git checks a symlink out as a one-line text file when
  `core.symlinks` is false, and creating real links needs Developer Mode or the symlink privilege;
  inspect the checkout, and prefer the import for Claude there.
- Codex logs the instruction chain it built: start it with `-c log_dir=<dir>` and read
  `codex-tui.log`.
- Broken connections fail silently. A session-start check should test what each harness actually
  loads, not only that the files exist: the canonical file is non-empty, the import line and the
  link target are correct, no non-empty `AGENTS.override.md` hides it, and `CODEX_HOME` points
  where you expect. Confirm once in a fresh session of each harness that the content arrived
  without file access: ask about a distinctive rule in the file without quoting it, and tell the
  agent not to read any file. An agent that reads the file to answer proves access, not loading.

## Skills

- Both harnesses put only each visible skill's name and description into the session; `SKILL.md`
  loads when the skill is used, and references and scripts only when the body points to them.
- Codex scans `.agents/skills` from the working directory up to the repo root, `~/.agents/skills`,
  `/etc/codex/skills`, and its built-in skills. Its list is capped at about 2 % of the context
  window (8,000 characters when the window is unknown); with too many skills it shortens
  descriptions first, then leaves skills out with a warning
  ([docs](https://learn.chatgpt.com/docs/build-skills)).
- Claude Code reads `~/.claude/skills/`, the project's `.claude/skills/`, nested and `--add-dir`
  directories, plugins, and skills synced from claude.ai (written to `~/.claude/skills/synced/`);
  link shared skills into `~/.claude/skills/` per skill (`ln -s`, on Windows `mklink /D`), never
  the whole directory, or that sync lands in the shared store and Codex lists it. Each description (with `when_to_use`) is cut at
  `skillListingMaxDescChars` (1,536 by default), and the whole listing is capped by
  `skillListingBudgetFraction` (0.01 of the context window by default); on overflow, names stay
  and descriptions are dropped. `disable-model-invocation: true` removes the description from the
  context entirely; the skill then runs only when the user invokes it
  ([docs](https://code.claude.com/docs/en/skills)).
- Every visible skill costs listing space in every session. Merge a skill whose job is a sub-case
  of another into that skill's `references/`, and keep machine-specific skills off machines that
  never need them.

## Hooks

- Claude Code: hooks in `settings.json`; a `PreToolUse` hook or a permission deny rule blocks an
  action whatever the instructions say ([docs](https://code.claude.com/docs/en/hooks-guide)).
- Codex: hooks in `~/.codex/hooks.json` or `[hooks]` in `config.toml`; project hooks only when
  `.codex/` is trusted, and each new or changed non-managed hook runs only after it is reviewed and
  trusted in `/hooks`. Check that a hook actually fires before calling a rule enforced. `PreToolUse` denies with `permissionDecision: "deny"` or exit code 2. It
  does not cover hosted tools such as web search, nor input sent to an already running shell
  (`write_stdin`) ([docs](https://learn.chatgpt.com/docs/hooks)).

## Memory

- Claude Code auto memory is on by default, per repository: the first 200 lines or 25 KB of its
  `MEMORY.md` load every session and come back after compaction; non-fork subagents do not get
  the parent's auto memory but can have their own (`memory` frontmatter)
  ([docs](https://code.claude.com/docs/en/memory#auto-memory)).
- Codex memories are off by default (`[features] memories = true`), live under `~/.codex/memories/`
  as generated state, and are not meant for hand-editing or for rules
  ([docs](https://learn.chatgpt.com/docs/customization/memories)).
- Both are harness layers beside any curated knowledge base: audit them for stale or normative
  entries rather than treating them as a second system of record.

## Subagents

- Claude Code non-fork subagents load the `CLAUDE.md` hierarchy (and `AGENTS.md` read as project
  instructions), except the built-in Explore and Plan and custom agents with `omitClaudeMd: true`;
  nested `CLAUDE.md` and path-scoped rules still load when they touch matching files. The parent's
  auto memory does not reach them; a fork inherits the whole parent context; skills load in full only when listed in `skills:`
  ([docs](https://code.claude.com/docs/en/sub-agents)).
- Codex subagents inherit skills, model, permissions and MCP servers; whether `AGENTS.md` is
  passed is not documented.
