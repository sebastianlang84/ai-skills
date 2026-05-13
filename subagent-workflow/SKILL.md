---
name: subagent-workflow
description: Use when dispatching subagents. Covers whether to delegate, role workflow, handoffs, review expectations, and allowed local provider/model routing in one compact policy.
---

# Subagent workflow

Use this skill before dispatching subagents. Skip subagents for tiny, clear, local tasks.

## Core rules
- Main agent owns orchestration, final judgment, writes by default, and the user-facing summary.
- Use subagents for context isolation, compression, bounded implementation, or independent review.
- Do not use subagents as a default team simulation.
- Prefer read-only subagents unless a bounded worker is explicitly useful.
- Avoid skill-token cascades: main may read workflow/reference skills, but subagents should not read additional skills unless the dispatch prompt explicitly says so.

## Workflow choices
- Small/clear task: no subagent.
- Context gathering only: `scout`.
- Risky/ambiguous decision check before action: `oracle`.
- Implementation task: `scout -> worker -> reviewer`.
- Large, risky, cross-cutting, or ambiguous task: `scout -> planner -> oracle -> worker -> reviewer` when a decision challenge would reduce risk.
- Lightweight parallel read-only work: use up to 4 disjoint lanes when justified, usually `2x scout + 2x reviewer`; prefer fewer if the split is weak.

## Roles
- `scout`: read-only facts-first reconnaissance; produce a compact worker-ready brief with uncertainties and stop conditions.
- `oracle`: read-only decision challenger; reconstruct the contract, find hidden assumptions/drift, and recommend the safest next move before risky action.
- `planner`: read-only strategy pass for risky or ambiguous tasks; produce a bounded plan faithful to scout evidence.
- `worker`: bounded implementation only; minimal reviewable changes; stop instead of guessing outside scope.
- `reviewer`: read-only final check against the original task, scope, diff/context, verification, and policy conflicts.

## Handoffs
- Main agent gives each subagent goal, scope, exclusions, success criteria, allowed files/tools, stop conditions, and budget limits.
- Inline only the compact runtime rules the subagent needs; do not tell subagents to load broad skills unless that is the task.
- Subagents hand back compressed findings/plans/results, not raw transcript dumps.
- Reviewer checks the original request, not only the worker brief, and reports concise severity-tagged findings.

## Budgets and context discipline
- Prefer explicit budgets in dispatch prompts: max tool calls, allowed paths, allowed commands, output line limit, and whether CodeMap is allowed.
- Default lightweight budget: up to 4 tool calls for a scout/reviewer, up to 2 CodeMap queries, max 25-40 output lines.
- Do not let subagents crawl broad home/system paths, session history, or unrelated repos unless explicitly in scope.

## CodeMap / repo navigation tools
- Use CodeMap when it is available and useful for codebase understanding, symbol/file discovery, execution-flow hints, impact review, or repo navigation.
- Before dispatching a subagent for codebase work, check whether the target agent's `tools:` include `codemap_status`, `codemap_index`, `codemap_search`, or `codemap_context`; Pi extensions may not be exposed to subagents unless listed there.
- If CodeMap is available to the subagent, explicitly allow it in the dispatch prompt, ask it to run `codemap_status` first, and refresh with `codemap_index` when the index is stale and mutation is acceptable for the task.
- If CodeMap is not available to the subagent, do not assume it can use it: either use CodeMap in the main agent and pass compact findings, or fall back to bounded `rg`/`read` instructions.
- Keep `rg`/`read` for exact text, config, logs, and small local lookups; prefer CodeMap for semantic/symbol-oriented exploration.

## Local agent files
- Global subagents live at `~/.pi/agent/agents/<name>.md`.
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
