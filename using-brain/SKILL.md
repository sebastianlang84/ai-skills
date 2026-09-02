---
name: using-brain
description: Read, explain, and extend the shared Brain at ~/.agents/brain. Use when a task depends on prior local decisions, preferences, methods, patterns, or indexed repo knowledge; when the user asks what the Brain knows or how it works; when durable cross-session learning should be recorded; or before changing Brain structure, retrieval, categories, provenance, or trust. Skip it for self-contained tasks answered entirely by current sources when no durable learning is expected. Do not use it for a project-local knowledge system with its own rules.
---

# Using the shared Brain

The Brain is the machine-wide, linked, durable memory shared by all agent harnesses. Its canonical
checkout is `~/dev/brain`; `~/.agents/brain` points to it. Use it to recover relevant context and to
preserve knowledge that should survive sessions, without loading the whole corpus.

The Brain's purpose, architecture, retrieval model, and construction recipe live in
[`brain-architecture.md`](/home/wasti/.agents/brain/brain-architecture.md). Its schema and trust
rules live in [`README.md`](/home/wasti/.agents/brain/README.md) and
[`type-vocabulary.md`](/home/wasti/.agents/brain/type-vocabulary.md). Read those only when the task
touches the Brain itself or will write to it.

## Read

1. Open `~/.agents/brain/index.md`. Use its titles and descriptions to choose the smallest relevant
   subtree.
2. Follow the relevant subtree index, then open only the concepts needed for the task. If routing is
   unclear, use `rg` first for exact names, paths, commands, or one discriminative keyword. For a
   ranked second pass, use `codemap search` with short terms matching the Brain's vocabulary and
   language. Do not pass a free-form German question to the mostly English corpus and treat its
   ranking as semantic retrieval. Do not bulk-load the bundle.
3. Distinguish the Brain's synthesis from the current authority. For drift-prone or consequential
   claims, inspect the cited source or the owning repo before treating the claim as current. When
   freshness itself is in scope or a local source appears to have moved, run
   `python3 ~/.agents/brain/tools/audit_staleness.py`; treat every finding as a review trigger, not
   proof that the concept is false.
4. Preserve trust state in the answer: machine-written or `draft` concepts inform; they are not
   human-confirmed rules.

Reading is complete when the answer can name the relevant concept, its authority, and any material
staleness or verification boundary.

## Decide whether to write

Write only knowledge that should change a future session:

- a decision with its reason and reversal condition;
- a correction or durable working agreement from the user;
- an invariant or repo-specific synthesis not already documented by the owning repo;
- a reusable method, proven cross-repo pattern, goal, person fact, or executable check;
- a confirmed limitation or retrieval failure in the Brain itself.

Interesting external tools that plausibly solve a future job on this machine go into
[`decisions/tool-candidates/`](/home/wasti/.agents/brain/decisions/tool-candidates/). Record the
target job, status and evidence that would change it; add a dedicated Decision or Check only after
meaningful evaluation. Do not turn every mentioned library into a candidate.

Keep transient task state in the task tracker or handoff and current product facts in the owning
repo. Record a durable unresolved question under the exact `## Open questions` heading defined by
the type vocabulary; keep actionable work in the planning system. A proposal becomes a decision or
method only when it is adopted, rejected, or supported by evidence. Never store secrets, bulk
transcripts, copied repo documentation, or a claim without an openable source.

Before adding a concept, search for the same idea and its nearest neighbours. Update the canonical
concept when the identity is the same; create a new concept only when it has a distinct claim.

## Write

1. Read the root index, the target subtree index, `README.md`, and `type-vocabulary.md`.
2. Choose an existing type and canonical path. If none fits, stop the content write and treat the
   vocabulary change as a deliberate Brain design decision; never mint a plausible new type inline.
3. Check live ownership with the `parallel-agents` workflow. Atomically lock the concept, every
   index it changes, and `log.md`:

   ```bash
   python3 ~/.agents/skills/parallel-agents/scripts/brain-lock.py acquire \
     <concept> <index> log.md
   ```

4. Write one concept per file with honest `title` and `description`, actor and timestamp, openable
   provenance, and links to neighbouring concepts. Do not add a `verified` entry for the agent's own
   work.
5. Link the concept from the nearest index and add one chronological entry to `log.md`. Update the
   root index only when it is part of the retrieval path.
6. From `~/dev/brain`, run `python3 tools/lint.py`. Fix every failure before releasing the lock:

   ```bash
   python3 ~/.agents/skills/parallel-agents/scripts/brain-lock.py release <token>
   ```

The write is complete only when the concept has one canonical home, is discoverable from an index,
has provenance, passes lint, and the lock is released.

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

When changing this skill's frontmatter or the global Brain-routing policy, run the frozen
`using-brain` suite under `~/dev/wasti-research/programs/skill-descriptions/` separately for each
harness. Report literal skill invocation and functional Brain routing as different metrics: Claude
Code exposes a first-class `Skill` call, while Promptfoo infers Codex skill use only from a direct
`SKILL.md` read. The current baseline and re-run contract live in the
[cross-harness trigger check](/home/wasti/.agents/brain/checks/using-brain-trigger-routing.md).
Require repeated runs before changing the description from a routing result; keep raw outputs in
the research repository, not the Brain.

## Keep the layers aligned

- Change this skill when triggers, step order, commands, safety checks, or completion criteria
  change.
- Change the Brain when purpose, architecture, rationale, current capability, limitations, or
  durable knowledge changes.
- Change scripts, hooks, or lint when a rule can be checked mechanically; documents name the
  invariant and point to the enforcement.
- Re-read `brain-architecture.md` after changing this skill, and re-read this skill after changing
  the documented operating model. Update only the canonical layer unless behavior actually changed.
