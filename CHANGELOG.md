# Changelog

Operator-facing changes to this global skill collection are documented here.

This repo does not version individual skills with SemVer. Use this changelog to record skill additions, removals, renames, source-of-truth changes, and enforcement changes.

## [Unreleased]

### Added

- Added `handoff`: compacts the current conversation into a document a fresh session — or a different harness — can resume from, covering state, decisions and their reasons, open questions, suggested skills, and Git state. Written to the scratchpad, never into a repo, with secrets redacted because the document gets pasted elsewhere. User-invoked.
- Added `resolving-merge-conflicts`: resolve an in-progress merge or rebase hunk by hunk, by tracing each side's original intent through commit messages, PRs, and linked issues rather than picking whichever side looks tidier. Adapted to this collection's approval gates — resolving is repair work, but finishing the operation is proposed and waits for the operator, and `--abort` is never the agent's call because it discards the resolution. Adapted from Matt Pocock's skill (MIT).
- Added `git-guardrails`: a `PreToolUse` hook that refuses irreversible Git commands before they execute, turning `git-workflow`'s prose rule into enforcement. It follows one rule — block the force variant, allow the guarded one: `push --force`/`+refspec`/`--delete`, `reset --hard`, `clean -f`, wholesale `checkout .`/`restore .`, `stash drop`/`clear`, `branch -D`, and `filter-branch`/`filter-repo` are blocked, while `--force-with-lease`, `branch -d`, `clean -n`, targeted `restore <path>`, `rebase`, and `commit --amend` stay available. Commit and tag messages are blanked before matching so prose cannot trigger a rule. Verified against 40 cases plus an end-to-end block in a live session.
- Added `diagnosing-bugs`: a six-phase discipline for hard bugs, flaky failures, and performance regressions. Its rule is that no hypothesis may be formed until one named command exists that has already been run and goes **red** on this specific bug — tight, deterministic, fast, agent-runnable. Loop recipes are written for this machine (curl against a running service, `docker compose run --rm`, the unit command from `systemctl --user cat` in the foreground, bisecting image tags), because system log access here is restricted. Adapted from Matt Pocock's `diagnosing-bugs` skill (MIT).
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

- Added `references/skill-design-theory.md` to `skill-creator` and wired two steps into its workflow: choose the invocation deliberately (model-invoked costs context every turn, user-invoked costs the operator's memory) and prune with a sentence-by-sentence no-op test before finishing. The reference covers the information hierarchy, completion criteria, leading words, and the failure modes — no-op, negation, negative space, premature completion, duplication, sediment, sprawl. Adapted from Matt Pocock's `writing-great-skills` (MIT).
- Added the tautological-test anti-pattern to `tdd` — an assertion whose expected value is recomputed the way the code computes it passes by construction and can never fail. Distinct from implementation coupling, and previously not covered at all. Also introduced **seam** as the unit to agree before testing ("no test at an unconfirmed seam"), and dropped the last reference to a project domain glossary this collection no longer maintains.
- Marked `newsletter-delivery`, `releasing-pi-packages`, and `nightly-review-pipeline` user-invoked (`disable-model-invocation`). Each one sends, publishes, or installs a systemd timer, so it should fire only when typed — not when the model infers it from prose.
- Shortened the `autoresearch`, `nightly-review-pipeline`, `releasing-pi-packages`, and `newsletter-delivery` descriptions to one trigger per branch. Descriptions load into context on every turn, and these four carried 2,019 characters between them; they now carry 710, with the same reach.
- Taught `skill-creator`'s validator to accept Claude Code's frontmatter extensions (`disable-model-invocation`, `model`, `effort`, `paths`, `context`, …) instead of rejecting them as unknown keys. They now pass with a note that the skill is Claude-Code-specific; genuinely unknown keys still fail. This unblocks marking skills user-invoked.
- Corrected the `nightly-review-pipeline` description, which still promised findings in `todo.md` / `IDEAS.md` after the move to a managed block in the repo's own files.
- Changed `nightly-review-pipeline` to write findings into a marker-delimited managed block (`<!-- nightly-review:<lens>:start -->`) inside the repo's existing task and ideas files, instead of appending to hardcoded `todo.md` / `IDEAS.md`. The pipeline owns only that block and never touches surrounding content.
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
