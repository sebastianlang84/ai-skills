#!/usr/bin/env bash
# One adversarial cross-vendor review.
#
# This blocks for as long as the reviewer thinks. That is deliberate:
# the CALLER backgrounds it, so the harness reports completion instead of the script detaching
# into something nobody is watching.
#
#   launch-review.sh <prompt-file> <output-file> [cwd]
#
# REVIEW_MODEL overrides the model (default gpt-5.6-sol).
# REVIEW_REASONING_EFFORT overrides the effort (default medium).
set -euo pipefail

prompt="${1:?usage: launch-review.sh <prompt-file> <output-file> [cwd]}"
out="${2:?usage: launch-review.sh <prompt-file> <output-file> [cwd]}"
cwd="${3:-$PWD}"
model="${REVIEW_MODEL:-gpt-5.6-sol}"
reasoning_effort="${REVIEW_REASONING_EFFORT:-medium}"

[ -r "$prompt" ] || { echo "prompt file not readable: $prompt" >&2; exit 2; }
command -v codex >/dev/null 2>&1 || { echo "codex CLI not found — no cross-vendor reviewer available" >&2; exit 2; }

mkdir -p "$(dirname "$out")"

# read-only: the reviewer reads the design, it never touches it.
# --skip-git-repo-check: the review target is often a directory tree, not one repo.
cd "$cwd" && codex exec \
  -m "$model" \
  -c model_reasoning_effort="$reasoning_effort" \
  --sandbox read-only \
  --skip-git-repo-check \
  - < "$prompt" > "$out" 2> "${out%.*}.err"
