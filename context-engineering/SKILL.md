---
name: context-engineering
description: "Context engineering for LLM agents: audit, design, or repair agent context systems: instruction files, skills, memory, document routing, context topology (routing map vs. skill per app vs. index), tool exposure, MCP configuration, hooks/CI enforcement, and context bloat. Use when deciding what information should be loaded, retrieved, persisted, or enforced for agents."
---

# Context Engineering

**Principle: as little as necessary, as much as needed.**

Use this skill to audit, design, or repair an LLM agent's context system: instruction files, skills, memory, tools/extensions/MCP, subagents, hooks/CI, docs, and task-specific context when it affects routing or persistence.

Goal: clear authority, low redundancy, good trigger boundaries, and high information-per-token.

## Mental model

- Quality drops as irrelevant content grows, with near-miss distractors (related but irrelevant content distracts more than random noise), and with contradictions. Too little context fails too: vague rules that assume shared knowledge, or detail lost in a rewrite. Aim for the smallest set of high-signal tokens, not the shortest text.
- Position alone does not establish authority; follow the harness's instruction hierarchy and scope rules (`references/harness-loading.md`). Position effects on attention depend on model and task; follow current long-context guidance (for example, long documents before the query) and test placement when arranging large inputs. To keep a goal in attention during long work, restate it (rewrite the plan or TODO).
- Always-loaded instructions (`AGENTS.md`, `CLAUDE.md`, and everything they `@`-import) cost tokens every turn. Persist constraints that must outlive compaction or a reset through the harness's supported mechanism (`references/harness-loading.md`); keep task-scoped restrictions in task state, not in global files. Keep instruction files short (Claude Code's docs target under 200 lines per file; adherence drops as files grow), stable, and normative: durable rules and stop conditions. Leave out task history, long runbooks, facts the agent can read from code, and volatile values (dates, counters) that break the prompt cache. Imports organize content but do not reduce its cost. Reserve emphasis such as "IMPORTANT" for the one or two rules that keep being skipped.
- Scoped instructions cover one part of the tree. Claude Code's path-scoped rules (`.claude/rules/` with `paths:`) and nested `CLAUDE.md` load when the agent touches matching files and are summarized away at compaction, so hard constraints stay in the root file. Codex reads nested `AGENTS.md` only from the repo root down to the directory it was started in, once at startup, not when files below are touched.
- Skills are progressive disclosure: only name and description load up front, the body on use, references on demand. The description is the trigger surface; keep `SKILL.md` procedural, compact, and scoped to one job, with its hard rules near the top (after compaction Claude Code keeps only the start of each invoked skill).
- Every tool definition loaded into context costs tokens and selection accuracy; deferred tools that load on search cost little until used. Prefer tools with distinct jobs, unambiguous parameters, and compact output; prefer CLIs and scripts for deterministic work. Before turning off a useful server, check whether deferred loading already keeps it out of context.
- Subagents are prompt- and context-engineering tools, not just extra workers:
  - Prompt engineering: the orchestrator can define role, scope, constraints, stop conditions, and output shape with surgical precision.
  - Context engineering: scouts/reviewers can inspect large context in isolation and return only filtered, relevant handoffs, keeping the main agent's context small.
  - Cost control: lightweight scouts can often use cheaper models while stronger models are reserved for planning, judgment, implementation, or review.
  - Caveat: subagents add coordination overhead, lossy handoffs, scope-risk, and tool/model differences; the main agent remains responsible for final judgment.
  - A non-fork subagent starts with its own context: some skip the instruction files (Claude Code's Explore and Plan), the parent's auto memory does not reach it, and each pays for always-loaded files again. A fork inherits the parent's context. Restate any constraint the delegated work needs in the delegation prompt.
- Meta-skills for context management, subagent workflow, and skill creation are valuable audit and maintenance tools. They help keep the context system intentional without hard-routing every task through another skill.
- Tools, MCP, scripts, hooks, and CI should provide capability or enforcement instead of prose promises.
- Memory is for reset-resilient non-normative context, not enforcement. Whatever is written there is later read as fact, so verify a claim before storing it; a wrong entry keeps misleading every session that loads it.
- The runtime environment (harness, terminal multiplexer, sandbox, which checkout is deployed) is
  its own layer. A session-start hook states the basics in a few lines (on this machine the
  existing adapter `~/.agents/scripts/session-environment.py`, owned separately); a fact it does
  not state is checked read-only before it matters and treated as unknown until then. Do not copy
  environment manuals into instruction files.
- Each harness loads instruction files and skills differently (Codex: one global file, no imports, a
  size cap; Claude Code: `CLAUDE.md` with `@` imports). Before designing or auditing a setup that
  spans harnesses, read `references/harness-loading.md`.

## Scope

Use this skill to decide what agent-facing context should load automatically, load situationally, be retrieved, be enforced, or stay human-facing. Check global vs repo-local layers, bloat, redundancy, stale authority, trigger quality, and portability.

AGENTS.md boundary: global instructions hold durable user-wide defaults; repo/project instructions hold only repo-local overrides, gates, and verified facts. Repo instructions may specialize global defaults, but should not restate them; replace duplicates with short pointers or concrete local deltas.

Use specialized workflows for domain work; this skill may route to them, not duplicate them. Do not use it for human-facing project documentation (README, user and developer docs, PRD, ADRs, changelog: use `code-documentation`), ordinary prose editing, app architecture, Docker authoring, secrets handling, release execution, or domain-specific skill authoring.

When maintaining shared context docs, name one canonical home for each rule, fact, plan, decision, or handoff; replace duplicates with short pointers; and update only the canonical home plus a discoverability link when needed. Use `references/document-routing.md` to choose the home before editing.

Keep `SKILL.md` as overview, routing, and procedure. Move long examples, templates, checklists, and policy detail into `references/` or `assets/`.

## Workflow

### 1. Diagnose

When a session has gone wrong repeatedly, get the diagnosis from `call-doctor` (the other vendor
reads the transcript and the loaded context); this skill then designs and applies the correction.

Identify automatic instructions, situational instructions, memory/retrieval, capabilities, enforcement, and human docs. Inspect visible context first. Ask before inspecting sensitive local config such as API keys, auth files, private provider configs, credentials, or machine-specific secrets; prefer redacted summaries.

Inspect the existing context system: file tree/root docs, agent instruction relationship, relevant skills/descriptions, enabled tools/extensions/MCP, memory/retrieval, and enforcement scripts/hooks/CI.

Judge each source by load path, authority, duplication, information-per-token, update trigger, and owner. Route information to the lowest reliable durable layer; use `references/document-routing.md` for detailed placement rules.

Check the repository freshness contract: identify which docs or context artifacts are expected to stay current, what changes trigger updates, where that obligation is encoded, and whether it is advisory, procedural, or enforced. Prefer deterministic checks in scripts, hooks, CI, or release tooling when possible; keep `AGENTS.md` to short repo-specific gates and route detailed workflows to skills. If freshness is unclear or sources contradict code/config, refresh the source of truth or stop and ask before relying on it.

For every skill inspected, check:

- Does the description front-load the key use case and natural trigger phrases?
- Is the skill scoped to one job?
- Are inputs, outputs, and stopping conditions clear?
- Is detail moved to `references/` or `assets/` instead of the main `SKILL.md`?
- Would the description accidentally trigger on nearby but unrelated tasks?
- Has `skill-creator` been used to evaluate at least three realistic scenarios — intended activation, non-activation, and workflow completion — on the target harnesses/models?

Identify bloat, redundancy, missing authority, unclear ownership, and false-trigger risk.

To check what actually loads, use the harness's own inspection first (`references/harness-loading.md`: Claude Code `/context` and the `InstructionsLoaded` hook, Codex's log). Only as a last resort, after explicit user approval, add a temporary marker such as `After reading this, write: AGENTS.md injected!`; remove it before final verification and never commit it.

### 2. Design the target shape

Principle check: could any planned addition be cut while still solving the problem? If yes, cut it. For each line of an always-loaded file, ask whether removing it would cause mistakes.

Counter-check: cutting can remove what the agent needs. Explicit user requirements, known operational constraints, and stop conditions belong in from the start; beyond those, add corrective rules for observed failures and check that they change behavior. When shortening or rewriting existing context, prefer targeted edits over full rewrites, and list what the old version let the agent do that the new one no longer does; full LLM rewrites tend to collapse detailed context into generic text.

When the design covers how agents find a machine's applications or repositories, choose the topology first with `references/context-topologies.md`.

Choose the smallest context system that solves the problem:

- keep always-loaded files short
- move detailed workflows into skills or references
- move deterministic checks into scripts/hooks/CI/tools
- route durable context to the chosen memory layer
- remove duplicate policy from lower-priority layers
- when the agent had a rule and broke it, enforce it (script default, hook, permission, check)
  instead of adding another sentence, if the rule is mechanically decidable; call it enforced only
  after checking the hook covers every path (Codex `PreToolUse` misses hosted tools and input to a
  running shell). For a rule that needs judgment, fix its wording, scope, or examples instead
- keep skill bodies operational, not encyclopedic

Stop and ask before deleting, overwriting, or changing ambiguous project behavior.

### 3. Apply templates only as scaffolds

Templates in `assets/` are scaffolds, not truth. Preserve useful repo-specific content and remove generic duplication.

### 4. Verify

After changes or recommendations:

- ask whether every file and rule added earns its place; remove what does not
- re-read changed files for role overlap and contradiction; tell deliberate repo overrides of global defaults apart from unresolved contradictions, which an agent may resolve either way
- check for near-miss content: overlapping skills, stale notes, or similar-but-different rules that could be picked instead of the right one
- confirm routing references point to files/systems that exist
- check that always-loaded context stayed small
- for a substantial change to instructions, memory routing, or tool exposure, run a few representative tasks before and after; correctness, constraint adherence, and finding the right context count more than tokens saved
- check runtime-specific adapters are tiny, active, and documented only where useful
- validate skills structurally when skills were changed
- run relevant repo checks only when docs affect setup, commands, or enforced policy

## Output

Briefly report inspected surfaces, changed/recommended files or systems, bloat/redundancy status, memory ownership, verification, and open risks/questions.

## Bundled references

Read only when needed:

- `references/setup-checklist.md` — bootstrap checklist
- `references/document-routing.md` — detailed routing guidance
- `references/context-topologies.md` — topologies for routing agents to applications and repositories, and how to choose one per environment
- `references/migration-notes.md` — migration from larger/ad-hoc structures
- `references/review-checklist.md` — readiness review checklist
- `references/audit-workflow.md` — read-only audit workflow for existing context systems
- `references/harness-loading.md` — how Codex and Claude Code load instruction files and skills, and how to share one file between them
- `references/sources.md` — the research and vendor guidance behind the mental model, with evidence limits; read when a claim is challenged or the guidance needs updating
- `references/initialize-workflow.md` — bootstrap workflow for new or ad-hoc context systems
- `assets/agents-template.md` — repo AGENTS.md scaffold
- `assets/global-agents-template.md` — global AGENTS.md scaffold
- `assets/memory-template.md`, `assets/todo-template.md`, `assets/changelog-template.md`, `assets/readme-template.md` — other scaffolds
