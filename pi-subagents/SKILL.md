---
name: pi-subagents
description: "Use when Pi subagent orchestration needs more than the subagent tool's built-in prompt guidance: role selection, multi-step handoffs, local agent-file/tool/model checks, CodeMap availability, or review discipline. Do not use for tiny/local tasks where the tool metadata is sufficient."
---

# Pi Subagents

Use this skill for **Pi-specific** subagent orchestration policy. The `subagent` extension already injects compact always-on guidance for when to delegate, how to phrase delegated prompts, and when to use single/parallel/chain modes. Do not repeat that baseline unless a task needs the deeper rules below.

## When this skill adds value

Load this skill when you need one of these Pi-specific decisions:

- choosing among local roles (`scout`, `oracle`, `planner`, `worker`, `reviewer`)
- checking local agent files, declared tools, model routing, or project-agent trust
- deciding a multi-step handoff/review workflow for risky or cross-cutting work
- controlling context budgets, CodeMap availability, or subagent crawl scope
- reviewing whether a subagent result satisfies the original user request

For tiny, clear, local tasks: do not delegate and do not load more subagent policy.

## Orchestration rules

- Main agent owns orchestration, final judgment, writes by default, and the user-facing summary.
- Prefer read-only subagents unless a bounded `worker` is explicitly useful.
- Avoid skill-token cascades: main may read workflow/reference skills, but subagents should not read additional skills unless the dispatch prompt explicitly says so.
- Do not use subagents as a default team simulation.

## Workflow choices

- Context gathering only: `scout`.
- Risky or ambiguous decision check before action: `oracle`.
- Non-trivial implementation: `scout -> worker -> reviewer`, or main-agent implementation between scout and reviewer.
- Large, risky, cross-cutting, or ambiguous work: `scout -> planner -> oracle -> worker -> reviewer` when a decision challenge would reduce risk.
- Lightweight independent checks: use up to 4 disjoint lanes when justified; prefer fewer if the split is weak.

## Local roles

- `scout`: read-only facts-first reconnaissance; compact worker-ready brief with uncertainties and stop conditions.
- `oracle`: read-only decision challenger; reconstruct the contract, find hidden assumptions/drift, recommend the safest next move.
- `planner`: read-only strategy pass for risky or ambiguous tasks; produce a bounded plan faithful to evidence.
- `worker`: bounded implementation only; minimal reviewable changes; stop instead of guessing outside scope.
- `reviewer`: read-only final check against original task, scope, diff/context, verification, and policy conflicts.

## Handoff and budget discipline

- Give subagents only the task-specific policy they need; do not tell them to load broad skills by default.
- Include explicit scope, exclusions, allowed paths/tools, stop conditions, command/tool-call budget, and output shape.
- Default lightweight budget: up to 4 tool calls for a scout/reviewer, up to 2 CodeMap queries, max 25-40 output lines.
- Do not let subagents crawl broad home/system paths, session history, or unrelated repos unless explicitly in scope.
- Reviewer checks the original request, not only the worker brief, and reports concise severity-tagged findings.

## CodeMap / repo navigation tools

- Before dispatching a subagent for codebase work, check whether the target agent's `tools:` include `codemap_status`, `codemap_index`, `codemap_search`, or `codemap_context`; Pi extensions may not be exposed to subagents unless listed there.
- If CodeMap is available to the subagent, explicitly allow it in the dispatch prompt, ask it to run `codemap_status` first, and refresh with `codemap_index` only when mutation is acceptable for the task.
- If CodeMap is not available to the subagent, use CodeMap in the main agent and pass compact findings, or fall back to bounded `rg`/`read` instructions.
- Keep `rg`/`read` for exact text, config, logs, and small local lookups; prefer CodeMap for semantic/symbol-oriented exploration.

## Local agent files

- Global subagents live at `~/.pi/agent/agents/<name>.md`.
- Project subagents live at `.pi/agents/<name>.md` and are repo-controlled prompts; use project scope only for trusted repos.
- Agent frontmatter must include `name` and `description`.
- `model` is passed as `--model` to a new Pi process.
- `tools` is a comma-separated string such as `tools: read, bash` or `tools: read, bash, codemap_status, codemap_index, codemap_search, codemap_context`; do not use YAML list syntax.
- Do not rely on unsupported frontmatter fields like `thinking` or `reasoning`.

## Provider/model routing

- Before dispatch, read the target agent file and verify its `model:`.
- Only dispatch OpenAI Codex OAuth-backed subagents: model must match `openai-codex/gpt-*`.
- Do not append reasoning suffixes such as `:high`, `:medium`, `:low`, `:minimal`, or `:xhigh` to subagent model strings unless explicitly requested for a one-off test.
- If no compliant agent exists, say so and do not dispatch.
- Preferred local routing:
  - `scout`: `openai-codex/gpt-5.4-mini`
  - `oracle`: `openai-codex/gpt-5.5`
  - `planner`: `openai-codex/gpt-5.5`
  - `worker`: `openai-codex/gpt-5.5`
  - `reviewer`: `openai-codex/gpt-5.5`

## Anti-patterns

- Delegating tiny tasks.
- Letting `scout`, `planner`, or `reviewer` write code.
- Sending vague prompts without scope, budgets, and stop conditions.
- Skill cascades where a subagent reads multiple broad skills instead of receiving compact instructions.
- Treating worker output as final without main-agent review.
