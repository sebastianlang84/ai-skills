---
name: using-harnesses
description: Calls another agent harness headless — codex (gpt-6.1-sol, scouting on gpt-6-luna) or claude -p (Opus 5.5) — for a cross-vendor adversarial review, a question, a scouting search, a worker call or a follow-up in an existing thread. Use for every Codex or Claude call from another agent, for "let codex/opus look at this", gegenlesen lassen, a second opinion, before closing substantial self-authored work as the global AGENTS.md requires, and for whether a running review or call is done, failed or stuck. Never hand-write `codex exec` or `claude -p`. Not for interactive sessions, installing or logging in the CLIs, or two-model debates (peer-debate).
---

# Using harnesses

| Task | Read |
|---|---|
| Have work reviewed by the other vendor, or run a follow-up round | [review.md](references/review.md) |
| Codex: the reviewer home and its flags; questions, scouting, workers through `codex_call.py` | [codex.md](references/codex.md) |
| `claude -p`: safe mode, review sessions | [claude.md](references/claude.md) |

## Reviews go through one script

```bash
S=~/.agents/skills/using-harnesses/scripts
D=$("$S/review.sh" <codex|claude> [--resume <id>] [--effort <level>] <brief-file> <artifact-file>...)
"$S/review.sh" wait "$D"     # exit 75: still running, call wait again
```

The start returns at once with the call directory; `wait` returns after at most 540 s. Never run a
review blocking in the foreground of a session. The script assembles the payload from
[review-prompt.md](references/review-prompt.md), refuses secrets and `.env` inputs, runs the
reviewer contained (both without tools; codex read-only in its own home `~/.codex-review`),
checks the closing marker, and resumes only sessions it started. Never hand-write `codex exec` or
`claude -p` for a review.

- **The reviewer's vendor must differ from the author's.** Under Claude Code review with `codex`;
  under Codex review with `claude`. If only the author's vendor is reachable, say so and stop.
- Both reviewers run without tools and see only the payload; pass diffs and command output as
  files.

## Other calls

Questions, scouting and worker calls to Codex use `scripts/codex_call.py` ([codex.md](references/codex.md)).
Its callers outside this skill (market-digest, peer-debate, nightly-review-pipeline) depend on its
CLI and output; keep both stable.

## Models

Review defaults: Codex `gpt-6.1-sol` (efforts `medium,high`), Claude `claude-opus-5-5` (`medium`);
per-user overrides in `${XDG_CONFIG_HOME:-~/.config}/using-harnesses/models.conf`
([models.conf.example](references/models.conf.example)), shown by `scripts/review.sh --print-config`.
`gpt-6-sol` and `gpt-6-astra` are refused everywhere.

Quote an answer unchanged; the calling session verifies every finding.
