---
name: using-codex
description: Call Codex (gpt-6.1-sol) from another agent - for an adversarial review, a question, a scouting search, or a follow-up in an existing Codex thread. Use for every Codex call instead of writing `codex exec` by hand.
---

# Using Codex

`S=~/.agents/skills/using-codex/scripts/codex_call.py` pins model `gpt-6.1-sol`, effort `medium`,
read-only sandbox, hooks off, thread kept. Prompts go in as a file or `-` for stdin. On Windows,
run it with `python` from Git Bash; over ssh to beelink, use a login shell (`bash -lc`) so `codex`
is on the `PATH`.

- Start: `python3 $S new --cwd <dir> --label <name> --detach <prompt-file>` prints a call dir.
- Collect: `python3 $S wait <call-dir>` prints `thread:`, `result:` and the answer. Exit 3 means
  still running, so call `wait` again. Exit 1 is a failure with its reason.
- Follow up in the same thread: `python3 $S resume <thread-id> --detach <prompt-file>`, then `wait`.
- Without `--detach` a call blocks and prints the same output. Only do that for calls under 10 min.
- Stop a detached call with `python3 $S cancel <call-dir>`; it kills the runner and codex and
  records the call as cancelled.
- `--search` gives Codex its native web search; `--sandbox workspace-write|danger-full-access`
  widens the default read-only sandbox for callers that must write (peer-debate sides).
- `--model`, `--effort`, `--sandbox` or `CODEX_CALL_MODEL` / `CODEX_CALL_EFFORT` override the pins.
  `list` shows recent calls from `~/.agents/state/codex-call/calls.jsonl`.

Call it directly from the main session; no wrapper subagent. Quote the answer unchanged; the
calling session still evaluates it.

## Review

A Claude session that has its own work reviewed (the rule for when and how many rounds is in the
global `AGENTS.md`) follows [`references/review.md`](references/review.md) and launches Codex with
the command below. A Codex session never reviews itself: it uses `using-claude` instead.

```bash
~/.agents/skills/using-codex/scripts/launch-review.sh <prompt-file> <output-file> [cwd]
```

It appends [`references/review-rules.md`](references/review-rules.md), blocks by design (run it in
the background), writes the answer to `<output-file>`, the thread id to `<output-stem>.thread` for a
follow-up with `resume`, and errors to `<output-stem>.err`. `REVIEW_MODEL` and
`REVIEW_REASONING_EFFORT` override the defaults.

## Scouting

For cheap "where is this" searches pass `--model gpt-6-luna --effort low` and append
[`references/scout-rules.md`](references/scout-rules.md). Pass the same two flags to every `resume`
of a scout thread, or the follow-up silently runs on the sol/medium defaults.

## Maintenance

After a Codex update, or when a call fails in a way that looks like the CLI changed, run
`python3 $S selftest`. It checks new, an immediate resume and the sandbox against the live CLI and
records the verified version in `~/.agents/state/codex-call/selftest.json`.

`~/.agents/skills/codex-call/scripts/codex_call.py` is a link to this script for callers that still
use the old path (market-digest's quality loop); remove it once nothing uses that path.
