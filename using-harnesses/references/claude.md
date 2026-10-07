# Calling claude

For a review, use `scripts/review.sh claude …` ([review.md](review.md)); it fixes every flag below.

## Flags review.sh passes

| Flag | Why |
|---|---|
| `-p --output-format json` | non-interactive; the JSON result carries `result` and `session_id` |
| `--safe-mode` | no CLAUDE.md, skills, plugins, hooks or MCP servers; login and model selection keep working |
| `--setting-sources project` | no user settings (language and output style measured to leak without it); the neutral cwd has no project settings, so none load |
| `--tools ""` | no built-in tools: the reviewer sees the payload and nothing else |
| `--model`, `--effort` | the configured model and an allowed effort |
| `--resume <id>` | continue a session; the restrictions above apply again |

Never use `--bare`: it authenticates only with `ANTHROPIC_API_KEY` and fails for a logged-in user.
Do not pass `--no-session-persistence` to a review: the first round must stay resumable.

## Where review sessions live

Every review call runs in one fixed working directory, `~/.cache/using-harnesses/claude-review`
(created on demand, refused inside a git repository), so Claude Code stores the sessions in that
directory's project folder under `~/.claude/projects/` (the path with every non-alphanumeric
character replaced by `-`, ending in `-using-harnesses-claude-review`). `review.sh` unsets
`CLAUDE_CONFIG_DIR` and the XDG and session variables that would move that store.

`--resume` is accepted only when `<project folder>/<id>.jsonl` exists and its first user message
opens with the role lock. An ordinary session started in that directory by hand, for example while
troubleshooting, has no role lock and is refused. A caller who deliberately fakes one is out of scope:
it could call `claude -p` directly anyway.

## Direct calls

Claude cannot run commands or read files with `--tools ""`. Write diffs, logs and command output into
files and pass them as artifacts. A question to Claude from Codex goes through `review.sh claude` as
well: state the question and the answer format in the brief; the fixed review rules follow it.

## Windows (Git Bash)

Run from Git Bash; see [codex.md](codex.md) for `setsid`. Over ssh to beelink, use a login shell
(`bash -lc`) and check that Claude Code is logged in there. The project-folder name is derived from the Windows path there; `review.sh`
matches only its `-using-harnesses-claude-review` ending, so the drive prefix does not matter.
