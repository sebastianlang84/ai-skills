---
name: nightly-review-pipeline
description: Set up an unattended overnight code-review-and-fix pipeline for one or more git repos — systemd timer, bash orchestrator, headless `claude -p`.
disable-model-invocation: true
---

# Nightly review pipeline

A reproducible recipe for an **unattended, self-regulating** overnight pipeline that
reviews git repos and optionally fixes bugs as draft PRs. Adding or removing a repo is
a one-line config change; when to run is just a timer/cron entry.

Core principle: **the scheduler is dumb, the orchestrator is smart.**
The systemd timer only fires the orchestrator nightly. The orchestrator (`assets/orchestrator.sh`)
decides *per repo, per lens* whether to spend a `claude` run at all, based on saved state and
adaptive backoff. This "should I even run tonight?" logic is why a plain cron line is not enough.

## Architecture

```
systemd .timer  ──fires──▶  orchestrator.sh  ──per repo, per lens──▶  run-claude.sh (headless claude -p)
   (dumb)                     (smart: state,        │
                              backoff, dedup,       ├─ bug lens ──▶ repo's task file + draft-PR fixes
                              git/PR policy)        └─ usability ─▶ repo's ideas file (suggestions only)
```

## Review lenses

Each lens is a separate, bounded `claude -p` run (own prompt, timeout, permission mode, log).
A repo enables whichever lenses make sense for it, in the config.

- **`bug`** — correctness/security bug screen. Read-only review (`--permission-mode plan`).
  New, deduped, high-confidence findings become auto-fix **draft PRs**; all findings are also
  recorded as checkboxes in the repo's task file (see "Where findings go" below).
- **`usability`** — product/usability/functionality review. Read-only. Suggestions only,
  recorded in the repo's ideas file. **Never** opens a PR (design is a human call).

### Where findings go

Findings are written into a **marker-delimited managed block**
(`<!-- nightly-review:<lens>:start -->` … `:end`), so the pipeline owns that block and never
touches your own content. With `REPORT_IN_REPO=1` (default) it **reuses the repo's existing file,
case-insensitively** — an existing `TODO.md` is appended to, never a competing `todo.md` — falling
back to `TASK_FILE`/`IDEAS_FILE` if none exists. With `REPORT_IN_REPO=0` it writes out of the repo
under `REPORTS_DIR/<repo-slug>/` instead, leaving the repo's working tree completely untouched.
- **metrics is not a lens** — it is an *output*. When the bug or usability lens notices something
  whose quality can only be judged by measuring it (retrieval quality, recall, latency, memory hit
  rate), it emits a `metric-suggestion` item into `IDEAS.md`. You decide later whether to build an
  eval (see the `autoresearch` skill). No standing metrics scheduler.

## Adaptive cadence

The orchestrator runs a lens tonight only if **new commits arrived** since its last run, **or** the
lens is due again. After K consecutive empty runs it backs off (doubling the interval up to a cap),
so a quiet repo that yields nothing stops burning nightly runs — and wakes up automatically on the
next commit. Details and tuning: `references/adaptive-cadence.md`.

## Setup

1. **Prerequisites** (verify first): `claude` on PATH, `gh` authenticated (`gh auth status`),
   `jq`, `git`, and `timeout` (coreutils). PR mode needs push rights on each repo's remote.
2. **Copy the config** to a private location and edit it:
   ```bash
   mkdir -p ~/.config/nightly-review
   cp ~/.claude/skills/nightly-review-pipeline/assets/config.example.sh ~/.config/nightly-review/config.sh
   $EDITOR ~/.config/nightly-review/config.sh   # set REPOS, lenses per repo, test commands, thresholds
   ```
3. **Dry-run** to confirm decisions without spending runs or touching repos:
   ```bash
   ~/.claude/skills/nightly-review-pipeline/assets/orchestrator.sh --config ~/.config/nightly-review/config.sh --dry-run
   ```
4. **One real manual run** on a single repo (edit REPOS down to one first) and inspect the repo's
   task/ideas file (or `REPORTS_DIR/` if `REPORT_IN_REPO=0`), any draft PRs, and the log under
   `~/.local/state/nightly-review/logs/`.
5. **Install the timer** (systemd user units):
   ```bash
   cp assets/systemd/nightly-review.{service,timer} ~/.config/systemd/user/
   $EDITOR ~/.config/systemd/user/nightly-review.service   # fix ExecStart path/config
   systemctl --user daemon-reload
   systemctl --user enable --now nightly-review.timer
   loginctl enable-linger "$USER"   # so it runs while you are logged out
   ```
   Cron alternative: `assets/cron.example`.

Read `references/safety-and-permissions.md` before the first unattended run — it covers permission
modes, why fixes never touch `main` or auto-merge, and how to cap runaway cost.

## Safety guardrails (mandatory, enforced by the templates)

- Review lenses run read-only (`--permission-mode plan`); they cannot modify code.
- Fixes happen only in a **throwaway git worktree** on a `nightly/fix-<id>` branch off the base
  branch, never on `main`; the agent edits (`--permission-mode acceptEdits`) but the **orchestrator**
  runs tests, commits, pushes, and opens the PR.
- A fix PR is opened **only if the repo's test command passes**. No auto-merge, ever.
- Every `claude` run is bounded by `--max-turns` and a wall-clock `timeout`; everything is logged.
- Findings are deduped by hash so the same issue is not re-reported or re-PR'd every night.

## Assets

- `assets/orchestrator.sh` — the smart driver (state, backoff, dedup, render, fix flow).
- `assets/run-claude.sh` — bounded/logged wrapper around `claude -p` (permission mode, turns, timeout).
- `assets/config.example.sh` — repos, per-repo lenses + test command, thresholds, backoff knobs.
- `assets/prompts/{bug-review,usability-review,fix}.prompt.md` — the three prompt templates.
- `assets/findings.schema.json` — JSON shape the review lenses must emit.
- `assets/systemd/nightly-review.{service,timer}` and `assets/cron.example` — schedulers.

The shell/prompt files are **starter templates**: adapt `TEST_CMD`, confirm the installed
`claude` flag syntax (this was written against Claude Code 2.1.x), and always `--dry-run` first.
