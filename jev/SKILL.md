---
name: jev
description: Ask Jev, a cheap and fast OpenRouter decision model, for typed decisions with probabilities instead of text — classify, route, screen, score, or check a condition. Use when code needs a semantic judgement from a known answer space (a class, yes/no, an ordinal score), especially over many items or inside a loop where an LLM call is too slow or costly; when choosing a threshold for a pre-filter; or when the user asks what Jev is or where it fits. Not for writing, summarising, research, open-ended answers, or verdicts that need a reason.
---

# Jev

Jev (`typesafe/jev-1.13` from TypeSafe AI, OpenRouter Decisions API) is a decision model, not a
text model. The caller passes a JSON `state` and predefined questions; Jev returns a typed answer
with probabilities for each question. It never writes text or a reason, and it cannot answer
outside the answer space the caller defined.

```text
LLM: unstructured input -> generated text
Jev: state + questions with fixed answer spaces -> typed decisions + probabilities -> code decides
```

Think of it as an `if` whose condition is a semantic judgement:
`if p("transaction looks suspicious") > 0.95: ...`. It reads text and JSON only, up to 32k input
tokens, and bills input only (0.042 $ per million tokens). Measured here: about 0.00003 $ and a
median of 340 ms per item with two questions per call.

"Zero hallucinations", as TypeSafe puts it, only means the output always fits the schema. Jev can
still pick the wrong option or misjudge a probability.

## When to use it

First check whether a rule or script decides it: a regex, a keyword list, a number check. In
Market Digest a fixed rule (number + named subject + valuation word) picked web-verification
targets as well as Jev did, so Jev was dropped there. Jev earns its place only when the judgement
needs meaning that surface features miss.

Good fits are decisions a knowledgeable person could make in a few seconds with the right context,
where the answer space is known in advance:

- **Classify and route:** tickets, mails, documents, user intent, which tool or sub-agent gets a
  request (`choice`).
- **Score and rank:** severity, urgency, relevance, quality of an LLM output, re-ranking search or
  retrieval candidates (`score`, or several `noul`).
- **Guardrails and checks:** personal data present, prompt injection, policy violation, a tool call
  that looks implausible, an answer that misses the question (several `noul` in one call).
- **Bulk work:** labelling or enriching large record sets, where a frontier model is too slow or
  too expensive. The default cap covers about 900 items a day at the measured cost; more needs a
  raised cap (see Budget).

It pays off when volume or latency matters, when a probability is useful (threshold, sort, send
uncertain cases to a stronger model or a person), and when a wrong "keep" is cheap because a
stronger step follows.

Do not use it for anything generative: writing, summarising, explaining, code, research,
multi-step reasoning. Do not use it for a verdict that needs a justification, a comparison across a
whole pool, or a handful of decisions a day, where the saving does not matter. On labels alone a
general LLM (gpt-6-luna, MiMo Flash) did about as well; choose Jev for probability, price and speed.

### Measured in Market Digest

On 160 curator points
(`~/dev/market-digest/docs/measurements/20260924-jev-klassifizierung.md`):

- Jev agreed with each of two model references on 78 % of points. The references agreed with each
  other on 91 %.
- Every Jev error on points where both references agreed was an over-flag.
- At p(none) ≥ 0.7, Jev dropped 52 % of points and lost none of the 26 findings either reference
  saw.

So in Market Digest it serves as a pre-filter, not a judge. Status and reversal conditions:
`~/.agents/brain/decisions/tool-candidates/jev.md`.

## How to call it

- **MCP:** tool `jev_decide` on server `jev`, registered in Claude Code and Codex. Code:
  `~/.agents/mcp/jev/server.py`.
- **Python:** put `~/.agents/mcp/jev` on `sys.path` and call
  `jev_client.decide(state, questions, label="<job>")`. Use this for batches. A
  `ThreadPoolExecutor(6)` with a few retries on `JevError` handled 160 items.

```python
QUESTIONS = {
    "finding": {
        "type": "choice",
        "instructions": "For a private investor, what does this point amount to for one specific title?",
        "criteria": {
            "buy_opportunity": "Argues one specific asset is attractively priced now, citing a discount or entry level.",
            "crash_risk": "Names a concrete, sizable downside risk for one specific company or asset.",
            "new_title": "Introduces one specific asset as a new idea worth researching, without a stated discount.",
            "broken_thesis": "Says the case for one specific asset has changed or broken, or the speaker trims because of it.",
            "none": "Anything else: recap, macro commentary, facts without consequence for one title.",
        },
    },
}
result = jev_client.decide({"channel": ch, "point": text}, QUESTIONS, label="curator-screen")
# result == {"model": "typesafe/jev-1.13-20260917",
#            "answers": {"finding": {"type": "choice", "choice": "buy_opportunity",
#                                    "probabilities": {...}, "confidence": 0.97}},
#            "usage": {"input_tokens": 781, "cost": ...}}
```

| type | criteria | answer |
| --- | --- | --- |
| `choice` | `{option: one-line description}`, 2 to 255 options | `choice`, `probabilities`, `confidence` |
| `noul` | `{"true": ..., "false": ...}` | probability that the statement is true |
| `score` | ordered levels, low to high, 2 to 10 levels | probability per level and their weighted position (e.g. 1.43), `confidence` |

The measured criteria are in
`~/ai_stack_data/newsletter-writer/quality-pdca/jev-20260924/questions_t1.py`.

The client only checks that every question got an answer. It does not check the fields inside an
answer, so treat an answer without `probabilities`, or a `noul` answer without a probability, as no
answer.

Store the top-level `result["model"]` with your results. It names the snapshot OpenRouter served,
and the client does not compare it with the requested version.

## Writing good questions

- Split a big decision into small, atomic questions and combine the answers in code. For example,
  ask "is the event covered?", "is the evidence consistent?" and "are documents missing?" instead of
  "approve this claim?". Jev answers all questions of one call independently against the same
  state, and the input is billed once.
- Write every option as one line and make the options mutually exclusive. Add an explicit
  "none"/"anything else" option, or Jev forces items into a real class.
- In a screen, list every class that must survive. An item whose class is missing lands in "none"
  and is dropped without any error.
- Keep `state` small and relevant. The first few hundred characters of a claim were enough.
- Set thresholds from what each error costs, and check them on labelled items from your own use
  case. Do not pick round numbers. A typical pattern: act automatically above a high confidence,
  check further in the middle band, and hand the rest to a stronger model or a person.

## Budget and safety

- Jev has its own ledger, `~/.agents/state/jev/budget.sqlite3`, with a default cap of 0.03 €/day
  (`JEV_DAILY_LIMIT_EUR`), so it cannot take budget from the GLM source preparation.
- Raising the cap or adding a recurring job needs Sebastian's approval, because metered API spend
  is an exception here.
- The cap applies to each ledger file separately. An evaluation with its own `JEV_LEDGER` adds to
  the day's spend instead of sharing the cap, so state its expected cost beforehand and report the
  actual cost afterwards.
- `decide` sends only `typesafe/jev-1.13` and rejects any other model name, because the budget
  reservation is priced for it. OpenRouter may still serve a newer snapshot under that name. If
  the price or the snapshot changes, update `jev_client.py` and re-check the thresholds.
- TypeSafe gives 70–500 ms latency and the price as early-access figures, which may change.
- The key comes from `OPENROUTER_API_KEY` or the market-digest `.env`. It is never printed or
  returned, and `JevError` messages have the key redacted.
