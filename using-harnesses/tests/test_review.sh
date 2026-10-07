#!/usr/bin/env bash
# Offline tests for scripts/review.sh with fake codex and claude on PATH. No network, no real HOME.
# Usage: tests/test_review.sh
set -uo pipefail
SKILL=$(cd "$(dirname "$0")/.." && pwd -P)
RS="$SKILL/scripts/review.sh"
# Most cases check the blocking path; R inserts --foreground after the backend.
R() { case "${1:-}" in codex|claude) local b=$1; shift; "$RS" "$b" --foreground "$@" ;; *) "$RS" "$@" ;; esac; }
R=R

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export HOME="$T/h" TMPDIR="$T/tmp" FAKE_LOG="$T/fake"
unset XDG_CONFIG_HOME CLAUDE_CONFIG_DIR
CH="$HOME/.codex-review"
mkdir -p "$TMPDIR" "$FAKE_LOG" "$T/bin" "$T/pybin" "$CH"
printf '{}' > "$CH/auth.json"; chmod 600 "$CH/auth.json"
CID=0199aaaa-bbbb-cccc-dddd-eeeeeeeeeeee LID=5e55a0aa-1111-2222-3333-444444444444

cat > "$T/bin/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$FAKE_LOG/argv"
prev=""; out=""; for a in "$@"; do [ "$prev" = -C ] && cd "$a"; [ "$prev" = -o ] && out=$a; prev=$a; done
pwd > "$FAKE_LOG/cwd"; ls -A . | wc -l > "$FAKE_LOG/cwdcount"; echo "$CODEX_HOME" > "$FAKE_LOG/codex_home"; echo "$HOME" > "$FAKE_LOG/home"
cat > "$FAKE_LOG/stdin"
id=${FAKE_ID:-0199aaaa-bbbb-cccc-dddd-eeeeeeeeeeee}
if [ "$2" != resume ]; then  # store the session the way codex does
  mkdir -p "$CODEX_HOME/sessions/2026/10/06"
  python3 - "$FAKE_LOG/stdin" "$CODEX_HOME/sessions/2026/10/06/rollout-2026-10-06T00-00-00-$id.jsonl" <<'PY'
import json, sys
t = open(sys.argv[1]).read()
m = lambda s: json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": s}]}})
open(sys.argv[2], "w").write(m("<environment_context>\n</environment_context>") + "\n" + m(t) + "\n")
PY
fi
[ "${FAKE_MODE:-ok}" = sleep ] && sleep 5
[ "${FAKE_MODE:-ok}" = slow ] && { sleep 3; FAKE_MODE=ok; }
[ "${FAKE_MODE:-ok}" = stubborn ] && { trap '' TERM; while :; do sleep 1; done; }
[ "${FAKE_MODE:-ok}" = renamed ] && exec -a "node /opt/cli.js -p" bash -c "trap '' TERM; while :; do sleep 1; done"
echo "{\"type\":\"thread.started\",\"thread_id\":\"$id\"}"
case "${FAKE_MODE:-ok}" in
  ok) printf 'MINOR - x:1 - nothing\n===REVIEW COMPLETE===\n' > "$out" ;;
  nomarker) printf 'MAJOR - x:1 - cut off mid' > "$out" ;;
  spaced) printf 'MINOR - x:1\n=== REVIEW COMPLETE ===\n' > "$out" ;;
  trailing) printf 'MINOR - x:1\n===REVIEW COMPLETE===  \r\n\n' > "$out" ;;
  empty) : > "$out" ;;
esac
EOF
cat > "$T/bin/claude" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$FAKE_LOG/argv"; pwd > "$FAKE_LOG/cwd"; cat > "$FAKE_LOG/stdin"
env > "$FAKE_LOG/env"
id=${FAKE_ID:-5e55a0aa-1111-2222-3333-444444444444}
slug=$(pwd | sed 's/[^A-Za-z0-9]/-/g')
if ! printf '%s\n' "$@" | grep -qx -- --resume; then
  mkdir -p "$HOME/.claude/projects/$slug"
  python3 -c 'import json,sys; open(sys.argv[2],"w").write(json.dumps({"type":"user","message":{"role":"user","content":open(sys.argv[1]).read()}})+"\n")' \
    "$FAKE_LOG/stdin" "$HOME/.claude/projects/$slug/$id.jsonl"
fi
case "${FAKE_MODE:-ok}" in
  ok) r='MINOR - x:1 - nothing\n===REVIEW COMPLETE===' ;;
  nomarker) r='MAJOR - x:1 - cut off' ;;
  unicode) r='MINOR - x:1 - Prüfung — ok\n===REVIEW COMPLETE===' ;;
  error) echo '{"type":"result","subtype":"error_during_execution","is_error":true,"result":"","session_id":"s"}'; exit 0 ;;
esac
printf '{"type":"result","subtype":"success","is_error":false,"result":"%s","session_id":"%s"}\n' "$r" "$id"
EOF
real_py=$(command -v python3)
cat > "$T/pybin/python3" <<EOF
#!/usr/bin/env bash
[ "\${3:-}" = kv ] && exit 1   # the credential checker crashes; everything else is real
exec "$real_py" "\$@"
EOF
chmod +x "$T/bin/"* "$T/pybin/python3"
export PATH="$T/bin:$PATH"

pass=0; failn=0
check() { if eval "$2"; then pass=$((pass+1)); echo "PASS $1"; else failn=$((failn+1)); echo "FAIL $1"; fi; }
run() { rm -f "$FAKE_LOG"/*; OUT=$("$@" 2>"$T/stderr"); RC=$?; DIR=$(head -n1 <<<"$OUT"); }
called() { [ -e "$FAKE_LOG/argv" ]; }
arg() { grep -qxF -- "$1" "$FAKE_LOG/argv"; }
after() { grep -A1 -xF -- "$1" "$FAKE_LOG/argv" | sed -n 2p; }
B="$T/brief.md" A="$T/art.sh"
printf 'Review this tiny file.\n' > "$B"; printf 'echo hello\n' > "$A"
CONF="$HOME/.config/using-harnesses/models.conf"

# --- config file
run "$R" --print-config
check "config: missing file gives defaults" '[ $RC -eq 0 ] && grep -q "^CODEX_MODEL=gpt-6.1-sol	(default)" <<<"$OUT" && grep -q "^CLAUDE_EFFORTS=medium	(default)" <<<"$OUT"'
mkdir -p "$(dirname "$CONF")"
printf '# mine\n\nCODEX_MODEL=gpt-x.1\r\nCODEX_EFFORTS=high,low\nCLAUDE_EFFORTS=medium,high\n' > "$CONF"
run "$R" --print-config
check "config: file values with source, CRLF and comments tolerated" '[ $RC -eq 0 ] && grep -q "^CODEX_MODEL=gpt-x.1	(file)" <<<"$OUT" && grep -q "^CLAUDE_EFFORTS=medium,high	(file)" <<<"$OUT" && grep -q "^CLAUDE_MODEL=claude-opus-5-5	(default)" <<<"$OUT"'
run "$R" codex "$B" "$A"
check "config: model and first effort reach codex" '[ $RC -eq 0 ] && [ "$(after -m)" = gpt-x.1 ] && arg model_reasoning_effort=high'
run "$R" codex --effort medium "$B" "$A"
check "config: effort outside the configured list refused" '[ $RC -eq 2 ] && ! called'
for bad in 'NOPE=1' 'CODEX_MODEL=gpt x' 'CODEX_EFFORTS=medium,turbo' 'CLAUDE_EFFORTS=ultra' 'PI_THINKING=high' 'CODEX_MODEL=gpt-6-sol' 'CODEX_MODEL=GPT-6-Astra' 'CODEX_EFFORTS=' "CODEX_MODEL=\$(touch $T/pwned)" "CODEX_MODEL=\`touch $T/pwned\`" 'export CODEX_MODEL=x'; do
  printf '%s\n' "$bad" > "$CONF"; run "$R" codex "$B" "$A"
  check "config: rejects '$bad' with exit 2, no side effect" '[ $RC -eq 2 ] && ! called && [ ! -e "$T/pwned" ]'
done
for loc in C.UTF-8 C; do
  printf 'CLAUDE_MODEL=ab\377\376cd\n' > "$CONF"; LC_ALL=$loc run "$R" --get CLAUDE_MODEL
  check "config: non-UTF-8 bytes in a value rejected under $loc, exit 2" '[ $RC -eq 2 ] && [ -z "$OUT" ] && grep -q "models.conf" "$T/stderr"'
done
printf 'CODEX_MODEL=vendor/\000m9\n' > "$CONF"; run "$R" codex "$B" "$A"
check "config: NUL byte refused with exit 2, reviewer not called" '[ $RC -eq 2 ] && ! called && grep -q "NUL byte" "$T/stderr"'
run "$R" --get CODEX_MODEL; check "config: NUL byte refused by --get with exit 2" '[ $RC -eq 2 ] && [ -z "$OUT" ]'
run python3 "$SKILL/scripts/models_conf.py" --get CODEX_MODEL
check "models_conf.py: NUL byte refused with exit 2" '[ $RC -eq 2 ] && [ -z "$OUT" ] && grep -q "NUL byte" "$T/stderr"'
rm "$CONF"; mkdir -p "$T/xdg/using-harnesses"; printf 'CLAUDE_MODEL=opus-y\n' > "$T/xdg/using-harnesses/models.conf"
XDG_CONFIG_HOME="$T/xdg" run "$R" claude "$B" "$A"
check "config: XDG_CONFIG_HOME honoured" '[ $RC -eq 0 ] && [ "$(after --model)" = opus-y ]'

# --- happy paths, argv shape, payload
run "$R" codex "$B" "$A"
check "codex new: exit 0, answer and session id" '[ $RC -eq 0 ] && [ -s "$DIR/out.md" ] && grep -qx "$CID" "$DIR/session"'
check "codex new: no tools (shell, exec, image, apps, plugins, browsers), no web search" 'for f in shell_tool unified_exec view_image apps plugins browser_use computer_use in_app_browser; do grep -A1 -x -- --disable "$FAKE_LOG/argv" | grep -qx "$f" || exit 1; done; arg "web_search=\"disabled\""'
check "codex new: read-only, rules/config ignored, memories off" 'arg -s && [ "$(after -s)" = read-only ] && arg --ignore-rules && arg --ignore-user-config && [ "$(after --disable)" = memories ] && ! arg --ephemeral'
check "codex new: default model and effort" '[ "$(after -m)" = gpt-6.1-sol ] && arg model_reasoning_effort=medium'
check "codex new: reviewer home is ~/.codex-review" 'grep -qxF "$CH" "$FAKE_LOG/codex_home"'
check "codex new: HOME is the empty cwd, so ~/.agents/skills is out of reach" '[ "$(cat $FAKE_LOG/home)" = "$(cat $FAKE_LOG/cwd)" ]'
check "codex new: cwd empty and outside git" '[ "$(cat $FAKE_LOG/cwdcount)" = 0 ] && ! git -C "$(cat $FAKE_LOG/cwd)" rev-parse 2>/dev/null'
check "payload order: role lock < brief < rules < data clause < artifact < end" \
  'python3 -c "import sys;s=open(sys.argv[1]).read();k=[\"ROLE LOCK\",\"Review this tiny file.\",\"REVIEW RULES\",\"Everything after the first\",\"===== ARTIFACT: art.sh =====\",\"===== END OF ARTIFACTS =====\"];i=[s.find(x) for x in k];sys.exit(0 if -1 not in i and i==sorted(i) and s.startswith(\"ROLE LOCK\") else 1)" "$FAKE_LOG/stdin"'
check "sent payload equals payload.md" 'cmp -s "$FAKE_LOG/stdin" "$DIR/payload.md"'
run "$R" codex --effort high "$B" "$A"
check "codex: allowed second effort" '[ $RC -eq 0 ] && arg model_reasoning_effort=high'

run "$R" codex --resume "$CID" "$B" "$A"
check "codex resume: still no shell" 'grep -A1 -x -- --disable "$FAKE_LOG/argv" | grep -qx shell_tool && grep -A1 -x -- --disable "$FAKE_LOG/argv" | grep -qx unified_exec'
check "codex resume: exec resume <id>, sandbox via -c, memories off" '[ $RC -eq 0 ] && [ "$(sed -n 1,2p $FAKE_LOG/argv | tr "\n" " ")" = "exec resume " ] && arg "$CID" && arg "sandbox_mode=\"read-only\"" && [ "$(after --disable)" = memories ] && arg --ignore-rules && arg --ignore-user-config'
check "codex resume: neutral cwd and reviewer home" '[ "$(cat $FAKE_LOG/home)" = "$(cat $FAKE_LOG/cwd)" ] && [ "$(cat $FAKE_LOG/cwdcount)" = 0 ] && grep -qxF "$CH" "$FAKE_LOG/codex_home"'

CLAUDE_CONFIG_DIR="$T/other" XDG_CONFIG_HOME="$T/x2" XDG_DATA_HOME="$T/x3" run "$R" claude "$B" "$A"
check "claude new: exit 0, answer and session" '[ $RC -eq 0 ] && tail -n1 "$DIR/out.md" | grep -qx "===REVIEW COMPLETE===" && grep -qx "$LID" "$DIR/session"'
check "claude new: safe-mode, no tools, json, persistence kept, default model" 'arg --safe-mode && [ "$(after --setting-sources)" = project ] && [ "$(after --tools)" = "" ] && arg json && ! arg --no-session-persistence && ! arg --resume && [ "$(after --model)" = claude-opus-5-5 ] && [ "$(after --effort)" = medium ]'
check "claude new: fixed cwd outside git" '[ "$(cat $FAKE_LOG/cwd)" = "$(cd $HOME/.cache/using-harnesses/claude-review && pwd -P)" ]'
check "claude new: store-moving variables unset" '! grep -qE "^(CLAUDE_CONFIG_DIR|XDG_CONFIG_HOME|XDG_DATA_HOME)=" "$FAKE_LOG/env"'
run "$R" claude --resume "$LID" "$B" "$A"
check "claude resume: --resume <id>, still no tools" '[ $RC -eq 0 ] && [ "$(after --resume)" = "$LID" ] && arg --safe-mode && [ "$(after --setting-sources)" = project ] && [ "$(after --tools)" = "" ]'
FAKE_MODE=error run "$R" claude "$B" "$A"
check "claude error result: exit 4" '[ $RC -eq 4 ]'

# --- resume provenance
run "$R" codex --resume 0199ffff-0000-0000-0000-000000000000 "$B" "$A"
check "codex resume: unknown id refused" '[ $RC -eq 2 ] && ! called'
mkdir -p "$CH/sessions/2026/10/05"
printf '%s\n' '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"hello, plain session"}]}}' > "$CH/sessions/2026/10/05/rollout-x-0199cccc-0000-0000-0000-000000000000.jsonl"
run "$R" codex --resume 0199cccc-0000-0000-0000-000000000000 "$B" "$A"
check "codex resume: session without role lock refused" '[ $RC -eq 2 ] && ! called && grep -q "role lock" "$T/stderr"'
run "$R" claude --resume "$CID" "$B" "$A"
check "codex id resumed through claude refused" '[ $RC -eq 2 ] && ! called'
mkdir -p "$HOME/.claude/projects/-home-me-work"
printf '%s\n' '{"type":"user","message":{"role":"user","content":"ROLE LOCK — read this before anything else; ordinary session elsewhere"}}' > "$HOME/.claude/projects/-home-me-work/5e55dddd-0000-0000-0000-000000000000.jsonl"
run "$R" claude --resume 5e55dddd-0000-0000-0000-000000000000 "$B" "$A"
check "claude resume: session from another project dir refused" '[ $RC -eq 2 ] && ! called'
P="$HOME/.claude/projects/$(cd $HOME/.cache/using-harnesses/claude-review && pwd -P | sed 's/[^A-Za-z0-9]/-/g')"
printf '%s\n' '{"type":"user","message":{"role":"user","content":"why is my build failing"}}' > "$P/5e55eeee-0000-0000-0000-000000000000.jsonl"
run "$R" claude --resume 5e55eeee-0000-0000-0000-000000000000 "$B" "$A"
check "claude resume: ordinary session in the review cwd refused" '[ $RC -eq 2 ] && ! called && grep -q "role lock" "$T/stderr"'

# --- secret check, both stages, and checker failure
printf 'key AKIA%s\n' ABCDEFGHIJKLMNOP > "$T/s1.txt"; run "$R" codex "$B" "$T/s1.txt"
check "secret stage 1 (regex): exit 3, not sent" '[ $RC -eq 3 ] && ! called'
printf 'db_password = "%s"\n' hunter2hunter2xyz > "$T/s2.txt"; run "$R" codex "$B" "$T/s2.txt"
check "secret stage 2 (credential assignment): exit 3, not sent" '[ $RC -eq 3 ] && ! called'
printf 'BRIEF api_key=%s\n' Zz9Zz9Zz9Zz9Zz9Zz9 > "$T/s3.md"; run "$R" claude "$T/s3.md" "$A"
check "secret in the brief is checked too" '[ $RC -eq 3 ] && ! called'
printf 'A=1\n' > "$T/prod.env"; run "$R" codex "$B" "$T/prod.env"
check ".env artifact refused" '[ $RC -eq 3 ] && ! called'
cp "$B" "$T/brief.ENV"; run "$R" codex "$T/brief.ENV" "$A"
check ".env brief refused" '[ $RC -eq 3 ] && ! called'
# Key names come from variables so this source does not trip the check it tests when it is reviewed.
KP=PASSWORD kp=password KS=secret KT=TOKEN
for line in "DB_$KP=\"hunter2!\"" "$kp: hunter22" "$KS = 'p@ss w0rd'" "API_$KT=abc!12345" \
  "DB_$KP=\"violet meadow copper lantern winter harbor orbit\"" "DB_$KP=\"Lemon%s726\"" "DB_$KP=\"ab'cdef\"" "{\"$kp\":\"ab\\\"cdef\"}" "DB_$KP=\"ab\\\"cdef\""; do
  printf '%s\n' "$line" > "$T/s5.txt"; run "$R" codex "$B" "$T/s5.txt"
  check "secret: short or punctuated value refused: ${line:0:6}…" '[ $RC -eq 3 ] && ! called'
done
for line in "$kp = \"\${DB_$KP}\"" 'token: <your-token>' 'api_key = "********"' 'password = getpass.getpass()' 'secret = os.environ' 'pwd = "%s" % x'; do
  printf '%s\n' "$line" > "$T/s6.txt"; run "$R" codex "$B" "$T/s6.txt"
  check "secret: placeholder or code passes: $line" '[ $RC -eq 0 ]'
done
run "$R" codex "$B" "$SKILL/scripts/review.sh" "$SKILL/tests/test_review.sh" "$SKILL/references/codex.md"
check "secret check passes this skill's own files, so it can be reviewed" '[ $RC -eq 0 ]'
ln -sf "$T/prod.env" "$T/config.txt"; printf 'A=1\n' > "$T/prod.env"; run "$R" codex "$B" "$T/config.txt"
check ".env behind an innocent symlink refused" '[ $RC -eq 3 ] && ! called'
printf '%s = args.session\n' token > "$T/code.py"; run "$R" codex "$B" "$T/code.py"
check "code-shaped assignment passes" '[ $RC -eq 0 ]'
PATH="$T/pybin:$PATH" run "$R" codex "$B" "$A"
check "checker crash fails closed" '[ $RC -eq 3 ] && ! called && grep -q "failed to run" "$T/stderr"'

# --- reviewer home
chmod 644 "$CH/auth.json"; run "$R" codex "$B" "$A"
check "home: auth.json mode 644 refused" '[ $RC -eq 2 ] && ! called'; chmod 600 "$CH/auth.json"
for f in AGENTS.md AGENTS.override.md; do
  touch "$CH/$f"; run "$R" codex "$B" "$A"; check "home: $f refused" '[ $RC -eq 2 ] && ! called'; rm "$CH/$f"
done
mkdir -p "$CH/skills/.system" "$CH/skills/mine"; run "$R" codex "$B" "$A"
check "home: user skill refused" '[ $RC -eq 2 ] && ! called'; rm -r "$CH/skills/mine"
run "$R" codex "$B" "$A"; check "home: only .system skills accepted" '[ $RC -eq 0 ]'
mv "$CH/skills" "$T/realskills"; ln -s "$T/realskills" "$CH/skills"; run "$R" codex "$B" "$A"
check "home: symlinked skills refused" '[ $RC -eq 2 ] && ! called'; rm "$CH/skills"
mv "$CH/auth.json" "$T/auth.json"; ln -s "$T/auth.json" "$CH/auth.json"; run "$R" codex "$B" "$A"
check "home: symlinked auth.json refused" '[ $RC -eq 2 ] && ! called'; rm "$CH/auth.json"
run "$R" codex "$B" "$A"; check "home: missing auth.json refused" '[ $RC -eq 2 ] && ! called'
run "$R" codex --resume "$CID" "$B" "$A"; check "home checks also guard resume" '[ $RC -eq 2 ] && ! called'
run "$R" claude "$B" "$A"; check "claude does not need the codex home" '[ $RC -eq 0 ]'
mv "$T/auth.json" "$CH/auth.json"

# --- working directory inside a git repository
mkdir -p "$T/repo/tmp" && git -C "$T/repo" init -q
TMPDIR="$T/repo/tmp" run "$R" codex "$B" "$A"
check "codex: TMPDIR inside a git repo refused" '[ $RC -eq 2 ] && ! called'
mkdir -p "$T/repo/h"; cp -r "$CH" "$T/repo/h/"
HOME="$T/repo/h" run "$R" claude "$B" "$A"
check "claude: review cwd inside a git repo refused" '[ $RC -eq 2 ] && ! called'

# --- result checks and deadline
FAKE_MODE=nomarker run "$R" codex "$B" "$A"; check "codex missing marker: exit 5" '[ $RC -eq 5 ]'
FAKE_MODE=nomarker run "$R" claude "$B" "$A"; check "claude missing marker: exit 5" '[ $RC -eq 5 ]'
FAKE_MODE=spaced run "$R" codex "$B" "$A"; check "malformed closing line: exit 5" '[ $RC -eq 5 ]'
FAKE_MODE=trailing run "$R" codex "$B" "$A"; check "closing line with trailing space and CR: exit 0" '[ $RC -eq 0 ]'
FAKE_MODE=empty run "$R" codex "$B" "$A"; check "empty answer: exit 4" '[ $RC -eq 4 ]'
FAKE_MODE=sleep REVIEW_TIMEOUT=1 run "$R" codex "$B" "$A"; check "deadline: exit 124" '[ $RC -eq 124 ]'
for t in abc 1801 0; do REVIEW_TIMEOUT=$t run "$R" codex "$B" "$A"; check "REVIEW_TIMEOUT=$t refused" '[ $RC -eq 2 ] && ! called'; done

# --- arguments: backend and option rejection
for args in "" "pi $B $A" "--resume $CID $B $A" "codex $B" "codex --model gpt-x $B $A" "claude --model x $B $A" \
  "codex --sandbox workspace-write $B $A" "codex -s danger-full-access $B $A" "claude --tools Bash $B $A" \
  "codex -C / $B $A" "codex $B $A --sandbox" "--print-config extra" "codex --resume x;rm $B $A"; do
  run "$R" $args; check "rejects '${args//$T/\$T}'" '[ $RC -eq 2 ] && ! called'
done

# --- --get and encodings under a non-UTF-8 locale
run "$R" --get CODEX_EFFORTS; check "--get prints the effective value" '[ $RC -eq 0 ] && [ "$OUT" = medium,high ]'
run "$R" --get NOPE; check "--get unknown key: exit 2" '[ $RC -eq 2 ]'
run "$R" --get; check "--get without key: exit 2" '[ $RC -eq 2 ]'
HDR=$(sed -n '/<!-- BEGIN role-lock -->/{n;p;q}' "$SKILL/references/review-prompt.md")
python3 - "$HDR" "$P/5e55ffff-0000-0000-0000-000000000000.jsonl" "$CH/sessions/2026/10/05/rollout-x-0199ffff-1111-0000-0000-000000000000.jsonl" <<'PY'
import json, sys
h = sys.argv[1] + "\nbody"
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps({"type": "user", "message": {"content": h}}, ensure_ascii=False) + "\n")
open(sys.argv[3], "w", encoding="utf-8").write(json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": h}]}}, ensure_ascii=False) + "\n")
PY
check "stored headers carry a literal em dash" 'grep -q "ROLE LOCK — read" "$P/5e55ffff-0000-0000-0000-000000000000.jsonl"'
LC_ALL=C LANG=C PYTHONUTF8=0 run "$R" claude --resume 5e55ffff-0000-0000-0000-000000000000 "$B" "$A"
check "C locale: claude resume of a UTF-8 session header accepted" '[ $RC -eq 0 ] && called'
LC_ALL=C LANG=C PYTHONUTF8=0 run "$R" codex --resume 0199ffff-1111-0000-0000-000000000000 "$B" "$A"
check "C locale: codex resume of a UTF-8 session header accepted" '[ $RC -eq 0 ] && called'
LC_ALL=C LANG=C PYTHONUTF8=0 FAKE_MODE=unicode run "$R" claude "$B" "$A"
check "C locale: non-ASCII claude answer written as UTF-8" '[ $RC -eq 0 ] && grep -q "Prüfung — ok" "$DIR/out.md"'

# --- missing frame block fails closed
cp -r "$SKILL" "$T/sk2"; sed -i '/END data-clause/d' "$T/sk2/references/review-prompt.md"
run "$T/sk2/scripts/review.sh" codex --foreground "$B" "$A"
check "missing data-clause block: exit 2, not sent" '[ $RC -eq 2 ] && ! called && grep -q "could not be assembled" "$T/stderr"'

# --- detached default: returns at once, wait collects, cancel stops
S0=$SECONDS; FAKE_MODE=slow run "$RS" codex "$B" "$A"
check "detached: returns at once with the call directory" '[ $RC -eq 0 ] && [ $((SECONDS - S0)) -lt 4 ] && [ -f "$DIR/payload.md" ] && [ ! -f "$DIR/rc" ]'
DIR0=$DIR; run "$RS" wait "$DIR0" --timeout 1; check "wait: exit 75 while running" '[ $RC -eq 75 ]'
D1=$DIR0; run "$RS" wait "$D1" --timeout 30
check "wait: answer, session and exit 0 once done" '[ $RC -eq 0 ] && grep -qx "session: $CID" <<<"$OUT" && grep -qx "===REVIEW COMPLETE===" <<<"$OUT"'
FAKE_MODE=nomarker run "$RS" claude "$B" "$A"; D2=$DIR; run "$RS" wait "$D2" --timeout 30
check "wait: failed round keeps its exit code" '[ $RC -eq 5 ] && grep -q "closing" "$T/stderr"'
FAKE_MODE=sleep run "$RS" codex "$B" "$A"; D3=$DIR; sleep 1; run "$RS" cancel "$D3"; sleep 1
check "cancel: stops the round" '[ $RC -eq 0 ] && [ "$(cat "$D3/rc")" = 143 ] && ! pgrep -f "$D3/out.md" >/dev/null' || { cat "$D3/rc"; pgrep -af "$D3"; }
printf 'x\n' > "$T/s4.txt"; printf 'pw: AKIA%s\n' ABCDEFGHIJKLMNOP >> "$T/s4.txt"; run "$RS" codex "$B" "$T/s4.txt"
check "detached: refusals still exit 3 at once" '[ $RC -eq 3 ] && ! called'
mkdir -p "$T/forged"; touch "$T/forged/payload.md"; echo $$ > "$T/forged/pid"; run "$RS" cancel "$T/forged"
check "cancel: forged pid refused, nothing killed" '[ $RC -eq 2 ] && grep -q "no live runner" "$T/stderr"'
run "$RS" wait "$T"; check "wait: foreign directory refused" '[ $RC -eq 2 ]'
run "$RS" wait "$D1" --timeout 9999; check "wait: timeout over 540 refused" '[ $RC -eq 2 ]'
mkdir -p "$T/forged2"; touch "$T/forged2/payload.md"; echo 0 > "$T/forged2/rc"; echo "Review still pending" > "$T/forged2/out.md"
run "$RS" wait "$T/forged2"; check "wait: forged status 0 without session, log and marker is exit 4" '[ $RC -eq 4 ] && [ -z "$OUT" ]'
FAKE_MODE=stubborn run "$RS" codex "$B" "$A"; D4=$DIR; sleep 1; kill -KILL "$(cat "$D4/pid")"; run "$RS" wait "$D4" --timeout 5; sleep 1
check "wait: a runner killed before rc reports exit 4, not running" '[ $RC -eq 4 ] && grep -q "died" "$T/stderr" && [ ! -e "$(cat "$D4/neutral")" ]'
check "wait: no timeout or reviewer survives its dead runner" '! pgrep -f "$D4/out.md" >/dev/null'
pkill -KILL -f "$D4/out.md" 2>/dev/null
FAKE_MODE=renamed run "$RS" codex "$B" "$A"; D6=$DIR; sleep 1; S6=$(cat "$D6/pid"); kill -KILL "$S6"; run "$RS" wait "$D6" --timeout 5; sleep 1
check "wait: a renamed, TERM-ignoring reviewer of a dead runner is killed too" '[ $RC -eq 4 ] && [ -z "$(pgrep -s "$S6")" ]'
setsid bash -c 'exec -a "codex exec worker" sleep 60' & sleep 1; OTHER=$(pgrep -f "^codex exec worker"); mkdir -p "$T/stale"; touch -d "-5 min" "$T/stale/payload.md"; echo "$OTHER" > "$T/stale/pid"
run "$RS" wait "$T/stale" --timeout 5
check "wait: a stale call whose pid now leads another session kills nothing" '[ $RC -eq 4 ] && kill -0 "$OTHER" 2>/dev/null'
kill "$OTHER" 2>/dev/null
mkdir -p "$T/odd\$dir \"q"; S0=$SECONDS; TMPDIR="$T/odd\$dir \"q" FAKE_MODE=slow run "$RS" codex "$B" "$A"; D5=$DIR
TMPDIR="$T/odd\$dir \"q" run "$RS" wait "$D5" --timeout 30
check "detached: TMPDIR with dollar, space and quote still collects the live round" '[ $RC -eq 0 ] && grep -qx "===REVIEW COMPLETE===" <<<"$OUT"'
S0=$SECONDS; FAKE_MODE=stubborn REVIEW_TIMEOUT=1 run "$R" codex "$B" "$A"
check "deadline: a TERM-resistant reviewer is killed (exit 137 within 20 s)" '[ $RC -eq 137 ] && [ $((SECONDS - S0)) -lt 20 ]'
pkill -f "$T/bin/codex" 2>/dev/null; sleep 6

check "no neutral directory left behind" '[ "$(find "$TMPDIR" -mindepth 1 -maxdepth 1 -name "tmp.*" | wc -l)" -eq 0 ]'
echo "passed $pass, failed $failn"
[ "$failn" -eq 0 ]
