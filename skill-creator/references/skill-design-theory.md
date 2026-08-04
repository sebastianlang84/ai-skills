# Skill Design Theory

Why a skill works, as opposed to how this repo structures one. Read it when writing a new skill, when an existing one fires unreliably, or when one has grown and you need a principled way to cut it.

Adapted from Matt Pocock's `writing-great-skills` and its glossary (MIT, github.com/mattpocock/skills).

A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same *process* every run, not producing the same output — is the root virtue. A brainstorming skill should predictably diverge; its tokens vary, its behaviour does not. Every lever below serves that.

## Invocation: two costs, no free option

**Model-invoked** keeps the `description`, so the agent can fire the skill on its own and other skills can reach it. The description sits in the context window on every turn — that is **context load**.

**User-invoked** (`disable-model-invocation: true`) strips it from the agent's reach: only the human typing `/name` can start it. The description becomes human-facing, a one-line summary. That buys **cognitive load** instead: *you* are now the index that has to remember the skill exists.

Neither is free. Pick model-invocation only when the agent must reach the skill autonomously, or another skill must. If it only ever fires by hand, make it user-invoked. Reserve it especially for skills that send, publish, delete, or install something — those should never fire on an inferred intent.

When user-invoked skills multiply past what you can hold in your head, the cure is a **router skill**: one user-invoked skill that names the others and says when to reach for each.

> On this machine the invocation keys are Claude Code extensions. `quick_validate.py` accepts them and flags the skill as Claude-Code-specific; other harnesses ignore them.

## Writing the description

A model-invoked description does two jobs: state what the skill is, and list the **branches** that should trigger it. Every word is paid on every turn, so it earns harder pruning than the body.

- **Front-load the leading word.** The first few words do the invocation work.
- **One trigger per branch.** Synonyms that rename one branch are duplication: "build features using TDD … asks for test-first development" is a single branch written twice.
- **Cut identity already in the body.** The description is triggers, plus any "when another skill needs…" clause.

## Information hierarchy

Skill content is either **steps** (ordered actions) or **reference** (definitions, rules, facts consulted on demand), and each sits on one of three rungs:

1. **In-skill step** — the primary tier: what the agent does, in order.
2. **In-skill reference** — consulted while working. Often a legitimately flat peer-set, not a smell.
3. **External reference** — pushed into a separate file, reached by a pointer, loaded only when the pointer fires.

**Progressive disclosure** is the move down that ladder. It is licensed by **branching**: inline what every path needs, disclose what only some paths reach. A pointer's *wording*, not its target, decides when and how reliably the agent follows it — a must-have behind a weakly worded pointer is a variance bug. Fix the wording first; inline only if that fails.

**Co-location** decides what sits *beside* a piece once placed: keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours.

## Completion criteria

Every step ends on a condition that tells the agent it is done. Two independent properties make it a lever:

- **Clarity** — can the agent tell done from not-done? A vague bound ("understanding reached") lets attention slip to *being done*.
- **Demand** — how much it requires. "Every modified model accounted for" forces thorough work where "produce a change list" does not.

Demand also binds flat reference, which is how a skill with no steps still carries an exhaustiveness bar ("every rule applied"). The strongest criteria are both checkable and exhaustive.

## Leading words

A **leading word** is a compact concept already in the model's pretraining that the agent thinks *with* while running the skill: *tight*, *red*, *seam*, *tracer bullet*, *fog of war*. Repeated as a token — never restated as a sentence — it accumulates a distributed meaning and anchors a whole region of behaviour in very few tokens.

It pays twice. In the body it anchors execution: the agent reaches for the same behaviour every time the word appears. In the description it anchors invocation: when the same word lives in your prompts and your code, the agent links that shared language to the skill and fires it more reliably.

Coining your own works only if you define it, and a made-up word recruits no priors — you pay in definition tokens what a pretrained word gives free. Reach for an existing word first. Hunt for passages that collapse into one: a triad spelled out three times ("fast, deterministic, low-overhead" → *tight*), a fuzzy gate that wants to be a binary state ("a loop you believe in" → the loop goes *red*).

## Failure modes

Use these to diagnose a skill that is not behaving.

- **Premature completion** — a step ends before it is genuinely done. Sharpen the completion criterion first; only if it is irreducibly fuzzy *and* you observe the rush, split the sequence so the later steps are out of view.
- **No-op** — a line the model already obeys by default, so you pay load to say nothing. The test: does it change behaviour versus the default? Model-relative, not reader-relative — settle disagreements by running the skill, not by arguing. A leading word too weak to beat the default is a no-op; the fix is a stronger word, not a different technique.
- **Negation** — steering by prohibition backfires. *Don't think of an elephant* names the elephant and makes it more available. Prompt the positive: state the target behaviour so the banned one is never spoken. Keep a prohibition only as a hard guardrail you cannot phrase positively — a destructive command, an irreversible action — and even then pair it with what to do instead.
- **Negative space** — the steering done by what you leave out. Every decision a skill declines to make is delegated to the agent's priors, not left neutral. Read a draft for its silences and decide each one: fill it, or leave it open as a real branch.
- **Duplication** — one meaning with more than one home. Costs maintenance and tokens, and inflates that meaning's rank on the ladder. The accidental inverse of a leading word, which repeats a *token* on purpose, never the meaning.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.
- **Sprawl** — simply too long, even when every line is live and unique. Cure with the hierarchy: disclose reference, split by branch.

## Pruning pass

Run this before calling a skill done:

1. Does each line still bear on what the skill does, or has the world moved?
2. Run the no-op test **sentence by sentence**, not line by line. When a sentence fails, delete the whole sentence rather than trimming words from it. Be aggressive — most prose that fails should go, not be rewritten.
3. Does each meaning have exactly one home?
4. Is every prohibition either phrased positively or a genuine hard guardrail?
5. Would a leading word retire a paragraph?
