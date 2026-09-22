# Maintaining the Brain

Read this only when explaining, reproducing, restructuring, or measuring the Brain itself, or when changing the `using-brain` skill.

## Explain or reproduce the Brain

When asked what the Brain is, why it exists, how it works, how to use it, or how to build another
one, start with `brain-architecture.md`, then follow its links for the requested depth. Report the
current implementation separately from desired future capabilities; in particular, do not imply
automatic clustering, contradiction detection, semantic retrieval, or semantic staleness
detection. The current report-only audit covers elapsed review dates and selected local-source
failures, not whether prose remains true.

## Improve retrieval and structure

Use the `autoresearch` workflow for retrieval or ranking changes and the Brain's
[measured improvement loop](/home/wasti/.agents/brain/methods/measured-improvement-loop.md): freeze
representative questions, expected concepts, and context cost; change one lever; keep or discard.
Record durable results in the Brain and keep raw runs outside it. The current measured routing
boundary is the [CodeMap-vs-rg Brain check](/home/wasti/.agents/brain/checks/brain-retrieval-codemap-vs-rg.md).
Real-use cases are accumulating in
`~/dev/wasti-research/programs/brain-real-use-retrieval/`; retrieval audits append only consecutive,
qualifying observed questions there and must not tune against the partial set before it is frozen.
There is no active SQLite projection: the
[preregistered SQLite/FTS5 treatment](/home/wasti/.agents/brain/checks/brain-sqlite-projection.md)
fully passed six of seven integrity gates; delete-and-rebuild did not retest retrieval. It also
ranked slightly worse and ran 5.6 times slower than `rg`. Do not recreate it as routine setup.
Reconsider it only for a measured compound-query need or after corpus size or query volume makes
direct Markdown scanning materially slow on a newly frozen workload.

Before implementing a new index, database projection, search engine, embedding layer, or ranking
strategy:

1. Pre-register the current baseline, visible regression cases, held-out cases, primary metrics,
   integrity guardrails, keep/discard rule, and result-log location. Freeze them before implementation.
2. Treat Markdown as the only write authority. A derived store must preserve every projected
   concept, link, source, tag, status, and verification; detect staleness; build deterministically;
   and survive deletion followed by a complete rebuild. Do not write knowledge directly to it.
3. Measure structured-query answer sets as well as Top-1, Recall@5, MRR@5, latency, and retrieved
   context size where applicable. Test embeddings as a separate lever from structured storage or
   lexical ranking.
4. Keep the addition only if every integrity gate passes and it produces a measured benefit worth
   its operational complexity. Otherwise remove it and retain the logged result.

Growth is successful when more useful knowledge is retrievable without increasing the default
context load or weakening provenance and trust.

When changing the `using-brain` skill's frontmatter or the global Brain-routing policy, run the frozen
`using-brain` suite under `~/dev/wasti-research/programs/skill-descriptions/` separately for each
harness. Report literal skill invocation and functional Brain routing as different metrics: Claude
Code exposes a first-class `Skill` call, while Promptfoo infers Codex skill use only from a direct
`SKILL.md` read. The current baseline and re-run contract live in the
[cross-harness trigger check](/home/wasti/.agents/brain/checks/using-brain-trigger-routing.md).
Require repeated runs before changing the description from a routing result; keep raw outputs in
the research repository, not the Brain.

## Keep the layers aligned

- Change the `using-brain` skill when triggers, step order, commands, safety checks, or completion criteria
  change.
- Change the Brain when purpose, architecture, rationale, current capability, limitations, or
  durable knowledge changes.
- Change scripts, hooks, or lint when a rule can be checked mechanically; documents name the
  invariant and point to the enforcement.
- Re-read `brain-architecture.md` after changing the `using-brain` skill, and re-read the skill after changing
  the documented operating model. Update only the canonical layer unless behavior actually changed.
