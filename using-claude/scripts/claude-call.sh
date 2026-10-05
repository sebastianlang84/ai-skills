#!/usr/bin/env bash
# One headless, read-only Claude call (usually from Codex): a review, a question, a follow-up.
#
# Blocks while Claude works; the caller backgrounds it.
#
#   claude-call.sh [--review] [--resume <session-id>] <prompt-file> <output-file> <dir> [more dirs...]
#
# The first <dir> is the working directory; every <dir> is readable. Claude gets only Read, Grep
# and Glob and no MCP servers, so it cannot write anything. --review appends using-codex's review
# rules to the prompt. CLAUDE_CALL_MODEL overrides the model (default claude-opus-5-5),
# CLAUDE_CALL_EFFORT the effort (default medium).
# Writes the answer to <output-file> and the Claude session id to <output-stem>.session;
# follow up with --resume <id>, which continues that session with the same restrictions.
set -euo pipefail

usage="usage: claude-call.sh [--review] [--resume <session-id>] <prompt-file> <output-file> <dir> [more dirs...]"
review=0
resume=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --review) review=1; shift ;;
    --resume) [ -n "${2:-}" ] || { echo "$usage" >&2; exit 2; }; resume=(--resume "$2"); shift 2 ;;
    *) break ;;
  esac
done
prompt="${1:?$usage}"
out="${2:?$usage}"
shift 2
[ "$#" -ge 1 ] || { echo "$usage" >&2; exit 2; }
cwd="$1"
model="${CLAUDE_CALL_MODEL:-claude-opus-5-5}"
effort="${CLAUDE_CALL_EFFORT:-medium}"

rm -f "$out" "${out%.*}.session"
[ -r "$prompt" ] || { echo "prompt file not readable: $prompt" >&2; exit 2; }
command -v claude >/dev/null 2>&1 || { echo "claude CLI not found" >&2; exit 2; }
# The first interpreter that really runs: on Windows, python3 may be a Store stub that only prints a hint.
py=""
for c in python3 python; do
  if "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then py="$c"; break; fi
done
[ -n "$py" ] || { echo "python 3.9+ not found (tried python3, python)" >&2; exit 2; }
rules="$HOME/.agents/skills/using-codex/references/review-rules.md"
if [ "$review" = 1 ]; then
  [ -r "$rules" ] || { echo "review rules not readable: $rules" >&2; exit 2; }
fi

mkdir -p "$(dirname "$out")"
add=()
for d in "$@"; do add+=(--add-dir "$d"); done
raw="$(mktemp)"
trap 'rm -f "$raw"' EXIT
{ cat "$prompt"; if [ "$review" = 1 ]; then printf '\n'; cat "$rules"; fi; } \
  | (cd "$cwd" && claude -p "${resume[@]}" --model "$model" --effort "$effort" \
      --tools "Read,Grep,Glob" --allowedTools "Read,Grep,Glob" --strict-mcp-config "${add[@]}" \
      --output-format json) > "$raw" 2> "${out%.*}.err"
"$py" - "$raw" "$out" "${out%.*}.session" <<'PY'
import json, sys
raw, out, session = sys.argv[1:4]
try:
    d = json.load(open(raw, encoding="utf-8"))
except (OSError, ValueError) as exc:
    sys.exit(f"claude call failed: no JSON result ({exc}); see the .err file")
result, sid = (d.get("result") or "").strip(), (d.get("session_id") or "").strip()
# Anything but a successful, non-empty result is a failure: a missing review must never pass.
if d.get("type") != "result" or d.get("subtype") != "success" or d.get("is_error") or not result or not sid:
    sys.exit(f"claude call failed: type={d.get('type')} subtype={d.get('subtype')} "
             f"is_error={d.get('is_error')} result={'yes' if result else 'empty'} session={'yes' if sid else 'none'}")
open(out, "w", encoding="utf-8").write(result + "\n")
open(session, "w", encoding="utf-8").write(sid + "\n")
PY
