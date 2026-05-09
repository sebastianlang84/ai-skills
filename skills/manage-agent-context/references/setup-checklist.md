# Agentic Repo Bootstrap Checklist

Use when aligning a repo's agent-facing context system.

## 1. Preflight

- State goal, scope, assumptions, and whether edits/deletions are in scope.
- Check for unrelated worktree changes before editing.
- Ask before broad, destructive, ambiguous, or ownership-changing edits.

## 2. Diagnose read-only

Inspect only what matters for context routing:

- root tree, README, TODO/issue convention, changelog, docs
- code/config/package/deploy files for project facts and verification commands
- agent files: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.roo/*`, `.agents/*`
- referenced skills, tools/extensions/MCP, scripts, hooks, CI
- memory/session files only enough to identify stable current context; do not import diaries

Look for duplicate authority, stale docs contradicted by code/config, missing setup or verification commands, secrets in docs, and overgrown memory/task history.

## 3. Design target shape

Choose the smallest baseline from `references/document-routing.md`. Add optional docs, repo-local skills, scripts, hooks, CI, or tools only when they have clear reuse or enforcement value.

## 4. Implement

- Preserve verified repo-specific content.
- Remove fillable placeholders; leave explicit placeholders only for unknown facts.
- Prefer targeted edits over broad rewrites.
- Suggested order: human docs, agent instructions, durable context, active work, history, then enforceable checks.

## 5. Verify

- Re-read changed files for contradictions and role overlap.
- Confirm referenced files/systems exist.
- Run the routing checks in `references/review-checklist.md`.
- Ensure important gates are encoded in durable/enforceable layers, not only chat promises.
- Run repo checks if setup, commands, or enforced policy changed.

## 6. Report

Summarize changed/recommended files, assumptions/placeholders, removed or remaining bloat, risky/deferred decisions, and verification.
