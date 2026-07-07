#!/usr/bin/env bash
# Bounded, logged wrapper around a headless `claude -p` run.
# The scheduler/orchestrator owns *what* to run; this owns *how to run it safely*:
# a permission mode (or explicit allowlist), a turn cap, a wall-clock timeout, closed
# stdin (so the agent can never block waiting for input), and full transcript logging.
#
# Usage:
#   run-claude.sh --cwd DIR --prompt-file FILE --log FILE \
#       [--raw FILE]            capture stdout (e.g. the JSON result) here; default /dev/null
#       [--permission-mode M]   plan | acceptEdits | default | bypassPermissions
#       [--allowed "A,B,C"]     comma-separated tool allowlist (alternative to --permission-mode)
#       [--output-format F]     json (default) | text | stream-json
#       [--max-turns N]         default 40
#       [--timeout SEC]         wall-clock seconds, default 1800
#
# Env: CLAUDE_BIN (default: claude), MODEL (optional; passed to --model).
set -uo pipefail

CLAUDE_BIN="${CLAUDE_BIN:-claude}"
MODEL="${MODEL:-}"

cwd="."; pf=""; raw="/dev/null"; log="/dev/stderr"
permmode=""; allowed=""; ofmt="json"; maxturns=40; wall=1800

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd) cwd=$2; shift 2;;
    --prompt-file) pf=$2; shift 2;;
    --raw) raw=$2; shift 2;;
    --log) log=$2; shift 2;;
    --permission-mode) permmode=$2; shift 2;;
    --allowed) allowed=$2; shift 2;;
    --output-format) ofmt=$2; shift 2;;
    --max-turns) maxturns=$2; shift 2;;
    --timeout) wall=$2; shift 2;;
    *) echo "run-claude: unknown arg: $1" >&2; exit 2;;
  esac
done
[[ -f "$pf" ]] || { echo "run-claude: prompt file missing: $pf" >&2; exit 2; }

args=( -p --output-format "$ofmt" --max-turns "$maxturns" )
[[ -n "$MODEL" ]] && args+=( --model "$MODEL" )
[[ -n "$permmode" ]] && args+=( --permission-mode "$permmode" )
if [[ -n "$allowed" ]]; then
  # Split on commas only; a pattern like "Bash(git log:*)" must stay one token.
  IFS=',' read -ra _tools <<< "$allowed"
  args+=( --allowedTools "${_tools[@]}" )
fi

prompt="$(cat "$pf")"
echo "=== $(date -Is) claude cwd=$cwd perm=${permmode:-none} turns=$maxturns to=${wall}s fmt=$ofmt ===" >> "$log"
cd "$cwd" || { echo "run-claude: cannot cd $cwd" >&2; exit 3; }

# Closed stdin: an unattended agent must never block on a prompt.
if [[ "$raw" == "/dev/null" ]]; then
  timeout --signal=INT "${wall}s" "$CLAUDE_BIN" "${args[@]}" "$prompt" < /dev/null >> "$log" 2>&1
else
  timeout --signal=INT "${wall}s" "$CLAUDE_BIN" "${args[@]}" "$prompt" < /dev/null > "$raw" 2>> "$log"
fi
rc=$?
echo "=== claude rc=$rc ===" >> "$log"
exit $rc
