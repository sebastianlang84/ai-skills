---
name: codex-call
description: Call Codex (gpt-6-sol) for a review, a question, or a follow-up in an existing Codex thread. Use for every Codex call instead of writing `codex exec` by hand.
---

# codex-call

`S=~/.agents/skills/codex-call/scripts/codex_call.py` pins model `gpt-6-sol`, effort `medium`,
read-only sandbox, hooks off, thread kept. Prompts go in as a file or `-` for stdin.

- Start: `python3 $S new --cwd <repo> --label <name> --detach <prompt-file>` prints a call dir.
- Collect: `python3 $S wait <call-dir>` prints `thread:`, `result:` and the answer. Exit 3 means
  still running, so call `wait` again. Exit 1 is a failure with its reason.
- Follow up in the same thread: `python3 $S resume <thread-id> --detach <prompt-file>`, then `wait`.
- Without `--detach` a call blocks and prints the same output. Only do that for calls under 10 min.

Call it directly from the main session; no wrapper subagent. For a review, append
`references/review-rules.md` to the prompt file. For scouting, pass `--model gpt-6-luna --effort low`
and append `references/scout-rules.md`; pass the same two flags to every `resume` of a scout thread,
or the follow-up silently runs on the sol/medium defaults. For long calls use `--detach` and run `wait` as a background
Bash command.

Quote the answer unchanged. The calling session still evaluates it: fix each finding or refute it
with evidence before reporting. `--model`, `--effort`, `--sandbox` or `CODEX_CALL_MODEL` /
`CODEX_CALL_EFFORT` override the pins. `list` shows recent calls from
`~/.agents/state/codex-call/calls.jsonl`.

After a Codex update, or when a call fails in a way that looks like the CLI changed, run
`python3 $S selftest`. It checks new, an immediate resume and the sandbox against the live CLI and
records the verified version in `~/.agents/state/codex-call/selftest.json`.
