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
- `autoresearch` — Use when the user mentions autoresearch, or when an improvement request explicitly needs a measurable baseline plus repeatable evaluation/benchmark/rubric to compare variants. Autoresearch turns optimization work into controlled loops: define a goal, freeze metrics and cases, form hypotheses, change one lever at a time, run evaluations, log quantitative deltas, classify regressions, and keep/discard changes. Especially useful for retrieval/search quality, ranking, chunking, agents/prompts/workflows, skill descriptions, extension/tool prompt injections, performance, cost, reliability, usability, and other systems with iterative loops and measurable outcomes. Do not use for ordinary bugfixes, reviews, prose edits, vague brainstorming, or one-off changes without a verification signal.
- `code-documentation` — Update or review project documentation after code changes. Use when user-visible behavior, APIs, CLI commands, config, schemas, architecture, PRD status/scope, changelog entries, TODO cleanup, or ADR-worthy decisions may need documentation. Do not use for ordinary prose editing or agent-context/memory routing.
- `evaluating-local-tools` — Evaluate an external repo, CLI, Pi extension, or local utility for possible use on this machine. Use when the user asks whether a tool has value, how heavy/risky it is, or to test it standalone before integrating. Emphasizes read-only research first, isolated installs/smoke tests, credential safety, and a clear adopt/skip verdict. Do not use for ordinary version update checks.
- `git-workflow` — Use for Git safety, branch/worktree choice, commits, version/changelog impact, merge/push approval, and task closeout.
- `grilling` — Grill the user relentlessly about a plan, decision, or idea before acting. Use when the user wants to stress-test their thinking, uses any 'grill' trigger phrase, or when another skill needs the interview loop.
- `improve-codebase-architecture` — Find deepening opportunities in a codebase, informed by the domain language in CONTEXT.md and the decisions in docs/adr/. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
- `managing-agent-context` — Use this skill to audit, design, or repair LLM agent context systems: instruction files, skills, memory, document routing, tool exposure, MCP configuration, hooks/CI enforcement, and context bloat. Use when deciding what information should be loaded, retrieved, persisted, or enforced for agents.
- `newsletter-delivery` — Fetch the Market Digest, check freshness, diagnose stale newsletter runs, audit content, and optionally deliver via Telegram only after explicit operator authorization.
- `nightly-review-pipeline` — Set up an unattended overnight code-review-and-fix pipeline on a Linux server. Use when the user wants scheduled/nightly automated reviews of one or more git repos that write findings to markdown (todo.md / IDEAS.md) and optionally open auto-fix draft pull requests, driven by a systemd timer (or cron) + a bash orchestrator + headless `claude -p`. Covers the review "lenses" (bug screening, usability/functionality), adaptive scheduling with backoff, git/PR policy, and safety guardrails for unattended agent runs. Not for one-off interactive reviews (use /code-review) or Anthropic cloud routines (use /schedule).
- `pi-extension-packaging` — Use this skill when designing, reviewing, restructuring, packaging, or auditing Pi extensions and Pi Packages, especially to choose clean repo structure (`src/index.ts` vs `extensions/`), package.json `pi` manifests, discovery paths, dependencies, and bundles with skills, prompts, or themes. Do not use for unrelated TypeScript work or non-Pi package management.
- `releasing-pi-packages` — Release a Pi extension or Pi package from a local Git repo. Use when preparing, versioning, tagging, packing, or pushing releases for Pi packages/extensions after code changes are verified. Extends generic git workflow with Pi/package-specific checks such as package.json pi manifest, changelog, npm pack dry-run, extension/tool tests, and post-release indexing notes. Do not use for ordinary code edits or non-Pi package releases.
- `secrets-env` — Use this skill when the user wants to design, review, or fix secrets and environment-variable handling. Covers .env boundaries, committed examples, secret-safe documentation, Compose env files, and leak-prevention checks.
- `skill-creator` — Create, audit, validate, repair, and improve portable agent skills. Use when designing a new skill, reviewing or simplifying a SKILL.md, improving trigger metadata, restructuring scripts/references/assets, or making a skill less runtime-specific. Do not use for unrelated package management or routine local inventory unless skill quality is the task.
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
