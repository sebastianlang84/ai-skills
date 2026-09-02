---
name: peer-debate
description: Answers an open, contestable question by making two independent model instances — one model on both sides, or two vendors via agy and codex — argue it out under asymmetric roles until they converge or hit a round cap, then adjudicating the result. Use when the user wants a question debated, stress-tested by two agents, worked out by a duo, or says "let two models argue this", "have them discuss until they agree", "peer debate", or in German „lass das ausdiskutieren", „zwei Modelle sollen sich einigen". Not for critiquing a finished artifact — one reviewer against an existing document or diff is adversarial-model-review. Not for interrogating the user's own thinking (grilling), and not for defect scans of a codebase (codebase-review).
---

# Peer debate

Two independent model instances argue one question — by default two instances of one model, or
one side on `agy` (Gemini) and the other on `codex` (GPT) when the user wants two vendors. You are
the transport between them and the judge of what they produce. The script moves turns; it decides
nothing.

## When this is the wrong tool

- The question has one right answer that a calculation settles → just calculate it.
- There is an artifact to review → `adversarial-model-review`, one reviewer, different vendor.
- The disagreement is with the user, not within the material → `grilling`.

## Procedure

### 1. Write the question down

Put the question in a file. It must be contestable and it must be closed enough to be wrong: a
question no answer can fail is not debatable.

State in the question what a finished answer looks like — a number, a decision, a ranked list.
Without that the two sides converge on an essay.

### 2. Check the machine once

```bash
python3 ~/.agents/skills/peer-debate/scripts/debate.py check
```

It names what is missing rather than failing mid-turn: each configured cli on `PATH`, an agy model
actually listed, and both role prompts present. Python 3 plus `agy` and/or `codex` are the only
requirements. A codex model id cannot be verified before round 0; a refused one fails round 0
loudly (measured 2026-09-02: `gpt-5.4-terra` is refused under a ChatGPT account, `gpt-5.6-terra`
runs).

### 3. Open the run

```bash
python3 ~/.agents/skills/peer-debate/scripts/debate.py init <slug> <question-file>
```

This creates `~/peer-debates/<date>-<slug>/` and puts the question to both sides blind — neither
sees the other in round 0, so neither is anchored by the other's framing. The two run
**concurrently**, since nothing connects them in round 0; the opening therefore costs the slower
side's wall clock, not the sum. Both replies land in `transcript.md`.

### 4. Run rounds

```bash
python3 ~/.agents/skills/peer-debate/scripts/debate.py round <slug>
```

One call is one exchange: A answers B's latest, then B answers A's. Stop as soon as both final
`STATUS:` lines say `converged`; otherwise cap the run at four exchanges after blind round 0. If
they have not converged by then, the dissent is the result — record it and decide yourself.

Inject a correction at any point, addressed to one side:

```bash
python3 ~/.agents/skills/peer-debate/scripts/debate.py ask <slug> A "You asserted X without computing it."
```

The message is labelled as the orchestrator's before it is sent. Without that label an injection
reads exactly like the opponent's next move, and a side that concedes to it has had a premise
installed rather than tested.

Use this when both sides drift onto a shared false premise. They share a model and therefore share
blind spots; when both agree on something unverified, that agreement is the thing to attack.

### 5. Judge before accepting

Convergence is not correctness. Two instances of one model agree readily and the agreement carries
no independent evidence. Before you hand the result on:

- Read the `STATUS:` line each side ends on first. It names whether anything is still open and
  what, and it tells you whether another round is worth its wall clock before you read the turn.
- Recompute the headline numbers yourself. Do not accept a figure you have not reproduced.
- Check that every concession is real — a side that conceded and kept its conclusion conceded
  nothing.
- Check that no missing input was silently invented. If the question was underdetermined, the
  honest result names the missing input.

Then take one of three exits, and say which:

- **Accept.** The result holds and you reproduced its headline numbers. Hand it on.
- **Re-debate, narrowed.** Something specific is still contested. Put that one quantity back to both
  sides with `ask`, not the whole question again — a second full round re-litigates what is already
  settled and buries the open point.
- **Escalate to an adversarial review by a different vendor's model.** Take this exit when both
  sides agree on a premise you cannot break yourself. Two instances of one model share a training
  set and therefore share blind spots, so their agreement is exactly where an independent
  cross-vendor reviewer earns its cost. Nothing here depends on how that review is run.

## Configuration

Every value below is an environment variable with a default.

| Variable | Default | Meaning |
|---|---|---|
| `PEER_DEBATE_ROOT` | `~/peer-debates` | where run directories are created. Point it elsewhere to keep a debate's record beside the thing it is about |
| `PEER_DEBATE_MODEL` | `agy:gemini-3.8-flash-medium` | model both sides run, as `<cli>:<id>` with cli `agy` or `codex`; a bare id means agy. `agy models` lists agy ids |
| `PEER_DEBATE_MODEL_A`, `PEER_DEBATE_MODEL_B` | unset | model for one side; set both to put two vendors against each other, e.g. `A=agy:gemini-3.8-flash-medium B=codex:gpt-5.6-terra` |
| `PEER_DEBATE_EFFORT` | `medium` | reasoning effort for both sides (`PEER_DEBATE_EFFORT_A`/`_B` per side) |
| `PEER_DEBATE_TIMEOUT` | `3600` | seconds per turn; a turn that hits it is killed and reported, not recorded |

What each side runs is written to `sides.json` at `init` and read by every later turn, so a
changed environment cannot swap a model mid-debate.

**Two vendors change what convergence means.** With one model on both sides, agreement carries no
independent evidence and the third exit below (cross-vendor review) exists for that reason. With
agy against codex the sides no longer share a training set, so their agreement is worth more and
their dissent is more often a real open point than a role artefact; the roles stay asymmetric
regardless.

**Material the debaters cannot reach.** They run as processes on this host and see only this host.
When the subject lives elsewhere — another machine, a share nobody has mounted, a system behind a
login — put a read-only copy somewhere local, point the question at that path, and tell both sides
not to modify it. A debate over a source neither side can open produces opinions.

Each side runs in its own subdirectory of the run — `A/` and `B/` — and can write and execute
there. That is deliberate: a debate in which nobody computes anything is an exchange of opinions.

### Tool policy

Both sides receive their cli's complete configured tool surface. The runner uses
`--dangerously-skip-permissions` on agy and `--dangerously-bypass-approvals-and-sandbox` on codex so
headless turns can use shell, files, web and MCP without soft denials or interactive pauses; it
deliberately enables no sandbox on either. Codex turns run with `features.hooks=false`: the
SessionEnd hook on this host compacts a thread after every `exec` and holds its writer lock for
minutes, and a resume inside that window fails. The role
prompts still require debate artifacts to stay under `A/` or `B/`. This broad grant is a conscious
choice for this private experiment host. Details: [`references/tool-policy.md`](references/tool-policy.md).

The two sides receive different binding role instructions in their first Agy turn
(`assets/role-proposer.md`, `assets/role-refuter.md`). That asymmetry is the mechanism: symmetric
roles produce agreement after one round, and that agreement is an artefact of the symmetry.

## Files

Run directory `~/peer-debates/<date>-<slug>/`:

- `question.md` — as put to both sides
- `sides.json` — cli, model and effort per side, fixed at `init`
- `environment.md` — the real current date, platform, cli versions, model per side, execution
  policy, capacity and numeric libraries. Each side receives a copy for round 0.
- `transcript.md` — every turn, timestamped and stamped with cli, model, effort and token counters
  (agy: cumulative for that side; codex: this turn).
- `conversation-A.txt`, `conversation-B.txt` — the side's persistent agy conversation id or codex
  thread id
- `last-A.md`, `last-B.md` — each side's latest, what the next turn relays
- `A/`, `B/` — one working directory per side, and what each wrote while computing. They are
  separate on purpose: in a shared directory the second side can read the first side's scripts and
  reply, which makes round 0 blind in name only.

Each turn starts one `agy --print` or `codex exec` process and resumes the side's stored id. There
is no resident debater process and no lock file.
