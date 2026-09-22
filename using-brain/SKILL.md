---
name: using-brain
description: Read and extend the shared Brain at ~/.agents/brain in every session — retrieve prior local decisions, preferences, methods, patterns, and repo knowledge before working, and record durable learning before finishing. A session-start hook loads this skill in Claude Code, Codex, and Pi; invoke it explicitly when the hook did not run. Also use when the user asks what the Brain knows or how it works, or before changing Brain structure, retrieval, categories, provenance, or trust. Do not use it for a project-local knowledge system with its own rules.
---

# Using the shared Brain

The Brain is the machine-wide, linked, durable memory shared by all agent harnesses. Its canonical
checkout is `~/dev/brain`; `~/.agents/brain` points to it. Use it to recover relevant context and to
preserve knowledge that should survive sessions, without loading the whole corpus.

Use it in every session, without exception:

- **Before working**, follow [Read](#read) far enough to know whether the Brain holds anything
  relevant to the task. When nothing matches after the index check, continue without it.
- **Before finishing**, apply [Decide whether to write](#decide-whether-to-write) to what the session
  produced, and follow [Write](#write) for every qualifying item. Skip the write only when nothing
  qualifies; never lower the bar to have something to write.

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

## Maintain the Brain

When explaining or reproducing the Brain, changing its retrieval or structure, or changing this
skill, read [`references/maintenance.md`](/home/wasti/.agents/skills/using-brain/references/maintenance.md) first.
