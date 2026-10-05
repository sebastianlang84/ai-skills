---
name: using-claude
description: Call Claude Opus 5.5 headless from another agent (usually Codex) - for an adversarial review, a question, or a follow-up in an existing Claude session, read-only by default. Use for every Claude call instead of writing `claude -p` by hand.
---

# Using Claude

`C=~/.agents/skills/using-claude/scripts/claude-call.sh` runs `claude -p` with model
`claude-opus-5-5`, effort `medium`, and only the tools Read, Grep and Glob, no MCP servers. The
reviewer or helper can read the directories you pass and nothing else, and it cannot write.

```bash
$C [--review] [--resume <session-id>] <prompt-file> <output-file> <dir> [more dirs]
```

- The first `<dir>` is the working directory; every `<dir>` is readable.
- `--review` appends `using-codex`'s [`review-rules.md`](../using-codex/references/review-rules.md)
  to the prompt. For a review, follow [`review.md`](../using-codex/references/review.md) (prompt,
  findings, rounds); the rule for when to review is in the global `AGENTS.md`.
- It blocks while Claude works; run it in the background and collect the output file.
- The answer lands in `<output-file>`, the Claude session id in `<output-stem>.session`, errors in
  `<output-stem>.err`. Follow up in the same session with `--resume <id>`; the restrictions stay
  the same. An empty, cut-off or failed result exits non-zero and writes no output file.
- Claude can only read files: it cannot run `git diff` or any other command. Write diffs, logs
  and command output to files inside a passed directory and name them in the prompt.
- `CLAUDE_CALL_MODEL` and `CLAUDE_CALL_EFFORT` override the model and effort.
- Needs Python 3.9 or newer. On Windows the `python3` from the Microsoft Store alias is only a
  placeholder; install Python (for example `winget install Python.Python.3.14 --scope user`).
- On Windows, run it from Git Bash. Over ssh to beelink, use a login shell (`bash -lc`) so `claude`
  is on the `PATH`, and check that Claude Code is logged in there.

Quote the answer unchanged; the calling session still evaluates it. If Claude is unreachable or not
logged in, say so; never substitute a model from the same vendor for a review.
