#!/usr/bin/env bash
# One adversarial review by the other vendor (Codex -> Claude Opus).
#
# Blocks while the reviewer thinks; the caller backgrounds it.
#
#   launch-review-opus.sh <prompt-file> <output-file> <dir> [more dirs...]
#
# The first <dir> is the working directory; every <dir> is readable by the reviewer.
# The reviewer gets only Read, Grep and Glob and no MCP servers, so it cannot write anything.
# REVIEW_CLAUDE_MODEL overrides the model (default claude-opus-5-5),
# REVIEW_CLAUDE_EFFORT the effort (default medium).
# Writes the answer to <output-file> and the Claude session id to <output-stem>.session;
# follow up with `claude -p --resume <id>` and the same flags.
set -euo pipefail

prompt="${1:?usage: launch-review-opus.sh <prompt-file> <output-file> <dir> [more dirs...]}"
out="${2:?usage: launch-review-opus.sh <prompt-file> <output-file> <dir> [more dirs...]}"
shift 2
[ "$#" -ge 1 ] || { echo "at least one readable directory is required" >&2; exit 2; }
cwd="$1"
model="${REVIEW_CLAUDE_MODEL:-claude-opus-5-5}"
effort="${REVIEW_CLAUDE_EFFORT:-medium}"

rm -f "$out" "${out%.*}.session"
[ -r "$prompt" ] || { echo "prompt file not readable: $prompt" >&2; exit 2; }
command -v claude >/dev/null 2>&1 || { echo "claude CLI not found — no other-vendor reviewer available" >&2; exit 2; }
# The first interpreter that really runs: on Windows, python3 may be a Store stub that only prints a hint.
py=""
for c in python3 python; do
  if "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then py="$c"; break; fi
done
[ -n "$py" ] || { echo "python 3.9+ not found (tried python3, python)" >&2; exit 2; }
rules="$HOME/.agents/skills/codex-call/references/review-rules.md"
[ -r "$rules" ] || { echo "review rules not readable: $rules" >&2; exit 2; }

mkdir -p "$(dirname "$out")"
add=()
for d in "$@"; do add+=(--add-dir "$d"); done
raw="$(mktemp)"
trap 'rm -f "$raw"' EXIT
{ cat "$prompt"; printf '\n'; cat "$rules"; } | (cd "$cwd" && claude -p --model "$model" --effort "$effort" \
  --tools "Read,Grep,Glob" --allowedTools "Read,Grep,Glob" --strict-mcp-config "${add[@]}" \
  --output-format json) > "$raw" 2> "${out%.*}.err"
"$py" - "$raw" "$out" "${out%.*}.session" <<'PY'
import json, sys
raw, out, session = sys.argv[1:4]
d = json.load(open(raw, encoding="utf-8"))
if d.get("is_error"):
    sys.exit(f"review failed: {d.get('result')}")
open(out, "w", encoding="utf-8").write((d.get("result") or "") + "\n")
open(session, "w", encoding="utf-8").write((d.get("session_id") or "") + "\n")
PY
