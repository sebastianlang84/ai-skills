#!/usr/bin/env bash
# One adversarial cross-vendor review.
#
# This blocks for as long as the reviewer thinks. That is deliberate:
# the CALLER backgrounds it, so the harness reports completion instead of the script detaching
# into something nobody is watching.
#
#   launch-review.sh <prompt-file> <output-file> [cwd]
#
# REVIEW_MODEL overrides the model (default gpt-6-sol).
# REVIEW_REASONING_EFFORT overrides the effort (default medium).
set -euo pipefail

prompt="${1:?usage: launch-review.sh <prompt-file> <output-file> [cwd]}"
out="${2:?usage: launch-review.sh <prompt-file> <output-file> [cwd]}"
cwd="${3:-$PWD}"
model="${REVIEW_MODEL:-gpt-6-sol}"
reasoning_effort="${REVIEW_REASONING_EFFORT:-medium}"

# A failed run must not leave the previous review behind as if it were this one.
rm -f "$out" "${out%.*}.thread"

[ -r "$prompt" ] || { echo "prompt file not readable: $prompt" >&2; exit 2; }
command -v codex >/dev/null 2>&1 || { echo "codex CLI not found — no cross-vendor reviewer available" >&2; exit 2; }

mkdir -p "$(dirname "$out")"

# codex-call owns the invocation: read-only sandbox, hooks off, thread kept for follow-ups.
# It blocks here; the caller backgrounds this script.
call="$HOME/.agents/skills/codex-call/scripts/codex_call.py"
raw="${out%.*}.call"
python3 "$call" new --cwd "$cwd" --label cross-vendor-review \
  --model "$model" --effort "$reasoning_effort" "$prompt" > "$raw" 2> "${out%.*}.err"
# codex-call prints `thread: <id>`, `result: <path>`, a blank line, then the answer. The output file
# keeps its old contract (the answer only); the thread id goes beside it for a follow-up.
sed -n '1s/^thread: //p' "$raw" > "${out%.*}.thread"
tail -n +4 "$raw" > "$out"
rm -f "$raw"
