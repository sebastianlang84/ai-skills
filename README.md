# ai-skills

Reusable AI/agent skills. This repository is laid out as the active Pi global skill store.

On this machine, the canonical checkout/runtime path is:

```text
~/.pi/agent/skills
```

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
.ignore           # excludes repo docs from Pi skill discovery
```

Treat each `<skill-name>/` directory as the portable artifact. Skill-local helper scripts belong under that skill's `scripts/` directory. Repo-maintenance scripts belong in the root `_scripts/` directory; there is intentionally no root `scripts/` directory.

This repo is checked out directly at `~/.pi/agent/skills`, so Pi discovers skill folders from the repo root. Pi also discovers direct root `*.md` files in `~/.pi/agent/skills/` as individual skills; this repo keeps `README.md` and `CHANGELOG.md` out of skill discovery via the root `.ignore` file.

Validate a skill after edits:

```bash
python3 ~/.pi/agent/skills/skill-creator/scripts/quick_validate.py <skill-name>
```

Validate repo metadata after README, CHANGELOG, hook, CI, or skill-list changes:

```bash
python3 _scripts/check_repo_metadata.py
```

## Current skills

This generated list must match the immediate skill directories in the repo root. Each summary comes from the skill's `SKILL.md` frontmatter.

<!-- BEGIN SKILL LIST -->
- `git-workflow` — Use for Git safety, branch/worktree choice, commits, version/changelog impact, merge/push approval, and task closeout.
- `grill-me` — Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
- `grill-with-docs` — Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates documentation (CONTEXT.md, ADRs) inline as decisions crystallise. Use when user wants to stress-test a plan against their project's language and documented decisions.
- `improve-codebase-architecture` — Find deepening opportunities in a codebase, informed by the domain language in CONTEXT.md and the decisions in docs/adr/. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
- `managing-agent-context` — Use this skill to audit, design, or repair LLM agent context systems: instruction files, skills, memory, document routing, tool exposure, MCP configuration, hooks/CI enforcement, and context bloat. Use when deciding what information should be loaded, retrieved, persisted, or enforced for agents.
- `newsletter-delivery` — Fetch, audit, and deliver the daily Market Digest newsletter via Telegram.
- `pi-extension-packaging` — Use this skill when designing, reviewing, restructuring, packaging, or auditing Pi extensions and Pi Packages, especially to choose clean repo structure (`src/index.ts` vs `extensions/`), package.json `pi` manifests, discovery paths, dependencies, and bundles with skills, prompts, or themes. Do not use for unrelated TypeScript work or non-Pi package management.
- `secrets-env` — Use this skill when the user wants to design, review, or fix secrets and environment-variable handling. Covers .env boundaries, committed examples, secret-safe documentation, Compose env files, and leak-prevention checks.
- `skill-creator` — Create, audit, validate, repair, and improve portable agent skills. Use when designing a new skill, reviewing or simplifying a SKILL.md, improving trigger metadata, restructuring scripts/references/assets, or making a skill less runtime-specific. Do not use for unrelated package management or routine local inventory unless skill quality is the task.
- `subagent-workflow` — Use when dispatching subagents. Covers whether to delegate, role workflow, handoffs, review expectations, and allowed local provider/model routing in one compact policy.
- `tdd` — Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
- `tool-update-checker` — Check whether locally installed tools, pi packages/extensions, npm globals, Git repositories, and GitHub-hosted tools have upstream updates available. Use this skill when the user asks to check for updates, newer versions, releases, tags, or remote changes for tools such as pi-coding-agent, pi packages, GitHub-based extensions, Hermes, OpenClaw, or similar local utilities.
- `write-docker-compose` — Use this skill when the user wants to create or substantially update a Docker Compose file. Covers env layering, secrets-safe configuration, ports, persistence, service dependencies, documentation impact, and rendered-config validation.
- `write-dockerfile` — Use this skill when the user wants to create or substantially rewrite a Dockerfile. Covers base image selection, multi-stage builds, cache-friendly layers, non-root runtime, secrets handling, .dockerignore, and post-write validation.
<!-- END SKILL LIST -->

## Versioning and changelog

This repo does not version each skill with SemVer. Treat it as a living global skill collection; use `CHANGELOG.md` for operator-facing changes, removals, renames, and source-of-truth or layout changes.

Every skill or repo-metadata change must keep this README skill list and `CHANGELOG.md` current. Local hooks and CI enforce that gate.

## Scope notes

Global skills should be broadly reusable across repos. Project-specific workflows should live with their consuming project under `.agents/skills/`.
