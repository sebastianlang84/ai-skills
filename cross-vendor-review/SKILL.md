---
name: cross-vendor-review
description: Get a narrowly scoped adversarial second opinion from another vendor's model on a substantial design, plan, or architecture decision. Use when the user explicitly asks for something to be "gegengelesen", a second opinion, a Codex/Opus review, or a devil's advocate; or when an expensive-to-reverse decision has a named unresolved risk and the verdict could change the decision. Not for routine implementation, small or reversible changes, code diffs, general reassurance, or automatic review after every change.
---

# Cross-vendor review

A second opinion is only worth its tokens if it comes from a **different vendor** and is pointed at
what the design *is*, not at a diff. Same-vendor review catches anchoring, not blind spots.

## Gate the launch

An explicit user request authorizes one review; still narrow it to the decision they care about.
Without an explicit request, launch only when all are true:

1. The decision is substantial and expensive to reverse, or controls a real security, data-loss, or
   correctness boundary.
2. One concrete uncertainty remains after reading the source and running the available deterministic
   checks.
3. A plausible contrary verdict would change the design or stop the work.

If any condition is missing, do not spend the foreign-model call. A passing routine change does not
earn a review merely because a reviewer is available. Review one decision against the smallest
evidence set that can settle it; do not submit the whole workstream for general reassurance.

## Background an approved review

Launch the reviewer through the harness's background mechanism and keep working. A review can take
minutes; blocking on it wastes the entire point. Fold the findings in when it lands.

```bash
~/.agents/skills/cross-vendor-review/scripts/launch-review.sh <prompt-file> <output-file> [cwd]
```

The script blocks by design — the *caller* backgrounds it. It is the Claude-to-GPT adapter and
defaults to `gpt-5.6-sol` at `medium` reasoning effort in a read-only sandbox; override with
`REVIEW_MODEL` or `REVIEW_REASONING_EFFORT`. From Codex/GPT, use the harness's Claude/Opus
background mechanism. If no foreign-vendor reviewer is available, report that instead of silently
substituting a same-vendor model.

## Write the prompt from the design, not from the diff

The reviewer has no shared context and will read only what you point it at. Copy
[`references/prompt-scaffold.md`](references/prompt-scaffold.md) and fill in its five parts:

1. **Explicit paths to read** — repos, specs, the files that carry the decision. A vague pointer
   produces a vague review.
2. **The design in your own words** — including the parts that exist only in the conversation and
   nowhere on disk yet. This is usually the largest section and the one that decides review quality.
3. **The operating context** — private machine vs. team, what the owner has already ruled out, what
   is not a constraint. Without it you get process objections that do not apply.
4. **A named attack list** — the specific joints you suspect. "Review this" returns a summary;
   "are these four gates independent or one gate wearing four hats" returns a finding.
5. **Ranked output, worst first**, each with the concrete breaking scenario and an alternative —
   plus the single change it would make if it could make only one.

## Treat the verdict as a claim, not a ruling

Reviewers assert confidently and are sometimes wrong about what the code actually does. Verify a
finding against the source before acting on it, and say plainly which ones you confirmed, which you
rejected and why. Fold the confirmed ones in; a durable one belongs in the knowledge base
(`~/.agents/brain`), not only in the chat.

## Decide when to stop *before* launching the first round

An adversarial reviewer asked "is anything wrong here?" answers yes for as long as it is asked, and
every fix affords new plausible objections. **"Review until it finds nothing" is not a termination
condition.** One round is the default. Stop when the acceptance criteria stated before the work are
met, the repo's deterministic gates pass, no confirmed blocker is open, and each confirmed defect
left a regression test behind.

A second round or higher reasoning effort is justified only when the first `medium` round produced a
confirmed blocker whose fix was substantial, or exposed one concrete risk that `medium` could not
settle — and then its mandate is *that fix or risk*. It is not a fresh unbounded pass over everything.

For a design document rather than code there are no gates, so the spec has to carry the whole load:
write down before the review what the document must establish, and treat anything outside it as the
weakest class of finding no matter how compelling it reads. Reasoning and the evidence ranking:
[`~/.agents/brain/methods/review-silence-is-not-a-stop-criterion.md`](../../brain/methods/review-silence-is-not-a-stop-criterion.md).
