# Safety & permissions for unattended runs

An unattended agent has nobody to approve a permission prompt and nobody to catch a bad edit. The
templates are built so that the blast radius is small by construction.

## Permission modes (not `--dangerously-skip-permissions`)

- **Review lenses run `--permission-mode plan`.** Plan mode is read-only: the agent can read, search,
  and run read commands but **cannot edit files or run mutating commands**, and it does not block on
  prompts. So a review lens physically cannot change your repo — the worst case is a wasted run.
- **Fix lens runs `--permission-mode acceptEdits`.** The agent may edit files in its worktree
  (auto-accepted, no prompt) but the fix prompt forbids it from running git or the test suite. The
  **orchestrator** runs the tests, commits, pushes, and opens the PR. This avoids handing the agent
  blanket permissions while still letting it work unattended.
- `--dangerously-skip-permissions` is intentionally **not** used. If you ever switch to it, only do so
  for the fix lens, which already runs inside a disposable worktree.

`--allowedTools` (an explicit tool allowlist) is supported by `run-claude.sh` as an alternative, but
prefer permission modes: allowlist patterns containing spaces (e.g. `Bash(git log:*)`) are
version-sensitive and easy to get subtly wrong.

## Git blast radius

- Fixes are made on a fresh `nightly/fix-<id>` branch in a **throwaway worktree** cut from
  `FIX_BASE_BRANCH`. `main` is never checked out for editing and never committed to directly.
- A PR is **draft** and is opened **only if the repo's test command exits 0**. If tests fail, the
  branch and worktree are discarded — no PR, no residue.
- **No auto-merge.** Ever. You review and merge (or close) each PR yourself.
- No force-push; each finding maps to its own branch, deduped so the same bug is not re-PR'd nightly.
- If `AUTO_FIX=0`, the bug lens is pure review: it records findings in the repo's task file (or
  `REPORTS_DIR/` when `REPORT_IN_REPO=0`) and opens nothing.

## Runaway-cost guards

- Every `claude` run is bounded by `--max-turns` (turn cap) and `timeout` (wall-clock). Tune
  `REVIEW_*` / `FIX_*` in the config.
- The systemd service adds `TimeoutStartSec=6h` as a hard ceiling for the whole night.
- Adaptive backoff (see `adaptive-cadence.md`) stops spending runs on quiet, empty repos.
- Start with `MODEL=""` (account default) and few repos; widen once you trust a few nights of logs.

## Preconditions to check before enabling the timer

- `gh auth status` is logged in and the account can push + open PRs on every target repo's remote.
- Each repo has a **real** `TEST_CMD`; without it, fixes open PRs **unverified** (a loud warning is
  logged). Prefer review-only (`AUTO_FIX=0`) for repos with no usable test suite.
- The repos are ones where an occasional bad draft PR is acceptable noise. Do not point auto-fix at
  anything where an unreviewed branch/PR could trigger deploys or notify other people.
