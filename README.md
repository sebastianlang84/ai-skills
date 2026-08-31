# ai-skills

Reusable AI/agent skills. This repository is the active global skill store.

On this machine, the canonical checkout/runtime path is:

```text
~/.agents/skills
```

Harness-specific skill directories are symlinks into it, not separate stores — currently `~/.claude/skills` → `~/.agents/skills`.

Do not keep a second global skill store. Repo-local skills, when needed, belong under a consuming repo's `.agents/skills/` directory.

## Layout

```text
<skill-name>/
  SKILL.md        # required skill entry point
  assets/         # optional skill-local templates/resources
  references/     # optional skill-local deeper guidance
  scripts/        # optional skill-local deterministic helpers
_scripts/         # repo-level validation/enforcement helpers, not a skill
.github/          # CI checks
.githooks/        # local Git hooks
README.md         # repo documentation
CHANGELOG.md      # operator-facing changes
.ignore           # excludes repo docs from skill discovery
```

Treat each `<skill-name>/` directory as the portable artifact. Skill-local helper scripts belong under that skill's `scripts/` directory. Repo-maintenance scripts belong in the root `_scripts/` directory; there is intentionally no root `scripts/` directory.

This repo is checked out directly at `~/.agents/skills`, so consuming harnesses discover skill folders from the repo root. Because some harnesses also treat root `*.md` files as individual skills, this repo keeps `README.md` and `CHANGELOG.md` out of skill discovery via the root `.ignore` file.

Validate a skill after edits:

```bash
python3 ~/.agents/skills/skill-creator/scripts/quick_validate.py <skill-name>
```

Validate repo metadata after README, CHANGELOG, hook, CI, or skill-list changes:

```bash
python3 _scripts/check_repo_metadata.py
```

## Current skills

This generated list must match the immediate skill directories in the repo root. Each summary comes from the skill's `SKILL.md` frontmatter.

<!-- BEGIN SKILL LIST -->
- `autoresearch` — Improve something through controlled experiments: freeze a metric and cases, change one lever, measure, keep or discard. Use when the user says autoresearch, or when tuning retrieval/ranking quality, prompts, skill descriptions, cost, or performance needs a baseline instead of a one-off change. Not for ordinary fixes with no verification signal.
- `code-documentation` — Update or review project documentation after code changes. Use when user-visible behavior, APIs, CLI commands, config, schemas, architecture, PRD status/scope, changelog entries, TODO cleanup, or ADR-worthy decisions may need documentation. Do not use for ordinary prose editing or agent-context/memory routing.
- `cross-vendor-review` — Get a narrowly scoped adversarial second opinion from another vendor's model on a substantial design, plan, or architecture decision. Use when the user explicitly asks for something to be "gegengelesen", a second opinion, a Codex/Opus review, or a devil's advocate; or when an expensive-to-reverse decision has a named unresolved risk and the verdict could change the decision. Not for routine implementation, small or reversible changes, code diffs, general reassurance, or automatic review after every change.
- `diagnosing-bugs` — Disciplined diagnosis loop for hard bugs, flaky failures, and performance regressions — build a tight failing feedback loop before forming any hypothesis. Use when the user says "debug this"/"diagnose", or reports something broken, throwing, failing, hanging, or slow.
- `evaluating-local-tools` — Evaluate an external repo, CLI, Pi extension, or local utility for possible use on this machine. Use when the user asks whether a tool has value, how heavy/risky it is, or to test it standalone before integrating. Emphasizes read-only research first, isolated installs/smoke tests, credential safety, and a clear adopt/skip verdict. Do not use for ordinary version update checks.
- `evaluating-with-promptfoo` — Run and preserve Promptfoo evaluations with pinned isolated tooling, frozen cases, provider-aware signals, and readable result records. Use when the user names Promptfoo, asks to rerun an existing Promptfoo suite, or chooses Promptfoo for cross-harness prompt, skill, tool-routing, or agent evaluation. Not for generic evaluation with no Promptfoo requirement; pair with autoresearch when tuning.
- `git-guardrails` — Install or adjust the hook that blocks irreversible git commands before Claude Code can run them.
- `git-workflow` — Use for Git safety, branch/worktree choice, commits, version/changelog impact, merge/push approval, and task closeout.
- `grilling` — Grill the user relentlessly about a plan, decision, or idea before acting. Use when the user wants to stress-test their thinking, uses any 'grill' trigger phrase, or when another skill needs the interview loop.
- `handoff` — Compact the current conversation into a handoff document so another agent or another harness can continue the work.
- `improve-codebase-architecture` — Find deepening opportunities in a codebase — refactors that turn shallow modules into deep ones. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
- `managing-agent-context` — Use this skill to audit, design, or repair LLM agent context systems: instruction files, skills, memory, document routing, tool exposure, MCP configuration, hooks/CI enforcement, and context bloat. Use when deciding what information should be loaded, retrieved, persisted, or enforced for agents.
- `newsletter-delivery` — Fetch and audit the Market Digest, diagnose stale runs, and deliver via Telegram only after explicit authorization.
- `nightly-review-pipeline` — Set up an unattended overnight code-review-and-fix pipeline for one or more git repos — systemd timer, bash orchestrator, headless `claude -p`.
- `parallel-agents` — Coordinating several agent sessions working the same repo at once — detecting that another session is already on your topic, claiming work, and the hook that refuses to create a file another live session already has. Use when several sessions run in parallel, when a merge turns up duplicate work, when a Write is refused as a collision, or when deciding whether to start on something another agent may already hold.
- `peer-debate` — Answers an open, contestable question by making two independent model instances argue it out under asymmetric roles until they converge or hit a round cap, then adjudicating the result. Use when the user wants a question debated, stress-tested by two agents, worked out by a duo, or says "let two models argue this", "have them discuss until they agree", "peer debate", or in German „lass das ausdiskutieren", „zwei Modelle sollen sich einigen". Not for critiquing a finished artifact — one reviewer against an existing document or diff is adversarial-model-review. Not for interrogating the user's own thinking (grilling), and not for defect scans of a codebase (codebase-review).
- `pi-extension-packaging` — Use this skill when designing, reviewing, restructuring, packaging, or auditing Pi extensions and Pi Packages, especially to choose clean repo structure (`src/index.ts` vs `extensions/`), package.json `pi` manifests, discovery paths, dependencies, and bundles with skills, prompts, or themes. Do not use for unrelated TypeScript work or non-Pi package management.
- `releasing-pi-packages` — Release a Pi extension or package from a local Git repo: verify, version, changelog, pack, tag, push.
- `resolving-merge-conflicts` — Resolve an in-progress git merge or rebase conflict hunk by hunk, by tracing each side's original intent. Use when a merge, rebase, or cherry-pick has stopped with conflicts.
- `secrets-env` — Use this skill when the user wants to design, review, or fix secrets and environment-variable handling. Covers .env boundaries, committed examples, secret-safe documentation, Compose env files, and leak-prevention checks.
- `skill-creator` — Create, audit, validate, repair, and improve portable agent skills. Use when designing a new skill, reviewing or simplifying a SKILL.md, improving trigger metadata, restructuring scripts/references/assets, or making a skill less runtime-specific. Do not use for unrelated package management or routine local inventory unless skill quality is the task.
- `tdd` — Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
- `tool-update-checker` — Check whether locally installed tools, pi packages/extensions, npm globals, Git repositories, and GitHub-hosted tools have upstream updates available. Use this skill when the user asks to check for updates, newer versions, releases, tags, or remote changes for tools such as pi-coding-agent, pi packages, GitHub-based extensions, Hermes, OpenClaw, or similar local utilities.
- `using-brain` — Read, explain, and extend the shared Brain at ~/.agents/brain. Use when a task depends on prior local decisions, preferences, methods, patterns, or indexed repo knowledge; when the user asks what the Brain knows or how it works; when durable cross-session learning should be recorded; or before changing Brain structure, retrieval, categories, provenance, or trust. Skip it for self-contained tasks answered entirely by current sources when no durable learning is expected. Do not use it for a project-local knowledge system with its own rules.
- `write-docker-compose` — Use this skill when the user wants to create or substantially update a Docker Compose file. Covers env layering, secrets-safe configuration, ports, persistence, service dependencies, documentation impact, and rendered-config validation.
- `write-dockerfile` — Use this skill when the user wants to create or substantially rewrite a Dockerfile. Covers base image selection, multi-stage builds, cache-friendly layers, non-root runtime, secrets handling, .dockerignore, and post-write validation.
<!-- END SKILL LIST -->

## Versioning and changelog

This repo does not version each skill with SemVer. Treat it as a living global skill collection; use `CHANGELOG.md` for operator-facing changes, removals, renames, and source-of-truth or layout changes.

Every skill or repo-metadata change must keep this README skill list and `CHANGELOG.md` current. Local hooks and CI enforce that gate.

## Scope notes

Global skills should be broadly reusable across repos. Project-specific workflows should live with their consuming project under `.agents/skills/`.
