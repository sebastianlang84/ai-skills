# Config for nightly-review-pipeline (sourced by orchestrator.sh).
# Copy to ~/.config/nightly-review/config.sh and edit. This is shell — no secrets here.

# --- Repositories -----------------------------------------------------------
# One entry per repo:  "ABSOLUTE_PATH|LENSES|TEST_CMD"
#   LENSES   : comma list of  bug  and/or  usability     (order runs left→right)
#   TEST_CMD : command run in the fix worktree; a fix PR opens only if it exits 0.
#              Leave the field empty to fall back to TEST_CMD_DEFAULT.
REPOS=(
  "/home/wasti/.pi/agent/git/github.com/sebastianlang84/pi-ext-codemap|bug,usability|npm test"
  # "/home/wasti/.pi/agent/git/.../pi-memory|bug,usability|npm test"
  # "/home/wasti/some/other/repo|bug||"            # bug only, uses TEST_CMD_DEFAULT
)

# --- Runtime ----------------------------------------------------------------
CLAUDE_BIN="claude"          # binary on PATH
MODEL=""                     # "" = account default; or e.g. claude-opus-4-8
STATE_DIR="$HOME/.local/state/nightly-review"
LOG_DIR="$STATE_DIR/logs"

# --- Adaptive cadence -------------------------------------------------------
EMPTY_RUNS_BEFORE_BACKOFF=2  # K empty runs before the interval starts doubling
BACKOFF_MAX_DAYS=14          # cap; a quiet lens is retried at most this rarely

# --- Bug lens: auto-fix policy ----------------------------------------------
AUTO_FIX=1                   # 0 = review only (write todo.md, open no PRs)
MIN_FIX_SEVERITY="high"      # low|medium|high|critical — floor to attempt a fix
MIN_FIX_CONFIDENCE="high"    # low|medium|high            — floor to attempt a fix
FIX_BASE_BRANCH="main"       # fixes branch off this and PR back into it; never committed to directly
TEST_CMD_DEFAULT=""          # used when a repo entry leaves TEST_CMD empty

# --- Run bounds (cost/runaway guards) ---------------------------------------
REVIEW_MAX_TURNS=40
REVIEW_TIMEOUT=1800          # seconds, wall-clock, per review lens run
FIX_MAX_TURNS=60
FIX_TIMEOUT=2400             # seconds, per fix run
TEST_TIMEOUT=1200            # seconds, per test-suite run
