---
name: diagnosing-bugs
description: 'Disciplined diagnosis loop for hard bugs, flaky failures, and performance regressions — build a tight failing feedback loop before forming any hypothesis. Use when the user says "debug this"/"diagnose", when a bug survived a first fix attempt or its cause is unclear after reading the code, for intermittent failures, or for performance regressions. Not for an ordinary bug with a clear reproduction: a direct fix with a regression test does as well there at lower cost.'
---

# Diagnosing Bugs

Three steps. Everything else is your ordinary judgement.

1. **Reproduce first.** Before changing any code, get a signal that goes red on *this* bug — a
   failing test, a command with a fixture input, a replayed payload. For a flake, raise the
   reproduction rate (loop it, add load or delay) until it is reliable. If reproduction is
   impractical (production-only data, hardware or timing), fix from the strongest evidence you have
   (dump, trace, logs), validate what you can, and say plainly that the bug was not reproduced.
2. **Make that signal the regression test** where one exists. Keep the reproduction as a test at
   the seam where the bug lives, red before the fix and green after. Run it, then the surrounding
   suite.
3. **Change nothing outside the fix.** No reformatting, line-ending changes, changelog rewrites or
   unrelated cleanups; the diff holds the fix and its test, plus the docs the change itself requires.

Why only these: measured 2026-11-03 on Opus 5.5 and gpt-6.1-sol (Brain `checks/skill-effect-ab.md`),
the former long version of this skill did not improve fix correctness, even on a hard bug; its one
effect was a regression test, and one run rewrote a whole changelog. Originally adapted from Matt
Pocock's `diagnosing-bugs` skill (MIT, github.com/mattpocock/skills).
