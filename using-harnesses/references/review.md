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
Fill in [prompt-scaffold.md](prompt-scaffold.md): what the work must establish, its intended use
and reach (the reviewer reports only what that use realistically reaches), the design in your
own words (including what exists only in the conversation), the operating context, a named attack
list, and the one change the reviewer would make first. A finding outside what the work must
establish is the weakest kind.

Give the reviewer the task, the evidence and the intended use, never your own verdict or the
answer you expect: a model told who wrote a text judges it more kindly (Sharma et al. 2023,
arXiv:2310.13548), and a reviewer handed your hypothesis tends to return it confirmed (adopted
2026-11-10).

Neither reviewer can run `git diff` or read a path you name; write diffs and command output to
files (`git diff --cached > "$W/review.diff"`) and pass them as artifacts.

Before any model starts, the script refuses non-UTF-8 content, NUL bytes and embedded Git binary patch
blocks (`GIT binary patch` followed by `literal N` or `delta N`, including ANSI SGR colour and CRLF).
Literal markers in prose or code fences are accepted. ESC, FF, BS and CR are allowed unchanged;
NUL and encoding errors report the byte value and zero-based offset. UTF-8 text,
ordinary code diffs and `Binary files ... differ` summaries remain valid. Use a textual diff without
`--binary`, and describe binary fixtures through their purpose, interfaces and relevant test outcomes.

There is no size bound: send the evidence the review needs, not run bookkeeping or bulk data the reviewer cannot use. Invalid installed prompt content exits 2, not 3.

## Frame the question

Measured once, on 10.11.2026: 16 planted defects of 9 kinds in two stored Market Digest analyses,
correct but suspicious sentences beside them, one reviewer model (gpt-6.1-sol high), scored without
knowing which brief produced a report, plus a check on three real first drafts
([Brain method](/home/wasti/.agents/brain/methods/review-question-over-repetition.md)). These are
observations from that test, not general laws; weigh them, do not apply them blindly.

1. Naming observed defect kinds in the brief (kinds, not instances) and closing with "does every
   sentence still fit the verdict and the numbers?" found more planted defects (12.3 against 10 of
   16 per review) and more real ones in the first drafts (15 against 13 of 17, plus 4 further
   errors). It also produced about one false or unresolvable finding per text where the plain error
   search produced almost none, and twice the output. Use it where missed defects cost more than
   checking extra findings.
2. Repeating a brief helps only if its results vary: the plain error search found the same 10
   defects in all three runs; the framed brief found 12, 13 and 12, together 14.
3. Splitting one review into viewpoints that each get all the evidence did not beat one framed
   review at the same number of calls: three calls found 12 planted defects against 14, with fewer
   false or unresolvable findings (12 against 28, not deduplicated) and some real errors no other
   brief named. A numbers-only pass found as many
   planted defects as the plain search and nothing else.
4. A second call asked to refute the findings removed true findings along with false ones; verify
   findings yourself against the source instead.
5. To choose between briefs, measure them like this: plant real defect kinds that only the evidence
   reveals (a planted sentence that contradicts another sentence is always found), add correct but
   suspicious sentences, repeat each brief, score blind. One review call cost under 1 % of the
   weekly Codex quota.

## Run one round

```bash
S=~/.agents/skills/using-harnesses/scripts
PY=python3   # Windows: PY=python (see codex.md "Windows")
D=$("$PY" "$S/review.py" codex  [--resume <id>] [--effort <level>] "$W/brief.md" <artifact>...)
D=$("$PY" "$S/review.py" claude [--resume <id>] [--effort <level>] "$W/brief.md" <artifact>...)
"$PY" "$S/review.py" wait "$D" [--timeout <s≤540>]
```

The start runs every check, prints the call directory and returns at once; the reviewer runs
detached. Keep the session responsive and call `wait` later; exit 75 means still running, so call it
again. Budget 5–20 minutes per round. `wait` prints `session: <id>`, a blank line and the answer.
`"$PY" "$S/review.py" cancel "$D"` stops a round. `--foreground` blocks until the round ends; use it only in
scripts that run in the background anyway. The call directory holds `out.md` (the answer),
`session` (the id for `--resume`), `err.txt`, `why`, `payload.md`, `rc` and the raw log; remove it
and `$W` once you have the session id. The model is fixed per backend; `--effort` takes only the
levels configured for it (`"$PY" "$S/review.py" --print-config`). `--rules <file>` replaces the
general review rules of [review-prompt.md](review-prompt.md) with the caller's own (a non-empty
file), for a fixed reading task whose output format the code-review rules would contradict, such as
a capped number of findings; role lock and data clause stay as they are.

| Exit | Meaning | Action |
|---|---|---|
| 0 | the answer ends with `===REVIEW COMPLETE===` | read it |
| 2 | usage, config, unclean reviewer home, cwd inside git, resume of a session review.py did not start | fix the cause; never bypass the script |
| 3 | payload refused: secret, `.env` or binary content/patch | remove secrets; send binary evidence as a textual description as above |
| 4 | no answer, no session id, a runner that died, or a status 0 without answer, session and log | read `err.txt` |
| 5 | closing line missing: truncated, refused or hijacked | failed round; do not report partial findings |
| 75 | `wait` only: the round still runs | call `wait` again |
| 124, 137 | deadline (30 min; 137 = killed after ignoring TERM) | report a timeout |
| 143 | cancelled | start again if still needed |

## Treat findings as claims

Exit 0 is a screen, not an acceptance. Read the answer: a question, a consent request, a plan or a
status note is a failed round, not "no findings". Verify every finding against the source before
acting. Fix the confirmed ones; reject the others with the reason. Reject also a technically
correct finding whose scenario the intended use does not realistically produce, with the reason "not
reached in this use"; the global rule to fix what you notice does not cover such findings. Severity is the reviewer's; lower
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

After verifying a round's findings, append one line to the outcome log, so the value of each round
can be counted later:

```bash
round=1 reach=internal reported=0 confirmed=0 irrelevant=0 adopted=0 why=""   # this round's verified values
printf '{"at":"%s","dir":"%s","round":%d,"reach":"%s","reported":%d,"confirmed":%d,"irrelevant":%d,"adopted":%d,"why":"%s"}\n' \
  "$(date -Is)" "$D" "$round" "$reach" "$reported" "$confirmed" "$irrelevant" "$adopted" "$why" >> ~/.agents/state/review-outcomes.jsonl
```

`reach` is `product` or `internal`; `reported` counts the reviewer's findings, `confirmed` those that
are true, `irrelevant` the true ones rejected as not reached in this use, `adopted` those
changed. `why` lists a short slug per rejected finding, comma-separated and without quotes
(`edge-case,style,speculation,wrong`), so recurring low-value kinds can be banned from the review
rules. The noise share of a round is `(reported - confirmed + irrelevant) / reported`: wrong and
unreached findings together. Entries before 2026-11-03 lack `reported`, `irrelevant` and `why`. What the counts teach is
collected in the [Brain method](/home/wasti/.agents/brain/methods/efficient-reviews.md).

Report how many rounds ran, what was fixed, what was rejected and why, what is open, and which
version the last review saw. If the other vendor is unreachable, say so.

## When rounds keep finding the same kind of defect

When two rounds in a row confirm new findings of the same kind (another spelling that slips through,
another false alarm from the last fix), the approach is the defect, not the next instance. Stop
fixing instances and change the angle instead of the reviewer. On 09.11.2026 three rounds on a
formula guard each found new bypasses; three different models then asked "why does this not
converge?" all named the same cause (Sebastian: „wie erklärst du dir diese riesige menge an
fehlern?!“).

1. Ask for the root cause, not for defects: why do the fixes not converge?
2. Separate what real runs showed from what the reviewer constructed; a constructed attack blocks
   only if a real use can reach it.
3. Give independent reviewers different contexts or viewpoints on the same problem, for example
   the code alone, the run history alone, or the product goal; anchor none of them on your own
   conclusion.
4. Check the proposed approach against the observed defects before building it (did it prevent
   them, which real calls would it block?).

Evidence and sources: Brain `methods/root-cause-over-instances.md`.

## Failure modes

| Symptom | Cause | Action |
|---|---|---|
| minutes of silence, process alive | normal: a reasoning model, buffered output | wait for the deadline |
| codex quotes `AGENTS.md` or house rules | the reviewer home or cwd is not the script's | use the script; never call `codex exec` by hand for a review |
| codex cites a file not in the payload | it ran with tools: not the script, or a disabled feature was renamed | use the script; check `codex features list` |
| `--resume` exits 2 | not a session review.py started on this backend, or deleted | start a new session with the full payload |
| claude auth error | `--bare` used instead of `--safe-mode` | use the script |
| no reviewer login | `~/.codex-review` not set up | see [codex.md](codex.md) "The reviewer home" |
