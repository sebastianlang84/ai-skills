---
name: improving-code-quality
description: "Audit existing programs and scripts for unnecessary complexity, duplicated business logic, and wasted work across a processing flow; improve them when requested. Use for code-quality or anti-slop audits, end-to-end efficiency work, and business-rule changes with known or suspected implementations elsewhere. Small isolated fixes, including local performance fixes, do not trigger this skill unless explicitly requested or a shared business rule is suspected. Excludes prose-only work and architecture-only redesign of module responsibilities."
---

# Improving Code Quality

Improve the required outcome across the affected system, not the appearance of a fragment.
Keep runtime efficiency, maintenance effort, and the agent's own effort distinct; a gain in one
is not evidence of a gain in the others. No change is a valid result.

## 1. Establish the task

Identify the required behavior, affected flow, scope, and a bounded investigation budget from the
request and project context. Scale the work to the impact; do not scan every repository by default.
If no budget is supplied, choose and record a reasonable time or tool-call limit before exploring.
Stop at that limit and report unresolved items; scope updates do not increase it. Continue beyond
the limit only under an explicitly agreed larger budget, not by silently revising the note.

An audit or review alone is read-only, including execution side effects: use static evidence,
existing isolated tests or a dry run whose executed code path you have inspected for writes, sends
and mutations; a flag name alone is not evidence. Alternatively, use an isolated fixture with
external boundaries mocked. Do not invoke live entry points
that write outputs, send messages or mutate external state without authorization for those effects.
An improvement request permits the relevant changes within
its scope; do not ask again for permission already given. Preserve behavior during simplification;
a confirmed bug needs a separately stated behavior change and verification, not a hidden refactor.

Before proceeding, record a short working note: intended outcome, invariants, inspected boundaries,
and the current uncertainty. Update it when evidence changes the scope or when handing work off;
use chat or existing task state, not a new repository file during a read-only audit.

## 2. Trace the affected flow

Read the entry point, relevant callers, existing implementations, transformations, state changes,
and downstream consumers. Include error paths, ordering, retries, concurrency, and resource lifetime
where they affect the contract. For scripts, check launchers, schedules, configuration, and outputs.
Stop expanding at inspected interfaces with known contracts; name unresolved boundaries.

Before changing code, be able to explain how the proposed change affects the caller and consumer,
what must remain true, and why the current structure might exist. If evidence is missing, investigate
within the budget or leave the candidate unresolved instead of guessing.

## 3. Evaluate candidates

Read [the assessment reference](references/assessment.md) for a whole-flow audit, a performance
claim, or a tradeoff between reuse and abstraction; for a narrow shared-rule change, consult only
the relevant section if the decision is unclear.

For each candidate, establish a concrete downside and test a plausible reason for keeping it.
Compare keeping, reusing, simplifying, and adding only as far as the decision requires.
A wrapper that moves complexity into several callers is not redundant; similar syntax alone does
not establish shared business knowledge. Counts and complexity scores are leads, not change orders.

For retries, locking, validation and cleanup, inspect the protected failure or concurrency contract
and its callers, then verify that the proposed removal preserves it with relevant checks; absence
of failures in logs is not evidence of redundancy. If removal changes that contract, treat it as
a separate behavior change and require authorization covering that policy change; a request to
simplify alone is insufficient. Preserve the safeguard when its purpose is uncertain.
Before removing a path, inspect
its actual integration, including known external callers, schedules, configuration and dynamic or
public entry points. No search hits alone do not establish non-use; unresolved use blocks deletion.
Remove confirmed obsolete parts together with their in-scope configuration and documentation.

If a useful change requires a broader architectural redesign, report the evidence and the boundary;
continue only within the authorized scope. Do not turn a bounded audit into a rewrite.

## 4. Change and verify when authorized

Choose the smallest coherent change that improves the whole flow. Establish the relevant existing
behavior first, including error and empty-input cases; use meaningful characterization checks when
coverage is missing. Preserve output types, side effects, ordering, data freshness, and failures,
not just the happy-path value. Keep baseline inputs and expected results outside the edited scope.

Run the project's required checks for the affected area and relevant caller/consumer checks.
Do not weaken tests to bless a refactor. Measure claimed performance improvements using identical
representative inputs and conditions, including end-to-end effects; record spread and quality limits.
If a comparison is incomplete or infrastructure fails, report it as unresolved, not as an improvement.
Qualitative maintainability improvements remain qualitative unless a follow-up task measures them.

Recheck affected boundaries after the change. Stop once the requested behavior and justified change
pass their checks; do not keep inventing cleanup to make the audit appear productive.

## 5. Report evidence

For an audit or whole-flow improvement, group every finding within the inspected scope by evidence,
with counts, keeping severity separate; for improvements also report changes and checks:

1. Reproduced behavior or measured resource waste.
2. Structural disadvantages supported by inspected callers, contracts, or duplicated rules.
3. Unresolved hypotheses requiring further evidence.

For each, state the location, affected flow, consequence, evidence, counterargument, proposed or
completed change, and verification. Include rejected candidates and their reasons in the full
record; the short summary may group them with counts. Identify uninspected areas and budget stops.
When there are no justified changes, say so without claiming the entire program is proven clean.
Choose the report form from the requested and inspected scope, not the number of edits made.
In either form, report rejected candidates, uninspected areas and budget stops when present.
For a narrow improvement, report what changed, which checks ran, and what remains unverified;
include any additional findings without forcing an audit-shaped record for a single change.
Keep the full audit record in chat or existing task state, not a new repository file in read-only mode.
Follow the existing delivery and
independent-review workflow rather than introducing a second review loop.
