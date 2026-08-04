---
name: diagnosing-bugs
description: Disciplined diagnosis loop for hard bugs, flaky failures, and performance regressions — build a tight failing feedback loop before forming any hypothesis. Use when the user says "debug this"/"diagnose", or reports something broken, throwing, failing, hanging, or slow.
---

# Diagnosing Bugs

A discipline for hard bugs — the ones that resist a first glance, the intermittent flake, the regression that crept in between two known-good states. Skip phases only when explicitly justified.

Adapted from Matt Pocock's `diagnosing-bugs` skill (MIT, github.com/mattpocock/skills).

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a **tight** pass/fail signal for the bug — one that goes **red** on *this* bug — you will find the cause; bisection, hypothesis-testing, and instrumentation all just consume it. If you don't have one, no amount of staring at code or logs will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to construct one — try them in roughly this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **HTTP probe** — `curl` against the running service, asserting on status/body/timing.
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
4. **Container-scoped run** — `docker compose run --rm <svc> <cmd>` or `docker exec` against the live container, so the loop reproduces the bug in the environment that actually has it.
5. **Unit-scoped service run** — run the unit's command directly (`systemctl --user cat <unit>` to get it, then run that command in the foreground) instead of restarting the service and reading logs afterwards.
6. **Replay a captured trace.** Save a real request / payload / event to disk; replay it through the code path in isolation.
7. **Throwaway harness.** Spin up a minimal subset of the system (one service, stubbed deps) that exercises the bug path with a single call.
8. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 varied inputs and look for the failure mode.
9. **Bisection harness.** If the bug appeared between two known states (commit, dataset, image tag, config), automate "boot at state X, check, repeat" so you can `git bisect run` it.
10. **Differential loop.** Run the same input through old-version vs new-version (or two configs) and diff outputs.

> **On this machine, logs are a weak signal.** System log access is restricted (no `journalctl`, no `/var/log` reads, no `dmesg`). Treat that as a feature of this skill, not an obstacle: it forces you to Phase 1 instead of grepping. Where a service's own file-based logs *are* readable, they are evidence — but a readable log is still not a loop.

Build the right feedback loop, and the bug is 90% fixed.

### Tighten the loop

Treat the loop as a product. Once you have *a* loop, **tighten** it:

- Faster? (Cache setup, skip unrelated init, narrow the scope.)
- Sharper signal? (Assert on the specific symptom, not "didn't crash".)
- More deterministic? (Pin time, seed RNG, isolate the filesystem, freeze the network, pin the image tag.)

A 30-second flaky loop is barely better than no loop; a 2-second deterministic one is tight — a debugging superpower.

### Non-deterministic bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate until it is.

### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to whatever environment reproduces it, (b) a captured artifact (HAR, log dump, payload, screen recording with timestamps), or (c) permission to add temporary instrumentation. Do **not** proceed to hypothesise without a loop.

### Completion criterion — a tight loop that goes red

Phase 1 is done when you can name **one command** — a script path, a test invocation, a curl — that you have **already run at least once** (paste the invocation and its output), and that is:

- [ ] **Red-capable** — it drives the actual bug code path and asserts the **user's exact symptom**, so it goes red on this bug and green once fixed. Not "runs without erroring".
- [ ] **Deterministic** — same verdict every run (flaky bugs: a pinned, high reproduction rate, per above).
- [ ] **Fast** — seconds, not minutes.
- [ ] **Agent-runnable** — you can run it unattended.

If you catch yourself reading code to build a theory before this command exists, **stop — jumping straight to a hypothesis is the exact failure this skill prevents.** No red-capable command, no Phase 2.

## Phase 2 — Reproduce + minimise

Run the loop. Watch it go red.

Confirm:

- [ ] The loop produces the failure mode the **user** described — not a different failure that happens to be nearby. Wrong bug = wrong fix.
- [ ] The failure reproduces across multiple runs (or, for flaky bugs, at a high enough rate to debug against).
- [ ] You have captured the exact symptom (error text, wrong output, timing) so later phases can verify the fix addresses it.

### Minimise

Once it is red, shrink the repro to the **smallest scenario that still goes red**. Cut inputs, callers, config, data, and steps **one at a time**, re-running the loop after each cut — keep only what is load-bearing.

A minimal repro shrinks the hypothesis space in Phase 3 and becomes the clean regression test in Phase 5.

Done when **every remaining element is load-bearing** — removing any one makes the loop go green.

Do not proceed until you have reproduced **and** minimised.

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.

Each hypothesis must be **falsifiable** — state the prediction it makes:

> "If X is the cause, then changing Y will make the bug disappear / changing Z will make it worse."

If you cannot state the prediction, the hypothesis is a vibe — discard or sharpen it.

**Show the ranked list to the user before testing.** They often re-rank it instantly ("we just changed #3 yesterday") or know what is already ruled out. Cheap checkpoint, big time saver. Don't block on it if the user is AFK — proceed with your ranking and say so.

## Phase 4 — Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** where the environment supports it. One breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Establish a baseline measurement (timing harness, profiler, query plan, `time`), then bisect. Measure first, fix second.

## Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow (a unit test that cannot replicate the chain that triggered the bug), a test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it: the architecture is preventing the bug from being locked down.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 loop against the original (un-minimised) scenario.

## Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or the absence of a seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (grep the prefix)
- [ ] Throwaway harnesses deleted or moved somewhere clearly marked
- [ ] The hypothesis that turned out correct is stated in the commit / PR message — so the next debugger learns

**Then ask: what would have prevented this bug?** If the answer is architectural (no good test seam, tangled callers, hidden coupling), hand off to `improve-codebase-architecture` with the specifics. If it is operational (no health check, silent failure, missing alert), say so plainly. Make the recommendation **after** the fix is in — you know more now than when you started.
