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

## Before any Codex worker or research call: size it

An agent resends its whole history on every step, so a broad call costs history × steps: on
01.11.2026 a few broad calls (build + fetch + model run + measurement for three firms in one; a
2 MB file rewritten again and again) reached ~290M input tokens in a day (Sebastian: „hast du eine
ahnung was du da redest?“). Before starting: cut the call to one firm and one step; tell the
worker the job only (`codex_call.py` appends a fixed context-discipline block to every prompt: search first with rg/find/wc, read excerpts, small outputs, narrow tests, no kb, skills or Brain unless the job names them); state the
expected cost to the user; run a series of model calls (one per document) on three items first
and extrapolate. After the call: report the `usage:` line `codex_call.py` prints and the quota.

A `resume` carries the thread's whole earlier history into every new step: on 02.11.2026 a fix
resumed a finished worker thread (5.3M input) and needed 10.5M input for fewer steps than the
original. For a new job, even a follow-up, start a fresh `new` call with a short written handoff
(paths, commit, state, the findings to fix); resume only for a short question about the thread's
own work. `codex_call.py resume` refuses without `--allow-resume`.

Workers start clean: their own Codex home without global or repository `AGENTS.md`, all tools kept.
So the brief carries what the worker needs: goal, end point, the paths and known places (run `rg`
yourself for known names and pass the hits), and how to report. The prompt tail tells the worker
to wait for long commands in one long poll. The `steps:` line after each call shows requests,
context growth and empty waits; check it against the expected size.

## Unattended board adapter

Before dispatching unattended board work, use the [worker setup](references/unattended-workers.md):
record per-ticket input, request and time budgets; keep board coordination in the caller and send
the worker one bounded step. Prompt limits are instructions until an external guard is verified.

## Reviews go through one script

```bash
S=~/.agents/skills/using-harnesses/scripts
PY=python3                   # Windows: PY=python (python3 there may be the Microsoft Store placeholder)
D=$("$PY" "$S/review.py" <codex|claude> [--resume <id>] [--effort <level>] [--rules <file>] <brief-file> <artifact-file>...)
"$PY" "$S/review.py" wait "$D"     # exit 75: still running, call wait again
```

From cmd the same arguments follow `python "%USERPROFILE%\.agents\skills\using-harnesses\scripts\review.py"`
(PowerShell: `python "$HOME\.agents\skills\using-harnesses\scripts\review.py"`). It needs Python 3.9 or newer; 3.7 and
3.8 stop with exit 2, anything older fails to compile.

The start returns at once with the call directory; `wait` returns after at most 540 s. Never run a
review blocking in the foreground of a session. The script assembles the payload from
[review-prompt.md](references/review-prompt.md), refuses secrets and `.env` inputs, runs the
reviewer contained (both without tools; codex read-only in its own home `~/.codex-review`),
checks the closing marker, and resumes only sessions it started. Never hand-write `codex exec` or
`claude -p` for a review. `--rules <file>` replaces only the general review rules, for a reading
that is not a code review (for example checking a document for errors); role lock and data clause
stay fixed.

- Follow the active global review rules: unattended board runs review Codex work in a separate
  `codex` call and never call Claude/Opus. Outside that exception, the reviewer's vendor must differ
  from the author's: Claude Code authors use `codex`, Codex authors use `claude`. If the required
  reviewer is unreachable, say so and stop.
- Both reviewers run without tools and see only the payload; pass diffs and command output as
  files.
- Submit scoped complete UTF-8 evidence: binary content and binary patches are refused before launch; see [input bounds](references/review.md#write-the-brief).

## Other calls

Questions, scouting and worker calls to Codex use `scripts/codex_call.py` ([codex.md](references/codex.md)).
Its callers outside this skill (market-digest, peer-debate) depend on its
CLI and output; keep both stable.

## Models

Review defaults: Codex `gpt-6.1-sol` (efforts `high,medium`, the first is the default), Claude `claude-opus-5-5` (`medium`);
per-user overrides in `${XDG_CONFIG_HOME:-~/.config}/using-harnesses/models.conf`
([models.conf.example](references/models.conf.example)), shown by `"$PY" "$S/review.py" --print-config`.
`gpt-6-sol` is refused everywhere; `gpt-6-astra` is never a default and runs only when the user names it
for that call (`codex_call.py --model gpt-6-astra --on-request`).

Quote an answer unchanged; the calling session verifies every finding.
