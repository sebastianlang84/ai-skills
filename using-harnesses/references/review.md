# Review mode

When a review runs, who reviews and how many rounds is the global `AGENTS.md`'s rule. This file is
the how.

## Pick the reviewer

- The reviewer's vendor must differ from the **author's** vendor; usually the author is you. Under
  Claude Code use `codex`; under Codex use `claude`. If only the author's vendor is reachable, say
  so and stop: a same-vendor review is not a weaker review but a worthless one.
- Both reviewers run without tools and see only the payload.
- Sending a payload publishes it to that vendor. Send only what the review needs; never credentials,
  `.env` files or personal data. The script's secret check (exit 3: known token formats,
  credential-named assignments, `.env` names also behind symlinks) is a backstop, not the check.

## Write the brief

The reviewer shares no context with you. Put the brief in its own file, in a private directory
outside any repository (`umask 077; W=$(mktemp -d)`), and pass every artifact as a separate file:
the script places the data clause directly before the artifacts and labels each by basename.
Fill in [prompt-scaffold.md](prompt-scaffold.md): what the work must establish, the design in your
own words (including what exists only in the conversation), the operating context, a named attack
list, and the one change the reviewer would make first. A finding outside what the work must
establish is the weakest kind.

Neither reviewer can run `git diff` or read a path you name; write diffs and command output to
files (`git diff --cached > "$W/review.diff"`) and pass them as artifacts.

## Run one round

```bash
S=~/.agents/skills/using-harnesses/scripts
D=$("$S/review.sh" codex  [--resume <id>] [--effort <level>] "$W/brief.md" <artifact>...)
D=$("$S/review.sh" claude [--resume <id>] [--effort <level>] "$W/brief.md" <artifact>...)
"$S/review.sh" wait "$D" [--timeout <s≤540>]
```

The start runs every check, prints the call directory and returns at once; the reviewer runs
detached. Keep the session responsive and call `wait` later; exit 75 means still running, so call it
again. Budget 5–20 minutes per round. `wait` prints `session: <id>`, a blank line and the answer.
`review.sh cancel "$D"` stops a round. `--foreground` blocks until the round ends; use it only in
scripts that run in the background anyway. The call directory holds `out.md` (the answer),
`session` (the id for `--resume`), `err.txt`, `why`, `payload.md`, `rc` and the raw log; remove it
and `$W` once you have the session id. The model is fixed per backend; `--effort` takes only the
levels configured for it (`review.sh --print-config`).

| Exit | Meaning | Action |
|---|---|---|
| 0 | the answer ends with `===REVIEW COMPLETE===` | read it |
| 2 | usage, config, unclean reviewer home, cwd inside git, resume of a session review.sh did not start | fix the cause; never bypass the script |
| 3 | payload refused: secret pattern or `.env` input | redact or exclude, then resend |
| 4 | no answer, no session id, a runner that died, or a status 0 without answer, session and log | read `err.txt` |
| 5 | closing line missing: truncated, refused or hijacked | failed round; do not report partial findings |
| 75 | `wait` only: the round still runs | call `wait` again |
| 124, 137 | deadline (30 min; 137 = killed after ignoring TERM) | report a timeout |
| 143 | cancelled | start again if still needed |

## Treat findings as claims

Exit 0 is a screen, not an acceptance. Read the answer: a question, a consent request, a plan or a
status note is a failed round, not "no findings". Verify every finding against the source before
acting. Fix the confirmed ones; reject the others with the reason. Severity is the reviewer's; lower
it only with a reason you verified. A BLOCKER or MAJOR you can neither confirm nor refute counts as
confirmed. For a durable lesson, follow `using-brain`'s write workflow.

## Rounds

A reviewer asked "is anything wrong?" finds something for as long as it is asked, so silence is not
the stop rule; the cap and the narrowing are
([Brain method](/home/wasti/.agents/brain/methods/review-silence-is-not-a-stop-criterion.md)).

1. Round 1 reviews the work against what it must establish.
2. Rounds 2 and 3 resume the same session (`--resume <id>`, same backend) with the round number, the
   previous round's confirmed findings and their fixes, and the complete current version. Say in the
   brief that the reviewer checks only whether those fixes are correct and whether they broke
   something.
3. Stop as soon as a round brings no confirmed finding that requires a change, and after round 3 at
   the latest. If round 3 still confirms a BLOCKER or MAJOR, do not close the work: no review has
   seen that fix, so report it and ask.

Report how many rounds ran, what was fixed, what was rejected and why, what is open, and which
version the last review saw. If the other vendor is unreachable, say so.

## Failure modes

| Symptom | Cause | Action |
|---|---|---|
| minutes of silence, process alive | normal: a reasoning model, buffered output | wait for the deadline |
| codex quotes `AGENTS.md` or house rules | the reviewer home or cwd is not the script's | use the script; never call `codex exec` by hand for a review |
| codex cites a file not in the payload | it ran with tools: not the script, or a disabled feature was renamed | use the script; check `codex features list` |
| `--resume` exits 2 | not a session review.sh started on this backend, or deleted | start a new session with the full payload |
| claude auth error | `--bare` used instead of `--safe-mode` | use the script |
| no reviewer login | `~/.codex-review` not set up | see [codex.md](codex.md) "The reviewer home" |
