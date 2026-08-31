# peer-debate — for humans

`SKILL.md` is written for the agent and says what to do. This file says why it is built the way it
is, and is deliberately not referenced from `SKILL.md`, so it costs the agent nothing.

Open [`docs/debate-flow.html`](docs/debate-flow.html) in a browser for the control flow.

## What it is

Two instances of one model argue one contestable question under opposed roles. The orchestrating
agent carries every turn between them and judges the result. The point is not to get two answers —
it is to make each side attack the other's reasoning, which surfaces errors that neither would find
alone and that the orchestrator, sharing the question but not the work, would not find either.

## Three decisions worth knowing

**Nobody is running between turns.** Each turn starts a fresh `agy --print` process that exits once
it has answered; what survives is an Agy conversation id, not a resident agent. There is no separate
judge — judging happens inside the orchestrator. The two sides run concurrently only in blind round
0; later turns are relayed in order.

That is also why there is no lock file and none is missing. Nothing polls and nothing can be woken,
so two debaters sharing a file would sit waiting for a writer that never runs. The orchestrator is
the transport.

**The roles are asymmetric on purpose.** Two instances of one model at one temperature agree after
about one round, and that agreement is an artefact of the symmetry rather than a signal of quality.
One side proposes and defends; the other is told to break it. Open dissent is a valid outcome.

**Convergence is not correctness.** Both sides share a training set and therefore share blind spots.
Where they agree on something the judge cannot independently break, the correct move is not another
round — it is a reviewer from a different vendor. That is the third exit in the diagram.

## Usage record

Each Agy result reports cumulative input, output, thinking, cache-read and total tokens for that
side. The driver stamps those counters into `transcript.md`. Agy does not report a monetary cost, so
the transcript makes no cost claim.

## Requirements

Python 3 and `agy`, authenticated with the requested model available. `debate.py check` verifies the
machine before the first turn.

## Where things live

| | |
|---|---|
| Skill and role prompts | this directory |
| Run directories | `~/peer-debates/<date>-<slug>/` — transcript, result, and one `A/` and `B/` working directory per side |
| Session state | Agy conversation ids in `conversation-A.txt` and `conversation-B.txt`; Agy keeps its own history |

## Worked example

The first real run asked how supply droop depends on load position across a 10 × 10 load matrix on a
copper plane pair. Side B computed its static map with the two planes treated as parallel rather than
in series and was out by a factor of four; side A found it, and B conceded only after building an
independent two-sheet model that reproduced the series value exactly. In the following round B found
a further factor-of-two bug in its own inductance extraction that nobody had attacked, and A
withdrew an analytic bound it had misapplied. Neither error would have survived to the answer, and
neither would have been found by one model working alone.
