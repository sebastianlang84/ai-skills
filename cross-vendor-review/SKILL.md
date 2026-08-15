---
name: cross-vendor-review
description: Get an adversarial second opinion from a different vendor's model (Codex/GPT) on a design, plan, or architecture decision, running in the background so work continues meanwhile. Use when a substantial decision is about to be committed to, when the user asks to have something "gegengelesen", wants a second opinion, a codex review, or a devil's advocate — and proactively after any design that will be expensive to reverse. Not for reviewing a code diff; that is what a code review does.
---

# Cross-vendor review

A second opinion is only worth its tokens if it comes from a **different vendor** and is pointed at
what the design *is*, not at a diff. Same-vendor review catches anchoring, not blind spots.

## Always background it

Launch the reviewer through the harness's background mechanism and keep working. A high-effort
review takes minutes; blocking on it wastes the entire point. Fold the findings in when it lands.

```bash
~/.agents/skills/cross-vendor-review/scripts/launch-review.sh <prompt-file> <output-file> [cwd]
```

The script blocks by design — the *caller* backgrounds it. Defaults to `gpt-5.6-sol` at high
reasoning effort, read-only sandbox; override with `REVIEW_MODEL`.

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

A second round is justified only when the first produced a confirmed blocker whose fix was
substantial — and then its mandate is *that fix*: was it really fixed, did it break anything, do the
criteria still hold. It is not a fresh unbounded pass over everything.

For a design document rather than code there are no gates, so the spec has to carry the whole load:
write down before the review what the document must establish, and treat anything outside it as the
weakest class of finding no matter how compelling it reads. Reasoning and the evidence ranking:
[`~/.agents/brain/methods/review-silence-is-not-a-stop-criterion.md`](../../brain/methods/review-silence-is-not-a-stop-criterion.md).
