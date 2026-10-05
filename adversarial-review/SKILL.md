---
name: adversarial-review
description: Have the other vendor's model review your finished work adversarially (Claude → Codex gpt-6.1-sol, Codex → Opus 5.5), fix confirmed findings, repeat for at most three rounds. Default before reporting a plan, design, skill, configuration, script, or relied-on document as done. Not for trivial changes such as typos or a one-line fix.
---

# Adversarial review

The main session never reviews its own work. Before it reports a substantial result as done, the
other vendor's model attacks it, and the session fixes what holds up. A different vendor catches
blind spots; the same vendor mostly repeats the anchoring.

## When

The user's standing default (Sebastian, 2026-10-05): every substantial work product gets this
review without being asked. Substantial means a plan, design, new or changed skill,
configuration, script, or a document others will rely on. Skip it only for trivial changes (a
typo, a one-line fix with an obvious effect) and for plain answers in conversation. Scope and
impact decide; that a change is easy to undo does not exempt it, because a skipped review fails
silently. Point the review at the decision or artefact that
matters, with the smallest evidence set that settles it, not at the whole workstream.

## Who reviews

| Main session | Reviewer | How |
|---|---|---|
| Claude Code | Codex `gpt-6.1-sol`, effort `medium` | `scripts/launch-review.sh` (runs through `codex-call`) |
| Codex | Claude Opus 5.5, effort `medium` | `scripts/launch-review-opus.sh` |

```bash
~/.agents/skills/adversarial-review/scripts/launch-review.sh <prompt-file> <output-file> [cwd]
~/.agents/skills/adversarial-review/scripts/launch-review-opus.sh <prompt-file> <output-file> <dir> [more dirs]
```

- Both scripts append `codex-call`'s [`review-rules.md`](../codex-call/references/review-rules.md)
  to the prompt, in every round and both directions.
- Both block by design; run them in the background and collect the output file when they finish.
- Both reviewers only read. The Codex reviewer runs in a read-only sandbox. The Opus reviewer gets
  only Read, Grep and Glob and no MCP servers, and it can read only the directories passed to it.
- Follow-ups: the Codex thread id lands in `<output-stem>.thread` (continue with `codex-call`'s
  `resume`); the Claude session id lands in `<output-stem>.session` (continue with
  `claude -p --resume <id>` and the same flags as the script).
- Errors go to `<output-stem>.err`. If the other vendor is unreachable, say so; never substitute
  a model from the same vendor.
- On Windows, run the scripts from Git Bash. They pick the first Python that really runs, because
  `python3` there may be a Store stub. Over ssh to beelink, use a login shell (`bash -lc`) so
  `codex` and `claude` are on the `PATH`.

## Write the prompt from the work, not from the diff

The reviewer has no shared context and reads only what you point it at. Copy
[`references/prompt-scaffold.md`](references/prompt-scaffold.md) and fill in its five parts: paths
to read, the design in your own words (including what exists only in the conversation), the
operating context, a named attack list, and ranked output with the one change it would make first.
Before the first round, write down what the work must establish; a finding outside that is the
weakest kind.

## Treat findings as claims

Reviewers assert confidently and are sometimes wrong about what the code or a source does. Verify
every finding against the source before acting. Fix the confirmed ones; reject the others with the
reason. For a durable lesson, follow `using-brain`'s write workflow instead of leaving it in the chat.

## Rounds and stopping

A reviewer asked "is anything wrong?" finds something for as long as it is asked, so silence is not
the stop rule; the cap and the narrowing are
([Brain method](../../brain/methods/review-silence-is-not-a-stop-criterion.md)).

1. Round 1 reviews the work against what it must establish.
2. Rounds 2 and 3 check only whether the confirmed findings of the previous round are fixed
   correctly and whether those fixes broke something. They are not a fresh pass over everything.
3. Stop as soon as a round brings no confirmed finding that requires a change, and after round 3
   at the latest. Report what is still open.

Report to the user: how many rounds ran, what was fixed, what was rejected and why.
