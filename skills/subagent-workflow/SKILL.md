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

## Workflow choices
- Small/clear task: no subagent.
- Context gathering only: `scout`.
- Implementation task: `scout -> worker -> reviewer`.
- Large, risky, cross-cutting, or ambiguous task: `scout -> planner -> worker -> reviewer`.
- Lightweight parallel read-only work: use up to 4 disjoint lanes when justified, usually `2x scout + 2x reviewer`; prefer fewer if the split is weak.

## Roles
- `scout`: read-only facts-first reconnaissance; produce a compact worker-ready brief with uncertainties and stop conditions.
- `planner`: read-only strategy pass for risky or ambiguous tasks; produce a bounded plan faithful to scout evidence.
- `worker`: bounded implementation only; minimal reviewable changes; stop instead of guessing outside scope.
- `reviewer`: read-only final check against the original task, scope, diff/context, verification, and policy conflicts.

## Handoffs
- Main agent gives each subagent goal, scope, exclusions, success criteria, allowed files/tools, and stop conditions.
- Subagents hand back compressed findings/plans/results, not raw transcript dumps.
- Reviewer checks the original request, not only the worker brief, and reports concise severity-tagged findings.

## Local agent files
- Global subagents live at `~/.pi/agent/agents/<name>.md`.
- Agent frontmatter must include `name` and `description`.
- `model` is passed as `--model` to a new Pi process.
- `tools` is a comma-separated string such as `tools: read, bash`; do not use YAML list syntax.
- Do not rely on unsupported frontmatter fields like `thinking` or `reasoning`.

## Provider/model routing
- Before dispatch, read the target agent file and verify its `model:`.
- Only dispatch OpenAI Codex OAuth-backed subagents: model must match `openai-codex/gpt-*`.
- Allowed reasoning suffixes: `:minimal`, `:low`, `:medium`, `:high`; do not use `:xhigh` for subagents.
- If no compliant agent exists, say so and do not dispatch.
- Preferred local routing:
  - `scout`: `openai-codex/gpt-5.4-mini:high`
  - `planner`: `openai-codex/gpt-5.5:high`
  - `worker`: `openai-codex/gpt-5.4:medium`
  - `reviewer`: `openai-codex/gpt-5.5:high`

## Anti-patterns
- Delegating tiny tasks.
- Letting `scout`, `planner`, or `reviewer` write code.
- Sending vague prompts without scope and stop conditions.
- Treating worker output as final without main-agent review.
