# Changelog

Operator-facing changes to this global skill collection are documented here.

This repo does not version individual skills with SemVer. Use this changelog to record skill additions, removals, renames, source-of-truth changes, and enforcement changes.

## [Unreleased]

### Added

- Added `grilling`: the reusable relentless-interview loop, run before acting on a plan. Separates *facts* (the agent looks them up) from *decisions* (put to the user, one question at a time, each with a recommended answer), and ends on an explicit confirmation gate so nothing is built before shared understanding is reached. Adapted from Matt Pocock's `grilling` skill (MIT).
- Tracked `autoresearch`, `evaluating-local-tools`, and `releasing-pi-packages`, which existed in the working tree but had never been committed.
- Added `nightly-review-pipeline` to set up an unattended overnight review+fix pipeline (systemd/cron + bash orchestrator + headless `claude -p`) with bug and usability lenses, adaptive backoff, and safe auto-fix draft PRs (isolated worktree, tests-green gate, never main, never auto-merge).
- Added `code-documentation` to route documentation updates after code changes and keep PRD, README, changelog, TODO, AGENTS, and memory roles separate.
- Clarified the `code-documentation` goal so README, changelog, and TODO updates remain encouraged when they match each artifact's role.

### Removed

- Removed `grill-me` and `grill-with-docs`. `grill-with-docs` coupled grilling to a `CONTEXT.md` domain model that this collection no longer maintains (see the matching `improve-codebase-architecture` change); `grill-me` was a wrapper whose only remaining primitive, `grilling`, is directly invocable.
- Removed `pi-subagents`. It was entirely Pi-specific orchestration policy, and Pi no longer consumes this skill store.

### Fixed

- Corrected the canonical global skill store path from `~/.pi/agent/skills` to `~/.agents/skills` across `README.md`, `skill-creator`, and `skill-creator/references/agent_adapters.md`. The old path does not exist on this machine, so the documented validation command could not run and `skill-creator` instructed agents to relocate skills to a missing directory, contradicting the global `AGENTS.md`.

### Changed

- Tightened `git-workflow` release discipline: patch/minor/major impact now requires proposing the concrete next version number and expected tag name before push or closeout, and a version bump may not be pushed while silently omitting its matching release tag.
- Decoupled `improve-codebase-architecture` from the `CONTEXT.md` domain model: it names modules from the project's own terms in the code instead of a maintained glossary, and no longer reads or writes `CONTEXT.md` or ADRs as part of its process.
- Updated `newsletter-delivery` for the `market-digest-*` systemd unit names and added a Risk & Chance Radar private-test gate: a private Radar test counts as ready only after a final no-delivery end-to-end run produces and validates `risk_chance_radar.md`, never from renderer-only output or stale artifacts.
- Hardened `newsletter-delivery` with explicit production-send authorization, stale-run diagnosis guidance, safe Telegram/Oberhummer DM render-test helper, and redaction rules.
- Renamed `subagent-workflow` to `pi-subagents` and narrowed it to Pi-specific orchestration policy that complements the `subagent` extension's built-in tool guidance.
- Clarified `managing-agent-context` mental model for AGENTS.md primacy, skill recency, subagent prompt/context engineering, and meta-skill audit value.
- Added explicit `managing-agent-context` guidance for shared context docs: one canonical home, thin pointers, and stale-copy cleanup.
- Added a `managing-agent-context` repository freshness contract check for maintained docs/context artifacts, update triggers, and enforcement paths.
- Refined the `managing-agent-context` TODO template guidance to keep active items short and move detail into linked plans.
- Clarified the `managing-agent-context` global-vs-repo `AGENTS.md` boundary: global defaults versus repo-local overrides, gates, and facts.
- Extended `tool-update-checker` with a `skills-root-git` check that validates every skill in a collection and compares the installed checkout against its remote, plus `--actionable-only`, `--exit-code`, and `--notify` for unattended runs.
- Extended `tool-update-checker` with read-only skill source checks for `skill-local`, `skill-git`, and `skills-sh` entries.
- Added a root `.ignore` so top-level repository docs (`README.md`, `CHANGELOG.md`) are not discovered as Pi skills, and corrected README layout docs for skill-local `scripts/` versus repo-level `_scripts/`.
- Flattened the repository so Pi discovers skill folders directly from the repo root at `~/.pi/agent/skills`.
- Renamed `manage-agent-context` to `managing-agent-context` to match the preferred gerund naming convention.
- Updated `skill-creator` naming guidance to prefer gerund skill names while allowing established noun/action names.
- Added README/CHANGELOG enforcement via a shared metadata checker, GitHub Actions workflow, and local Git hooks.

### Removed

- Removed unused or archived runtime skills from the active collection: `audit-manager`, `claude-api`, `doc-coauthoring`, `mcp-builder`, `pdf`, and `to-prd`.
- Dropped stale repo-only skills that were not present in the active runtime skill set during the flattening migration.
