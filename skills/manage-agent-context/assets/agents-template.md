---
role: Normative agent behavior, process rules, and bootstrap sequence
contains: Role norms, guardrails, gates, document-role overview, routing table
not-contains: Project state, how-tos, full policy text, detailed service designs
write-when: A behavior rule, gate, guardrail, or document-role summary changes
---

# AGENTS.md

[Target length: <=80 lines; <=100 acceptable with clear justification.]

## 1) Role & Behaviour

[Durable task behavior and decision style.]

- Be honest about uncertainty, limits, and mistakes.
- Be helpful, not flattering.
- Be concise, precise, and factual.
- Read and diagnose before you write.
- State assumptions and ambiguity; ask instead of guessing.
- Surface alternatives; do not choose silently when trade-offs matter.
- Prefer the simplest sufficient solution.
- Push back when simpler or safer is better.
- Define success criteria early and verify before calling work complete.
- Treat durable behavior changes as repo file changes, not chat promises.

## 2) Rules

[Repo-specific hard constraints. Adapt these defaults instead of copying blindly.]

- One technical goal per task unless the user explicitly asks for a broader pass.
- Avoid speculative features, abstractions, or configurability.
- Change only what is needed; keep diffs small.
- Avoid unrelated refactors, reformatting, or cleanup.
- Match existing style unless asked otherwise.
- Remove only unused code created by your change.
- Stop and ask when facts are unclear and risk is non-trivial.
- Protect secrets; never expose them in chat, logs, docs, or commits.
- Do not overwrite or revert unrelated user changes.
- If the worktree has unexpected or unrelated changes, stop and ask before commit, revert, delete, or broad edits.

## 3) Bootstrap Sequence

[Read order for every new agent session.]

On session start: use the agent/harness memory tools for durable context, then read `TODO.md` if it exists. Everything else is read on demand.

Load the relevant global/repo skill instead of copying long procedures here: use `git-workflow` for branch, commit, merge, push, tag, and release mechanics; use `manage-agent-context` for document routing and context-system changes.

## 4) Document Roles

[Route durable information to the right file.]

| File | Role | Write when |
| --- | --- | --- |
| agent/harness memory (Pi: pi-memory tools) | Stable current truth and reset-resilient handoff | Stable truth, durable context, or handoff state changes |
| `TODO.md` | Active open work only | Work or priorities change |
| `CHANGELOG.md` | Outward-facing change history | User/operator-relevant change introduced |
| `README.md` | Human/operator guide | Setup, usage, operation, or troubleshooting changes |
| `docs/adr/*` | Durable decision records | A durable decision is made |
| `docs/runbooks/*` | Procedural how-to | A workflow is documented |
| `docs/plans/*` | Detailed execution plans | A task needs more breakdown |
| `.agents/skills/*` | Optional repo-local skills | A reusable skill is curated |

## 5) Gates

[Mandatory task flow.]

- Preflight: state goal, scope, and assumptions before writing.
- Diagnose: inspect files/config/tool output before editing.
- Implement: keep changes minimal and scoped.
- Verify: check results after changes; update routed docs only when their triggers are met.
- Closeout: inspect status, protect unrelated changes, close completed `TODO.md`/memory todos, decide SemVer impact, update `CHANGELOG.md` when release-relevant, and run the smallest relevant checks.
- Commit/merge/push/tag only after explicit approval. Before push, state: TODO cleanup result, CHANGELOG/SemVer decision, verification result, and target branch/remote/tags.

## 6) Repo

[Short repo-specific summary.]

- Purpose: [what this repository exists to do]
- In scope: [what belongs here]
- Out of scope: [what does not belong here]
- Main components: [key services, apps, packages, or directories]
