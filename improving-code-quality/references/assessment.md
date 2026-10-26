# Assessment questions

## Principles and tradeoffs

| Principle | Question | Limit |
|---|---|---|
| KISS — keep it simple | What is the simplest correct design across this flow? | Fewer lines or layers may hide work or distribute it into callers. |
| YAGNI — you aren't gonna need it | Does this capability serve a current requirement? | Necessary reliability, tests and maintainability are current needs, not speculative features. |
| AHA — avoid hasty abstractions | Do the actual use cases justify one shared contract? | Temporary duplication is preferable to an abstraction that bends unrelated cases together. |
| DRY — don't repeat yourself | Is the same business rule maintained independently in several places? | Similar code with different reasons to change need not be unified. |
| CUPID — composable, Unix philosophy, predictable, idiomatic, domain-based | Does this part have a clear purpose, work well with others, behave predictably, follow local idioms and reflect the domain? | These are contextual properties, not a rule to split everything into tiny functions. |

Required behavior and reliability come first. Prefer lower total complexity across implementation
and consumers; justify added complexity with current needs and observed benefits. No universal
function-length, parameter-count, file-size, inheritance, or dependency target applies.

## Whole-flow inspection

1. What outcome does the user actually need, and does the entry point produce it all the way to the
   consumer? Distinguish unused work from work whose output has an external or dynamic consumer.
2. Where is each business rule authoritative? Do separate implementations disagree, or merely look
   similar? Can existing behavior be reused without coupling unrelated policies?
3. Which boundaries hide meaningful work, and which merely forward arguments, translate the same
   representation repeatedly, or expose internals that callers must understand?
4. Which input reads, queries, process starts or model calls repeat unnecessarily? Does batching,
   caching or hoisting preserve freshness, ordering, failure timing and resource ownership?
5. Are retries, locking, validation and cleanup still required? Does an apparent fallback hide an
   error by turning failure into an empty success? Preserve required safeguards and separate any
   intentional failure-policy correction from simplification.
6. Do tests exercise observable contracts and relevant integration paths, or mirror implementation?
   Will a change remain correct for empty inputs, partial failures and all affected consumers?

These questions guide investigation; findings outside this list still count. A suspicious pattern
is not itself evidence of harm. Follow data and actual use rather than inferring behavior from names.

## Measuring a claim

Freeze the input set, expected behavior, environment and primary measure before editing. Use the
same representative workload before and after; keep warmup and caching conditions comparable and
choose a fixed repeat count before seeing results. Select the relevant measure: elapsed time,
throughput, peak memory, I/O, external calls or cost, with correctness and resource limits as guards.

Count the whole affected flow, including retries and work moved to callers. A reduction in one API
call count does not establish faster execution or lower monetary cost. Report measured values,
variation, scope and remaining uncertainty; a noisy difference is inconclusive. A network outage or
quota failure is not a baseline quality deficit. Never shorten input, drop records, weaken error
handling or reduce output quality merely to improve a timing.

For maintenance claims, identify which independently maintained decisions disappear and why the
consumers become easier to change. A fixed follow-up task can test that claim; line count alone
cannot. Test only what the claim needs, not a generic benchmark for every edit.

## Sources

These explain the design principles, not the effectiveness of this skill:

1. [AHA Programming](https://kentcdodds.com/blog/aha-programming) — premature abstraction and shared use cases.
2. [YAGNI](https://martinfowler.com/bliki/Yagni.html) — speculative features versus keeping software changeable.
3. [CUPID](https://dannorth.net/blog/cupid-for-joyful-coding/) — properties and contextual tradeoffs.
