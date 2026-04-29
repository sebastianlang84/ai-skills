---
name: audit-manager
description: Use this skill when the user wants a structured repository or documentation audit. Provides reusable profiles for AGENTS.md policy quality, README quality, monorepo hygiene, and repo structure without editing files unless separately requested.
---

# Audit Manager

Use this skill to run read-only audits and produce structured findings. Do not modify audited files unless the user explicitly asks for a remediation pass.

## Profiles

- `profiles/agents-md.md` — audit agent policy/governance files such as `AGENTS.md`.
- `profiles/readme.md` — audit README usefulness, accuracy, setup, security, and maintainability.
- `profiles/monorepo-hygiene.md` — audit large or mixed-purpose repositories for hygiene, governance, operations, and security baseline.
- `profiles/repo-structure.md` — focused audit of top-level layout, naming, ownership, and information architecture.

## Workflow

1. Select the narrowest profile matching the user's request.
2. Confirm audit scope, target paths, and whether the task is read-only.
3. Read relevant files before judging. Do not expose secrets found during review.
4. Score each section with ✅ / ⚠️ / ❌ or an equivalent clear status.
5. Provide evidence, risk, and concise remediation suggestions.
6. Keep filled audit results separate from reusable profiles/templates unless the user requests a specific output file.

## Output expectations

Include summary, top strengths, top risks/gaps, findings table, quick wins, larger measures, and any validation limits.
