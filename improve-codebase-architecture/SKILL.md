---
name: improve-codebase-architecture
description: Find deepening opportunities in a codebase — refactors that turn shallow modules into deep ones. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

## Glossary

Use the terms and principles in [LANGUAGE.md](LANGUAGE.md) exactly in every suggestion — read it first; don't drift into "component," "service," "API," or "boundary."

## Process

### 1. Explore

Walk the codebase: in Claude Code, use the Agent tool with `subagent_type=Explore`; elsewhere, read the code directly or run a cheap scout through `using-harnesses`' `codex_call.py` with `--model gpt-6-luna --effort low`. Don't follow rigid heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Look for evidence

Exploration yields suspicions; evidence decides which ones become candidates. Look for:

- Files in separate modules that change together (`git log --name-only`).
- Repeated bug fixes at the same seam.
- Tests that mock internals, or tests that are missing.
- The same call sequence repeated across several callers.

Evidence counts only when it ties a cost to the current interface. Rule out mechanical causes first — formatting, renames, generated code, dependency bumps, large rewrites. Citable code is evidence even without history.

### 3. Present candidates

Present a numbered list of deepening opportunities, ranked by benefit against cost. For each candidate:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Evidence** — the commits, call sites, or tests that show it
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality and leverage, and also in how tests would improve
- **Cost** — S, M, or L, with the counted callers and tests:
  - **S** — one module and its tests.
  - **M** — several modules or callers within the repo.
  - **L** — a public or cross-repo interface, stored data, or code you don't own. Unknown callers mean L.

  The levels are lower bounds. Raise the level for changes that are hard to verify: concurrency, ordering, state, untested behaviour.
- **Strength** — how sure the remedy is. **Speculative** means the friction is evidenced but the remedy or its benefit is uncertain.

A candidate without evidence is not listed. Give a top recommendation only when its benefit justifies its cost.

If no candidate has evidence, write exactly this line, so a calling skill or an eval can detect the empty result:

No warranted deepening found.

Then name what you examined, and stop.

When another skill loads this one as a method (for example as an audit lens), that skill sets the output format and the stopping point; the lens, the principles, the evidence rule and the candidate fields still apply.

**Use [LANGUAGE.md](LANGUAGE.md) vocabulary for the architecture.** Name modules after what they do, using the project's own terms from the code — "the Order intake module," not "the FooBarHandler," and not "the Order service."

Do NOT propose interfaces yet. Ask the user: "Which of these would you like to explore?"

### 4. Design conversation

Once the user picks a candidate, walk the design tree with them one question at a time, each with your recommended answer — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

To classify a candidate's dependencies and decide how the deepened module is tested across its seam, see [DEEPENING.md](DEEPENING.md). Want to explore alternative interfaces for the deepened module? See [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md).
