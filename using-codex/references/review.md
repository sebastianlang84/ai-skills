# Adversarial review: how

The rule for when a review runs, who reviews, and how many rounds is in the global `AGENTS.md`:
substantial work is reviewed by the other vendor, at most three rounds. This file is the how, for
both directions: Claude sessions launch Codex with `using-codex`'s `scripts/launch-review.sh`,
Codex sessions launch Opus with `using-claude`'s `scripts/claude-call.sh --review`.

## Write the prompt from the work, not from the diff

The reviewer has no shared context and reads only what you point it at. Copy
[`prompt-scaffold.md`](prompt-scaffold.md) and fill in its five parts: paths to read, the design in
your own words (including what exists only in the conversation), the operating context, a named
attack list, and ranked output with the one change it would make first. Before the first round,
write down what the work must establish; a finding outside that is the weakest kind. Point the
review at the decision or artefact that matters, with the smallest evidence set that settles it.

Both launchers append [`review-rules.md`](review-rules.md) in every round.

The Opus reviewer can only read files. Give it the diff and any command output as files (for
example `git diff --cached > <dir>/review.diff`) inside a directory you pass, and name them in the
prompt. The Codex reviewer can run read-only commands itself, but a diff file does no harm there.

## Treat findings as claims

Reviewers assert confidently and are sometimes wrong about what the code or a source does. Verify
every finding against the source before acting. Fix the confirmed ones; reject the others with the
reason. For a durable lesson, follow `using-brain`'s write workflow instead of leaving it in the chat.

## Rounds

A reviewer asked "is anything wrong?" finds something for as long as it is asked, so silence is not
the stop rule; the cap and the narrowing are
([Brain method](/home/wasti/.agents/brain/methods/review-silence-is-not-a-stop-criterion.md)).

1. Round 1 reviews the work against what it must establish.
2. Rounds 2 and 3 check only whether the previous round's confirmed findings are fixed correctly
   and whether those fixes broke something. Say so in the prompt.
3. Stop as soon as a round brings no confirmed finding that requires a change, and after round 3
   at the latest.

Report to the user: how many rounds ran, what was fixed, what was rejected and why, what is open.
If the other vendor is unreachable, say so; never substitute a model from the same vendor.
