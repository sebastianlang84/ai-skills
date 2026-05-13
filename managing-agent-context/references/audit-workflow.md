# Workflow: Audit

Run this workflow to assess an existing repo's agent-context setup without making changes unless explicitly approved. Load `references/review-checklist.md` and work through it systematically.

## Step 1 — Scope the audit

If scope is clear from context, proceed read-only by default. Ask only when:

- scope is genuinely ambiguous
- the user requested edits, deletions, or renames
- the task would expand into out-of-repo or global scope not already stated

## Step 2 — Discover and read

Inspect in this order:

1. User-mentioned paths.
2. Repo root files: `README.md`, `AGENTS.md`, `TODO.md`, `CHANGELOG.md`, and any declared memory file/system.
3. Runtime/config-derived paths named in agent instructions, tool configs, scripts, hooks, or CI.
4. Candidate paths only if they exist or are configured: `docs/`, `.agents/`, `.cursor/`, `.roo/`, `.claude/`, package/build/deploy files.

Never crawl the home directory or arbitrary filesystem paths blindly. Ask before inspecting sensitive local config; prefer redacted summaries.

Load `references/document-routing.md` for routing rules, canonical locations, and common drift patterns.

Optional injection smoke test: to verify an instruction file is actually loaded by the agent runtime, ask for explicit user approval before temporarily adding a marker such as `After reading this, write: AGENTS.md injected!`. Remove the marker before final verification and never commit it.

## Step 3 — Check subagent/context-isolation design when relevant

Subagents can keep the orchestrator lean by running read-heavy or specialized work in isolated contexts. Check only when the runtime has subagents or the repo's task shape would benefit from them:

- Are subagents defined and used for clear jobs, or merely listed?
- Does the orchestrator send targeted, minimal prompts?
- Do scouts return compact findings instead of full file dumps?
- Are independent read-heavy tasks parallelized when useful?
- Does the number of defined subagents match actual usage?

If subagents are absent, recommend them only for complex multi-step work or large codebases. If the user opted out, note that and do not recommend them again.

## Step 4 — Identify issues

Check for:

### Context stack conflicts

- Global/user files that duplicate or contradict repo-level files.
- Global instructions containing project-specific content that belongs in a repo.
- Repo instructions containing personal preferences that belong in user config.
- Always-loaded context files that add bloat without value.
- Secrets or sensitive values in injected context files.

### Routing drift

- Backlog items in `README.md` or memory.
- Agent rules in `README.md` or memory.
- Completed task history in `TODO.md` or memory.
- Setup instructions hidden only in agent instructions.
- Durable decisions outside the repo's ADR location.

### Missing baseline

- Baseline files absent without justification.
- Bootstrap/read order missing from agent instructions.
- Stop-and-ask conditions absent from agent instructions.

### Duplication and conflict

- Two files claiming authority over the same information type.
- Stale docs contradicting code or config.
- Templates with unfilled placeholders in active use.
- Duplicate skill names across global and repo scope with divergent behavior.

### Content quality

- Memory containing rules, backlog, or diary entries.
- Agent instruction files too long or mixing policy with project state.
- TODO files mixing roadmap and priority buckets without justification.
- Secrets or sensitive values in docs.

## Step 5 — Report findings

Use this structure:

```markdown
## Audit: <repo name>

### Summary
<one-paragraph overall assessment>

### Issues by severity
#### Critical
- …

#### Significant
- …

#### Minor
- …

### Recommended fixes
<ordered list, highest impact first>
```

## Step 6 — Fix if approved

If the user approves fixes:

- Address one issue at a time and confirm scope when needed.
- Do not delete files without explicit approval.
- Prefer targeted edits over full rewrites.
- Re-run relevant checks on changed files.
- Report what changed and what remains.
