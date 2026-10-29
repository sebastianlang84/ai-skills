---
name: autoresearch
description: "Improve something through controlled experiments: freeze a metric and cases, change one lever, measure, keep or discard. Use when the user says autoresearch, or when tuning retrieval/ranking quality, prompts, skill descriptions, cost, or performance needs a baseline instead of a one-off change. Not for ordinary fixes with no verification signal."
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
2. **Fix the decision point before measuring.** Record the decision question, the evidence already at hand, the decision rule, and the delivery date. On that date deliver a recommendation with its uncertainties, whatever the measurement has reached.
3. **Freeze the evaluation before tuning.** Fix known, evidenced defects in tools, inputs and environment; a baseline on a broken environment measures the breakage, not the lever, and disputed findings do not block the confirmed fixes. Then define benchmark cases, metrics, guardrails, and success criteria before changing the system. After freezing, change the evaluation, its cases and its harness only for defects that make the comparison unusable, and park improvements to them for a later experiment; the chosen lever stays the one change to the target system.
4. **Establish a baseline.** Record current results, version/commit when relevant, environment, and the target system's known misses.
5. **List levers.** Identify the parts of the system that can plausibly affect the metric.
6. **Pick one hypothesis.** Change one lever at a time; avoid mixing benchmark edits with implementation/ranking/tuning edits.
7. **Run the fixed evaluation.** Rebuild/reindex/restart only when the changed lever requires it. Keep each run's inputs, prompt, model configuration, code state, and result.
8. **Compare deltas.** Note improvements, regressions, latency/cost impact, and which cases moved. Before claiming repeatability, check that the compared runs share inputs, prompt, model configuration, and code state; report runs whose conditions differ as separate groups, and the spread of results within each group.
9. **Classify failures.** Use task-specific miss classes instead of guessing blindly.
10. **Decide keep/discard.** Keep only if metrics and qualitative evidence justify the complexity and regressions.
11. **Log the experiment.** Preserve enough detail that another agent can resume or reproduce the run. Delete comparison artifacts only after the evaluation is finished and its evidence is stored durably.

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

Apply this local default only when the user explicitly names CodeMap or `/home/wasti/dev/autoresearch`:

- `/home/wasti/dev/autoresearch` is the CodeMap retrieval-quality benchmark workspace: a small realistic benchmark corpus and experiment protocol for improving CodeMap retrieval quality through quantitative benchmark loops.
- The CodeMap implementation target is usually the checkout at `/home/wasti/dev/codemap`; read its repo rules before experimenting.
- Useful CodeMap levers include indexed files/extensions/ignores, chunking, symbol extraction, query planning, ranking, benchmark ground truth, and index-version rebuild behavior.
- Use fixed retrieval metrics such as MRR@5, recall@5, top-1 accuracy, expected coverage, and latency; classify misses before proposing changes.
