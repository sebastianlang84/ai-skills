---
name: autoresearch
description: "Use when the user mentions autoresearch, or when an improvement request explicitly needs a measurable baseline plus repeatable evaluation/benchmark/rubric to compare variants. Autoresearch turns optimization work into controlled loops: define a goal, freeze metrics and cases, form hypotheses, change one lever at a time, run evaluations, log quantitative deltas, classify regressions, and keep/discard changes. Especially useful for retrieval/search quality, ranking, chunking, agents/prompts/workflows, skill descriptions, extension/tool prompt injections, performance, cost, reliability, usability, and other systems with iterative loops and measurable outcomes. Do not use for ordinary bugfixes, reviews, prose edits, vague brainstorming, or one-off changes without a verification signal."
---

# Autoresearch

Autoresearch is an improvement method, not just a repository. Use it when the task is to make something better through repeatable, measurable experiments with a baseline and verification signal. Do not load it for ordinary “improve this” requests unless the work needs controlled comparison across variants.

Core idea: convert “improve this” into a loop of **hypothesis → controlled change → fixed evaluation → result log → keep/discard decision**.

## When it helps

Use autoresearch only for systems with:

- a target behavior to improve, such as quality, relevance, latency, accuracy, reliability, cost, usability, or throughput
- a baseline and repeatable evaluation, benchmark, test set, corpus, task list, rubric, or observable metric
- adjustable levers, such as ranking weights, prompts, skill descriptions, tool descriptions, prompt injections, chunking, symbols, parameters, workflows, caches, indexes, heuristics, UI variants, process steps, or configuration
- enough runs to compare a baseline against variants

Good fits include:

- search, retrieval, ranking, RAG, CodeMap, chunking, indexing, symbol extraction, and context selection
- agent prompts, skill descriptions, extension/tool prompt injections, workflows, orchestration, tool-routing, and review processes
- benchmarks, eval suites, golden cases, trigger tests, regression tests, and quality gates
- performance/cost tuning when latency, memory, throughput, or spend can be measured
- reliability, usability, conversion, quality, or process improvements when outcomes can be quantified

For agent-context surfaces such as skill descriptions or extension/tool prompt injections, first define a verification method: held-out user prompts, expected tool/skill routing, false-positive/false-negative counts, task replay outcomes, rubric scores, latency/token overhead, or another reproducible signal.

Do not use autoresearch as the main frame when:

- the user only wants a direct bug fix, prose edit, or implementation with obvious acceptance criteria
- no meaningful metric, benchmark, rubric, or fixed comparison can be defined
- the change is production-risky and cannot be tested safely
- the task is primarily exploratory discussion with no decision to run experiments

## Required workflow

1. **State the target system and improvement goal.** Name what should get better and for whom.
2. **Freeze the evaluation before tuning.** Define benchmark cases, metrics, guardrails, and success criteria before changing the system.
3. **Establish a baseline.** Record current results, version/commit when relevant, environment, and known misses.
4. **List levers.** Identify the parts of the system that can plausibly affect the metric.
5. **Pick one hypothesis.** Change one lever at a time; avoid mixing benchmark edits with implementation/ranking/tuning edits.
6. **Run the fixed evaluation.** Rebuild/reindex/restart only when the changed lever requires it.
7. **Compare deltas.** Note improvements, regressions, latency/cost impact, and which cases moved.
8. **Classify failures.** Use task-specific miss classes instead of guessing blindly.
9. **Decide keep/discard.** Keep only if metrics and qualitative evidence justify the complexity and regressions.
10. **Log the experiment.** Preserve enough detail that another agent can resume or reproduce the run.

## Experiment design rules

- Change one meaningful lever per experiment.
- Prefer simple, explainable changes over opaque magic unless the gain is large and robust.
- Do not optimize by weakening the benchmark after seeing results.
- Separate benchmark/ground-truth changes from system-behavior changes.
- Track both primary metrics and guardrails; a local win with broad regressions is not a win.
- If results are noisy, repeat the run or narrow the claim.
- If a miss is unclear, inspect the failure before changing code.

## Output shape

When planning autoresearch work, return:

```text
Goal:
Baseline/evaluation:
Primary metric:
Guardrails:
Levers:
Hypotheses:
Next experiment:
Keep/discard rule:
Log location:
```

When reporting a completed experiment, return:

```text
Experiment:
Change:
Baseline:
Result:
Delta:
Fixed cases:
Regressions:
Decision: keep|discard|rerun
Next step:
```

## Local default: CodeMap retrieval-quality work

In this environment, if the user mentions autoresearch together with CodeMap, retrieval, search quality, context, indexing, chunking, ranking, symbols, or `/home/wasti/dev/autoresearch`, default to this interpretation:

- `/home/wasti/dev/autoresearch` is the CodeMap retrieval-quality benchmark workspace.
- It is a small realistic benchmark corpus and experiment-protocol workspace.
- The goal is to improve CodeMap retrieval quality through quantitative benchmark loops.
- The CodeMap implementation target is usually `/home/wasti/.pi/agent/git/github.com/sebastianlang84/pi-ext-codemap`.
- Useful CodeMap levers include indexed files/extensions/ignores, chunking, symbol extraction, query planning, ranking, benchmark ground truth, and index-version rebuild behavior.
- Use fixed retrieval metrics such as MRR@5, recall@5, top-1 accuracy, expected coverage, and latency; classify misses before proposing changes.
