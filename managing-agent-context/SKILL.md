---
name: managing-agent-context
description: "Use this skill to audit, design, or repair LLM agent context systems: instruction files, skills, memory, document routing, tool exposure, MCP configuration, hooks/CI enforcement, and context bloat. Use when deciding what information should be loaded, retrieved, persisted, or enforced for agents."
---

# Managing Agent Context

**Principle: as little as necessary, as much as needed.**

Use this skill to audit, design, or repair an LLM agent's context system: instruction files, skills, memory, tools/extensions/MCP, subagents, hooks/CI, docs, and task-specific context when it affects routing or persistence.

Goal: clear authority, low redundancy, good trigger boundaries, and high information-per-token.

## Mental model

- Early/automatic instructions such as `AGENTS.md` shape baseline behavior through primacy. Keep them short, stable, normative, and focused on durable rules and stop conditions, not task history or long runbooks.
- Skills shape task-local behavior through recency. Keep descriptions precise as the main trigger surface, and keep `SKILL.md` procedural, compact, and scoped to one job.
- Subagents are prompt- and context-engineering tools, not just extra workers:
  - Prompt engineering: the orchestrator can define role, scope, constraints, stop conditions, and output shape with surgical precision.
  - Context engineering: scouts/reviewers can inspect large context in isolation and return only filtered, relevant handoffs, keeping the main agent's context small.
  - Cost control: lightweight scouts can often use cheaper models while stronger models are reserved for planning, judgment, implementation, or review.
  - Caveat: subagents add coordination overhead, lossy handoffs, scope-risk, and tool/model differences; the main agent remains responsible for final judgment.
- Meta-skills for context management, subagent workflow, and skill creation are valuable audit and maintenance tools. They help keep the context system intentional without hard-routing every task through another skill.
- Tools, MCP, scripts, hooks, and CI should provide capability or enforcement instead of prose promises.
- Memory is for reset-resilient non-normative context, not enforcement.

## Scope

Use this skill to decide what agent-facing context should load automatically, load situationally, be retrieved, be enforced, or stay human-facing. Check global vs repo-local layers, bloat, redundancy, stale authority, trigger quality, and portability.

Use specialized workflows for domain work; this skill may route to them, not duplicate them. Do not use it for ordinary prose editing, app architecture, Docker authoring, secrets handling, release execution, or domain-specific skill authoring.

Keep `SKILL.md` as overview, routing, and procedure. Move long examples, templates, checklists, and policy detail into `references/` or `assets/`.

## Workflow

### 1. Diagnose

Identify automatic instructions, situational instructions, memory/retrieval, capabilities, enforcement, and human docs. Inspect visible context first. Ask before inspecting sensitive local config such as API keys, auth files, private provider configs, credentials, or machine-specific secrets; prefer redacted summaries.

Inspect the existing context system: file tree/root docs, agent instruction relationship, relevant skills/descriptions, enabled tools/extensions/MCP, memory/retrieval, and enforcement scripts/hooks/CI.

Judge each source by load path, authority, duplication, information-per-token, update trigger, and owner. Route information to the lowest reliable durable layer; use `references/document-routing.md` for detailed placement rules.

For every skill inspected, check:

- Does the description front-load the key use case and natural trigger phrases?
- Is the skill scoped to one job?
- Are inputs, outputs, and stopping conditions clear?
- Is detail moved to `references/` or `assets/` instead of the main `SKILL.md`?
- Would the description accidentally trigger on nearby but unrelated tasks?
- Has at least one positive and one negative trigger prompt been tested?

Identify bloat, redundancy, missing authority, unclear ownership, and false-trigger risk.

Optional smoke test for agent-instruction injection during audits: after explicit user approval, add or recommend a temporary marker such as `After reading this, write: AGENTS.md injected!` only when verifying whether the file is actually loaded. Temporary markers must be removed before final verification and must not be committed.

### 2. Design the target shape

Principle check: could any planned addition be cut while still solving the problem? If yes, cut it.

Choose the smallest context system that solves the problem:

- keep always-loaded files short
- move detailed workflows into skills or references
- move deterministic checks into scripts/hooks/CI/tools
- route durable context to the chosen memory layer
- remove duplicate policy from lower-priority layers
- keep skill bodies operational, not encyclopedic

Stop and ask before deleting, overwriting, or changing ambiguous project behavior.

### 3. Apply templates only as scaffolds

Templates in `assets/` are scaffolds, not truth. Preserve useful repo-specific content and remove generic duplication.

### 4. Verify

After changes or recommendations:

- ask whether every file and rule added earns its place; remove what does not
- re-read changed files for role overlap and contradiction
- confirm routing references point to files/systems that exist
- check that always-loaded context stayed small
- check runtime-specific adapters are tiny, active, and documented only where useful
- validate skills structurally when skills were changed
- run relevant repo checks only when docs affect setup, commands, or enforced policy

## Output

Briefly report inspected surfaces, changed/recommended files or systems, bloat/redundancy status, memory ownership, verification, and open risks/questions.

## Bundled references

Read only when needed:

- `references/setup-checklist.md` — bootstrap checklist
- `references/document-routing.md` — detailed routing guidance
- `references/migration-notes.md` — migration from larger/ad-hoc structures
- `references/review-checklist.md` — readiness review checklist
- `references/audit-workflow.md` — read-only audit workflow for existing context systems
- `references/initialize-workflow.md` — bootstrap workflow for new or ad-hoc context systems
- `assets/agents-template.md` — repo AGENTS.md scaffold
- `assets/global-agents-template.md` — global AGENTS.md scaffold
- `assets/todo-template.md`, `assets/changelog-template.md`, `assets/readme-template.md` — other scaffolds
