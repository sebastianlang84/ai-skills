---
name: evaluating-with-promptfoo
description: Run and preserve Promptfoo evaluations with pinned isolated tooling, frozen cases, provider-aware signals, and readable result records. Use when the user names Promptfoo, asks to rerun an existing Promptfoo suite, or chooses Promptfoo for cross-harness prompt, skill, tool-routing, or agent evaluation. Not for generic evaluation with no Promptfoo requirement; pair with autoresearch when tuning.
---

# Evaluating with Promptfoo

Promptfoo is the runner, not the experiment method. When the goal is to improve or tune something,
load `autoresearch` first and let it own the hypothesis, baseline, one-lever rule and keep/discard
decision. This skill owns Promptfoo configuration, execution signals, isolation and evidence layout.

## 1. Recover or freeze the contract

For an existing suite, read its config, case generator, wrapper, latest human summary and canonical
Brain check before changing anything. Re-run the frozen version before editing it when a current
baseline is required.

For a new suite, fix these before the first canonical run:

- question and primary functional outcome;
- positive, negative and near-miss cases;
- assertions, guardrails and invalid-run conditions;
- provider, model, effort, permissions, cache and concurrency;
- repeats and keep/discard rule when the claim is probabilistic;
- locations for raw output and the human-readable result.

Record hashes for cases, configs, prompts or skills under test. A pilot that discovers a
configuration error remains labelled pilot evidence; it does not become the baseline after the
error is silently repaired.

This step is complete when another agent could predict exactly which files and numbers decide the
claim before any output exists.

## 2. Separate outcome from instrumentation

Make task behavior the primary signal whenever possible: expected answer, concept path, hidden
test, valid JSON contract, selected tool or another observable result. Track internal events such
as a skill read, tool call or trace as a separate metric.

Instrumentation is provider-specific. In the measured local skill-routing suite, Claude Code
exposed a first-class `Skill` call, while Promptfoo inferred Codex skill use only from a direct
`SKILL.md` read. Codex can behave correctly from global instructions without that read. Never turn
an absent provider-specific event into a functional failure unless that event is itself the claim.

Use deterministic assertions for deterministic claims. If an LLM judge is unavoidable, ask it at
least one question with known ground truth and discard the judge signal when it fails that
calibration. Do not collapse unlike provider signals into one pass rate.

## 3. Configure the harness explicitly

Prefer structured outputs and file-backed test generation over prose parsing. Give each provider a
stable label containing model and effort. Set `maxConcurrency: 1` for cross-harness comparisons
unless concurrency is the lever under test, and use one fresh agent thread per case.

For local Codex/Claude harness behavior, start from the working provider configurations in
`~/dev/wasti-research/programs/skill-descriptions/` rather than silently replacing subscription
auth with API-key providers. Keep runtime-specific options inside separate provider configs; the
case set and functional assertions should remain shared where their semantics are shared.

Promptfoo can write prompts, variables, outputs and configuration into exports. Keep sharing off in
both config and CLI, disable telemetry, and write results only to an explicit local path:

```bash
PROMPTFOO_DISABLE_TELEMETRY=1 \
PROMPTFOO_DISABLE_UPDATE=1 \
promptfoo eval -c <config> --no-cache --no-share --output <run.json>
```

Pin Promptfoo and provider SDK versions. Reuse a repo-owned isolated wrapper when one exists. If a
new package download is needed, obtain the required approval, install into a temporary prefix with
scripts disabled, and keep Promptfoo out of the global toolchain and CI until a separate adoption
decision changes that boundary. Never invoke `promptfoo share` for these local studies.

Configuration is complete when provider auth surface, permissions, network access, sharing,
telemetry, cache, concurrency, model and effort are explicit rather than inherited guesses.

## 4. Run without rewriting history

Run providers separately when that makes failures and usage attributable. Preserve stdout/stderr,
exit status and the raw JSON even when a run fails. A retry gets a distinct artifact or an explicit
retry record; it does not overwrite the failed evidence.

Validate that every expected case produced one parseable result, provider labels match the frozen
config, assertions actually executed, and no cache supplied a supposedly fresh run. Report tokens,
cost and duration as separate fields; subscription utilization is not inferable from Promptfoo's
local dollar estimate.

One successful run proves the harness can execute. It does not establish a stable invocation rate
or quality difference; use the frozen repeat count before making that stronger claim.

## 5. Preserve two layers

The research repository owns reproducibility:

```text
programs/<study>/
  cases or generator
  provider configs
  pinned runner
  runs/YYYY-MM-DD/raw outputs
  runs/YYYY-MM-DD/summary.md
```

The summary records question, setup, versions, hashes, result table, cost/tokens, limitations,
invalid pilots, verdict and exact re-run command. Secret-scan export files before committing them;
best-effort provider redaction is not a proof that an export is safe.

The Brain owns the durable conclusion. Use `using-brain` to add or update one `Attested
Computation`, then add one row to `checks/promptfoo/index.md`. Link to raw evidence; do not copy raw
JSON, complete prompts or transcripts into the Brain.

## Completion

Stop only when:

- the frozen inputs and runtime are identifiable by version or hash;
- raw outputs parse and account for every expected case;
- functional and instrumentation metrics are reported separately;
- invalid pilots and retries cannot be mistaken for the canonical run;
- the research summary contains the re-run command;
- the Brain result index points to the canonical check and raw location;
- relevant repo checks and secret scans pass.

Current local readout: `~/.agents/brain/checks/promptfoo/index.md`.
