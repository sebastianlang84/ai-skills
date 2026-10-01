# Claude Code Adapter

Claude-Code-specific behaviour for skills that target it. Adapter policy and canonical locations live in `agent_adapters.md`; this file only lists what Claude Code adds. Source: https://code.claude.com/docs/en/skills (checked 2026-10-02).

## Listing budget

- `description` and `when_to_use` are concatenated and truncated at **1,536 characters** in the skill listing (`skillListingMaxDescChars`). Put the key use case first; trailing triggers are the first to go.
- The whole listing gets about **1% of the model's context window** (`skillListingBudgetFraction`). On overflow, descriptions of the least-used skills are dropped first, so a long description costs other skills their discovery.

## Frontmatter: spec versus Claude Code

Spec fields, portable and accepted by claude.ai upload and the Skills API: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.

Claude-Code-only fields. Any of them makes claude.ai upload or API packaging fail with a hard error (`Unexpected key(s) in SKILL.md frontmatter`); other harnesses ignore them. `quick_validate.py` reports them as notes.

| Field | Effect |
|---|---|
| `when_to_use` | Extra trigger text appended to `description`; shares the 1,536-character cap |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]` |
| `arguments` | Named positional arguments for `$name` substitution |
| `disable-model-invocation` | `true`: only the user's `/name` starts the skill |
| `user-invocable` | `false`: hidden from the `/` menu, model-only |
| `disallowed-tools` | Removes tools while the skill is active |
| `model`, `effort` | Model or effort override for the invoking turn |
| `context: fork`, `agent`, `background` | Run in a forked subagent of type `agent`; `background: false` waits for its result in the same turn (default `true`) |
| `hooks` | Hooks registered while the skill is invoked |
| `paths` | Glob patterns that limit when the skill activates |
| `shell` | `bash` or `powershell` for `!` command blocks |

A skill meant for upload keeps to the spec fields; put Claude Code behaviour in a separate copy or adapter.

## Paths and dynamic context

- `${CLAUDE_SKILL_DIR}` is the directory holding `SKILL.md`. Use it for bundled scripts so the command works from any working directory: `python3 "${CLAUDE_SKILL_DIR}/scripts/check.py"`. It is substituted in the skill body and in Bash rules of `allowed-tools`, not by other harnesses, so the portable core names paths relative to the skill folder.
- Arguments: `$ARGUMENTS`, `$ARGUMENTS[N]` or `$N`, and `$name` for declared `arguments`.
- Dynamic context: a line `` !`git status --short` `` (or a fenced block opened with `` ```! ``) runs before Claude sees the skill and is replaced by its output, once, without rescanning. It runs on every invocation, so use only side-effect-free commands. It is off with `disableSkillShellExecution`, never runs in skills synced from claude.ai, and does nothing on claude.ai or the API.

## Compaction

After auto-compaction Claude Code re-attaches the most recent invocation of each skill, keeping only its **first 5,000 tokens**; all re-attached skills share **25,000 tokens**, filled from the most recently invoked, so older skills can drop out entirely. Put critical rules and stop conditions at the top of `SKILL.md`; text past the first 5,000 tokens can vanish mid-task.

## Rules that must hold every turn

A skill is prompt text: loaded once, compactable, and ignorable. A rule that must hold on every tool call — block a command, protect a path — belongs in a hook (`settings.json`, or the skill's `hooks` field while it is active). The skill may install or explain the hook; `git-guardrails` is the local example.
