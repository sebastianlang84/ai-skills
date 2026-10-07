#!/usr/bin/env bash
# Bounded, logged review run through codex-call (gpt-6.1-sol by default, read-only sandbox).
# Adversarial reviews on this machine run on Codex, not Claude; Claude stays the fix agent
# (run-claude.sh). The answer is handed back in run-claude's JSON contract, `{"result": "<text>"}`,
# so the orchestrator parses both the same way.
#
# Usage:
#   run-review.sh --cwd DIR --prompt-file FILE --raw FILE --log FILE [--timeout SEC] [--label L]
#
# The call is started detached and collected with `codex_call.py wait` until the deadline. At the
# deadline the call is cancelled (`codex_call.py cancel` stops the runner and codex) and reported
# as a failure, so the deadline bounds the spend, not only the wait.
#
# Env: CODEX_CALL (default ~/.agents/skills/using-harnesses/scripts/codex_call.py),
#      REVIEW_MODEL / REVIEW_EFFORT (optional; default to codex-call's pins).
set -uo pipefail

CODEX_CALL="${CODEX_CALL:-$HOME/.agents/skills/using-harnesses/scripts/codex_call.py}"

cwd=""; pf=""; raw=""; log="/dev/stderr"; wall=1800; label="nightly-review"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd) cwd=$2; shift 2;;
    --prompt-file) pf=$2; shift 2;;
    --raw) raw=$2; shift 2;;
    --log) log=$2; shift 2;;
    --timeout) wall=$2; shift 2;;
    --label) label=$2; shift 2;;
    *) echo "run-review: unknown arg: $1" >&2; exit 2;;
  esac
done
[[ -f "$pf" ]] || { echo "run-review: prompt file missing: $pf" >&2; exit 2; }
[[ -d "$cwd" ]] || { echo "run-review: cwd missing: $cwd" >&2; exit 2; }
[[ -n "$raw" ]] || { echo "run-review: --raw is required" >&2; exit 2; }
[[ -f "$CODEX_CALL" ]] || { echo "run-review: codex-call not found: $CODEX_CALL" >&2; exit 2; }

overrides=()
[[ -n "${REVIEW_MODEL:-}" ]] && overrides+=( --model "$REVIEW_MODEL" )
[[ -n "${REVIEW_EFFORT:-}" ]] && overrides+=( --effort "$REVIEW_EFFORT" )

echo "=== $(date -Is) codex-call review cwd=$cwd to=${wall}s ===" >> "$log"
# Installed before the start: a signal that lands while the call is starting is remembered and
# acted on as soon as the call directory is known, so no runner is left behind.
call=""; waiter=""; stop=""
on_signal(){
  stop=1
  [[ -n "$call" && -d "$call" ]] || return 0
  [[ -n "$waiter" ]] && kill "$waiter" 2>/dev/null
  python3 "$CODEX_CALL" cancel "$call" >> "$log" 2>&1
  echo "=== review interrupted; $call cancelled ===" >> "$log"
  exit 130
}
trap on_signal TERM INT HUP
call=$(python3 "$CODEX_CALL" new --cwd "$cwd" --label "$label" --sandbox read-only \
         "${overrides[@]}" --detach "$pf" 2>> "$log")
if [[ -z "$call" || ! -d "$call" ]]; then
  echo "=== codex-call did not start ===" >> "$log"; exit 1
fi
echo "codex-call: $call" >> "$log"
[[ -n "$stop" ]] && on_signal   # a signal arrived during the start

deadline=$(( $(date +%s) + wall ))
while :; do
  left=$(( deadline - $(date +%s) ))
  if (( left <= 0 )); then
    python3 "$CODEX_CALL" cancel "$call" >> "$log" 2>&1
    echo "=== review hit the ${wall}s limit; $call cancelled ===" >> "$log"
    exit 124
  fi
  # `wait` returns 0 done, 1 failed, 3 still running; cap each wait at what is left.
  # In the background: bash runs a trap only after a foreground command returns, and the
  # builtin `wait` is interruptible, so a TERM cancels the call at once instead of at its end.
  python3 "$CODEX_CALL" wait "$call" --timeout "$(( left < 540 ? left : 540 ))" > /dev/null 2>> "$log" &
  waiter=$!
  wait "$waiter"
  rc=$?
  [[ $rc -eq 3 ]] && continue
  break
done
if [[ $rc -ne 0 ]]; then
  echo "=== codex-call review failed rc=$rc ===" >> "$log"; exit "$rc"
fi

jq -n --rawfile r "$call/last.md" '{result: $r}' > "$raw" || { echo "=== could not write $raw ===" >> "$log"; exit 1; }
echo "=== codex-call review ok ===" >> "$log"
exit 0
