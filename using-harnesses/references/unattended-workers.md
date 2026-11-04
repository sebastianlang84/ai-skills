# Unattended worker setup

This is the coordinator's procedure for one small unattended step. It defines launch gates;
it does not install a guard or change a dispatcher.

## Record the run card

Inspect ticket notes and history for an existing result. The coordinator holds the ticket,
records the numbered plan and current step, then fills every field below in a ticket note:

```text
Current step and observable end result:
Owned checkout, branch and writable paths:
Evidence paths and a few known search hits:
Input-token ceiling (including cached input):
Model-request ceiling:
Wall-clock ceiling:
Separate verification/review reserve:
Result file and required narrow checks:
Stop and handoff when:
```

Choose positive numeric limits from a comparable small run, not remaining subscription quota.
Count every model request, including failed requests and waits returning to the model. Include
child calls in the input allowance or prohibit them and reserve separate review input in the
coordinator. If the work does not fit, dispatch a smaller step, not a batch of tickets.

The worker gets only this card, relevant constraints and evidence. The coordinator keeps board
claims, notes, replies and closure. Workers skip board, Brain, skill discovery and session
ownership rituals unless their bounded job explicitly needs one; supply necessary instructions
directly. Search before reading, bound excerpts/output, and run only checks that affect this step.

## Verify enforcement before dispatch

Use a fresh conversation for each step. A prompt ceiling is not enforcement. Before automatic
dispatch, verify an external guard against the actual runner:

1. Associate events with this run and its explicit children, not unrelated sessions sharing a
   directory. Canonical path boundaries must distinguish sibling checkouts such as repo/repo-old.
2. Start accounting before the worker, include initial input, count each request once, and cover
   worker and child homes. Ignore duplicate cumulative usage events.
3. Independently enforce input, request and elapsed-time ceilings. Stop the owned process group
   or unit, including children, without stopping another session.
4. Save counts, stop reason and result paths outside the disposable checkout. Verify the stop
   command succeeded. Missing/malformed usage must refuse launch or stop safely, not disable limits.

Exercise below-limit completion, each exceeded ceiling, a child call, a sibling checkout and
missing usage with synthetic/local fixtures before calling the guard verified. Accounting from
completed responses can overshoot by an in-flight request plus sampling delay; state that bound
instead of claiming an exact provider-side cap and set the allowance conservatively.

If a boundary is unverified, deliver the bounded preparatory result and record missing coverage
on the ticket; leave activation to the runner owner. Do not automatically dispatch or replace a
running worker to test its guard.

## Collect and hand off

Collect long commands after their expected completion without repeated short polls. Require a
result file with changed paths, narrow checks, measured input/request counts and open work.
Compare consumption with the card, including failed/cancelled runs. At a ceiling, keep the partial
result and stop. A fresh conversation does not replenish the same ticket's budget: the coordinator
must revise the recorded allowance or split remaining work before another dispatch.

The coordinator verifies the result and arranges the separate review under the active global
rules. For this host's unattended Codex adapter, use a separate Codex call, never Claude/Opus.
Merge only authorized, checked work. If foreign changes block integration, keep a clean branch
and ticket handoff. State measured guard coverage and untested behavior in the closing note.

## Local evidence and remaining integration

The compaction trial had 21 requests per run, no compactions and 8/8 checked facts. Input
sum/maximum was 740574/43423 without the setting and 822833/47338 with it. The configured threshold
was not reached: this proves neither savings nor a safe default. Keep compaction defaults unchanged.

The guard snapshot shows 3322786 input, 71 steps and a 6000000-token ceiling with no guard stop.
It demonstrates prototype accounting, not cutoff success. The prototype sets its own start time rather
than using an explicit worker-run identity, matches cwd by string prefix and enforces only input. Ownership and request/time limits
remain unverified. Do not treat it as the guard above. Dispatcher/runner integration belongs to
its owning repository; this procedure is a first step, not installed automatic enforcement.
