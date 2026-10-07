#!/usr/bin/env bash
# review.sh — send one adversarial review round to codex or claude with fixed, contained flags.
#
#   review.sh <codex|claude> [--foreground] [--resume <id>] [--effort <level>] <brief-file> <artifact-file>...
#   review.sh wait <dir> [--timeout <s>]  |  review.sh cancel <dir>
#   review.sh --print-config | --get <KEY>
#
# Builds the payload from ../references/review-prompt.md (role lock, brief, rules, data clause,
# artifacts), refuses secrets and `.env` inputs (exit 3), and runs the reviewer contained: codex in
# CODEX_HOME=~/.codex-review, read-only, memories off, in an empty directory outside git that is also its
# HOME; claude with
# --safe-mode --setting-sources project --tools "" in ~/.cache/using-harnesses/claude-review. --resume
# continues only a session this script started. Models: defaults and
# ${XDG_CONFIG_HOME:-~/.config}/using-harnesses/models.conf, both through models_conf.py.
# REVIEW_TIMEOUT may lower the 1800 s deadline. The only stdout line is a private directory (out.md,
# session, err.txt, why, payload.md, raw log, rc). Every check runs before that line; the reviewer then
# runs detached in its own session and the call returns at once. `wait` prints "session: <id>", a
# blank line and the answer, and exits with the round's status; it exits 75 while the round still runs.
# --foreground blocks instead and exits with the round's status. Status: reviewer's own (124 =
# deadline, 143 = cancelled), 2 = usage, config or unsafe environment, 3 = payload refused, 4 = no
# answer or session id, 5 = answer lacks the closing ===REVIEW COMPLETE=== line. Details:
# ../references/review.md.
set -euo pipefail
die() { echo "review.sh: $1" >&2; exit "${2:-2}"; }
usage() { die "usage: review.sh <codex|claude> [--foreground] [--resume <id>] [--effort <level>] <brief-file> <artifact-file>... | wait <dir> [--timeout <s>] | cancel <dir> | --print-config | --get <KEY>"; }
here=$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")" && pwd -P)
refs="$here/../references"
[ -n "${HOME:-}" ] || die "HOME is not set"

py=""; for c in python3 python; do "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null && { py=$c; break; }; done
[ -n "$py" ] || die "python 3.9 or newer not found"
mc="$here/models_conf.py"   # the one models.conf parser; exit 2 on a config error
case "${1:-}" in --get|--print-config) exec "$py" "$mc" "$@" ;; esac

# wait <dir> [--timeout s]: print the answer when the round has ended (exit = its status), or exit 75
# while it still runs. cancel <dir>: stop a running round.
# True when $1/pid names a live runner of exactly this call: its command line carries run_reviewer
# and this call's id, so a forged pid file cannot point cancel at another process.
runner_of() {
  local cmdline
  pid=$(cat "$1/pid" 2>/dev/null) && [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  cmdline=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null) || return 1
  [[ "$cmdline" == *"declare -- callid=\"$(basename -- "$1")\""* && "$cmdline" == *run_reviewer* ]]
}
# Stop every process of a runner's session, whatever its name (a CLI may re-exec as node or python).
# Called with "live" only after runner_of proved the leader is this call's runner. Called with "dead"
# when that runner is gone: Linux reuses no pid while a process still carries it as session id, so
# members of session $1 are this call's leftovers exactly when no process $1 exists; a live process
# with that pid is a reuse and nothing is signalled.
stop_session() {
  local sid=$1 mode=$2 sig
  [ "$mode" = live ] || ! kill -0 "$sid" 2>/dev/null || return 0
  for sig in TERM KILL; do   # KILL after a grace period: a reviewer may ignore TERM
    pkill -"$sig" -s "$sid" 2>/dev/null || true
    [ "$sig" = KILL ] || sleep 2
  done
  return 0
}
case "${1:-}" in
  wait|cancel)
    cmd=$1 dir=${2:-}; [ -n "$dir" ] || usage; shift 2
    limit=540
    if [ "$cmd" = wait ] && [ "$#" -gt 0 ]; then
      [ "$#" -eq 2 ] && [ "$1" = --timeout ] && [[ "$2" =~ ^[0-9]{1,3}$ ]] && [ "$2" -le 540 ] || usage; limit=$2
    else [ "$#" -eq 0 ] || usage; fi
    [ -d "$dir" ] && [ -O "$dir" ] && [ -f "$dir/payload.md" ] || die "not a review.sh call directory: $dir"
    if [ "$cmd" = cancel ]; then
      [ ! -f "$dir/rc" ] || { echo "already ended with exit $(cat "$dir/rc")"; exit 0; }
      runner_of "$dir" || die "no live runner of $dir; nothing stopped"
      # timeout puts codex or claude into a process group of its own; the session holds them all.
      stop_session "$pid" live
      n=$(cat "$dir/neutral" 2>/dev/null) && [[ "$n" == "${TMPDIR:-/tmp}"/tmp.* ]] && rm -rf -- "$n"
      echo 143 > "$dir/rc"; echo "review.sh: cancelled" >> "$dir/why"; echo cancelled; exit 0
    fi
    end=$((SECONDS + limit))
    while [ ! -f "$dir/rc" ]; do
      # A runner that died without publishing rc (SIGKILL, OOM) would otherwise read as running forever.
      started=$(stat -c %Y "$dir/payload.md")
      if { [ -f "$dir/pid" ] && ! runner_of "$dir"; } || { [ ! -f "$dir/pid" ] && [ $(( $(date +%s) - started )) -gt 60 ]; }; then
        [ -f "$dir/rc" ] && break
        p=$(cat "$dir/pid" 2>/dev/null) && [[ "$p" =~ ^[0-9]+$ ]] && stop_session "$p" dead
        n=$(cat "$dir/neutral" 2>/dev/null) && [[ "$n" == "${TMPDIR:-/tmp}"/tmp.* ]] && rm -rf -- "$n"
        echo "review.sh: the runner died before it finished; see $dir/err.txt" >> "$dir/why"; echo 4 > "$dir/rc"; break
      fi
      [ "$SECONDS" -lt "$end" ] || { echo "still running: $dir" >&2; exit 75; }
      sleep 2
    done
    rc=$(cat "$dir/rc")
    [[ "$rc" =~ ^[0-9]+$ ]] || die "corrupt status in $dir/rc"
    if [ "$rc" = 0 ]; then   # recheck what success means; never trust the status file alone
      [ -s "$dir/session" ] && { [ -s "$dir/log.jsonl" ] || [ -s "$dir/log.json" ]; } \
        && [ "$(grep -v '^[[:space:]]*$' "$dir/out.md" 2>/dev/null | tail -n 1 | sed 's/[[:space:]]*$//')" = "===REVIEW COMPLETE===" ] \
        || { echo "review.sh: status 0 without a complete answer, session and log in $dir" >&2; exit 4; }
      echo "session: $(cat "$dir/session")"; echo; cat "$dir/out.md"; [ -z "$(tail -c 1 "$dir/out.md")" ] || echo
    else
      [ ! -s "$dir/why" ] || cat "$dir/why" >&2
    fi
    exit "$rc" ;;
esac

backend=${1:-}; case "$backend" in codex|claude) shift ;; *) usage ;; esac
B=${backend^^} resume="" effort="" foreground=0 home=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --foreground) foreground=1; shift ;;
    --resume) [ "$#" -ge 2 ] || usage; resume=$2; shift 2 ;;
    --effort) [ "$#" -ge 2 ] || usage; effort=$2; shift 2 ;;
    -*) usage ;;
    *) break ;;
  esac
done
[ "$#" -ge 2 ] || usage
model=$("$py" "$mc" --get "${B}_MODEL") || exit 2
efforts=$("$py" "$mc" --get "${B}_EFFORTS") || exit 2
effort=${effort:-${efforts%%,*}}
[[ ",$efforts," == *",$effort,"* ]] || die "effort $effort not allowed for $backend (allowed: $efforts)"
[ -z "$resume" ] || [[ "$resume" =~ ^[A-Za-z0-9-]{8,64}$ ]] || die "invalid resume id"
brief=$1; shift
for f in "$brief" "$@"; do
  case "$f" in -*) usage ;; esac
  [ -f "$f" ] && [ -r "$f" ] || die "not a readable file: $f"
  for n in "$f" "$(readlink -f -- "$f")"; do   # the name given and the file it resolves to
    case "$(basename -- "$n" | tr 'A-Z' 'a-z')" in *.env*) die "payload refused: $f is or points to an excluded (.env) file" 3 ;; esac
  done
done
deadline=${REVIEW_TIMEOUT:-1800}
[[ "$deadline" =~ ^[1-9][0-9]{0,3}$ ]] && [ "$deadline" -le 1800 ] || die "REVIEW_TIMEOUT must be 1..1800 seconds"
read -r -d '' PYSRC <<'EOF' || true
import json, re, sys, os
cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "kv":  # credential-named assignment whose value is neither code nor a placeholder
    # A false rejection costs a resend, a false pass a leaked secret: short and punctuated values count.
    kv = re.compile(r'[A-Za-z0-9_]*(api[_-]?key|secret|password|passwd|pwd|token|credential)[A-Za-z0-9_]*["\']?'
                    r'\s*[:=]\s*(?:(["\'])((?:\\.|(?!\2)[^\\\r\n]){6,})\2|()([^\s"\'#;,(){}\[\]<>]{6,})(\(?))', re.I)
    name = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*')
    chain = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+')
    placeholder = re.compile(r'[*xX.<>-]+|<[^>]*>|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|%\(?\w*\)?s|\{\w*\}'
                             r'|(changeme|example|redacted|placeholder|dummy|secret|password|token)', re.I)
    def harmless(m):
        q, qv, _, v, call = m.groups()[1:]
        if q:  # only a value that is a placeholder as a whole; passphrases with spaces count
            return bool(placeholder.fullmatch(qv))
        return bool(placeholder.fullmatch(v)) or (bool(name.fullmatch(v)) if call else bool(chain.fullmatch(v)) and not re.search(r'[0-9]', v))
    with open(args[0], encoding="utf-8", errors="replace") as f:
        sys.exit(0 if any(not harmless(m) for l in f for m in kv.finditer(l)) else 10)
if cmd == "first":  # does the stored session's first user message open with the role lock?
    backend, path, head = args
    head = os.fsencode(head).decode("utf-8", "replace")  # argv decodes by locale; the file is UTF-8
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try: e = json.loads(line)
            except ValueError: continue
            if backend == "codex":
                p = e.get("payload") or {}
                if e.get("type") != "response_item" or p.get("type") != "message" or p.get("role") != "user": continue
                c = p.get("content")
            else:
                if e.get("type") != "user": continue
                c = (e.get("message") or {}).get("content")
            t = c if isinstance(c, str) else "".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
            if backend == "codex" and t.lstrip().startswith("<environment_context>"): continue
            sys.exit(0 if t.lstrip().startswith(head) else 1)
    sys.exit(1)
if cmd == "extract":  # session id (both) and answer (claude) from the raw log
    backend, out = args
    sid = ""
    if backend == "codex":
        for line in open(os.path.join(out, "log.jsonl"), encoding="utf-8", errors="replace"):
            try: e = json.loads(line)
            except ValueError: continue
            if isinstance(e, dict) and e.get("type") == "thread.started": sid = str(e.get("thread_id") or "")
    else:
        d = json.load(open(os.path.join(out, "log.json"), encoding="utf-8", errors="replace"))
        if d.get("type") != "result" or d.get("subtype") != "success" or d.get("is_error"):
            sys.exit("claude returned no successful result; see log.json")
        sid, r = str(d.get("session_id") or ""), (d.get("result") or "").strip()
        open(os.path.join(out, "out.md"), "w", encoding="utf-8").write(r + "\n" if r else "")
    if not sid: sys.exit("no session id in the reviewer's log")
    open(os.path.join(out, "session"), "w", encoding="utf-8").write(sid + "\n")
EOF
pyh() { "$py" -c "$PYSRC" "$@"; }

umask 077
outdir=$(mktemp -d "${TMPDIR:-/tmp}/review.XXXXXXXX") && outdir=$(cd "$outdir" && pwd -P)
neutral=""; trap '[ -z "$neutral" ] || rm -rf "$neutral"' EXIT
fail() { rm -rf "$outdir"; die "$1" "$2"; }
block() { awk -v b="<!-- BEGIN $1 -->" -v e="<!-- END $1 -->" \
  '$0 == e { if (on) done = 1; on = 0 } on { print } $0 == b { on = 1 } END { exit !done }' "$refs/review-prompt.md"; }
head_line=$(block role-lock) && head_line=${head_line%%$'\n'*} && [ -n "$head_line" ] || fail "review-prompt.md has no role-lock block" 2
payload="$outdir/payload.md"
( block role-lock && printf '\n' && cat -- "$brief" && printf '\n\n' && block rules && printf '\n' && block data-clause \
  && for f in "$@"; do printf '\n\n===== ARTIFACT: %s =====\n' "$(basename -- "$f")" && cat -- "$f" || exit 1; done \
  && printf '\n\n===== END OF ARTIFACTS =====\n' ) > "$payload" || fail "payload could not be assembled (review-prompt.md block or input missing)" 2

# Two-stage secret check on the exact copy that is sent; any error fails closed.
sig_re='-----BEGIN [A-Z ]*PRIVATE KEY-----|(^|[^A-Za-z0-9])(sk|pk|rk)-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|[a-z][a-z0-9+.-]*://[^/[:space:]:@]+:[^/[:space:]@]+@'
grc=0; grep -Eiq -- "$sig_re" "$payload" || grc=$?
[ "$grc" -eq 1 ] && { grc=0; pyh kv "$payload" || grc=$?; case "$grc" in 10) grc=1 ;; 0) ;; *) grc=2 ;; esac; }
[ "$grc" -eq 0 ] && fail "payload refused: it matches a secret pattern; redact or exclude it" 3
[ "$grc" -eq 1 ] || fail "payload refused: the secret check failed to run" 3

if [ "$backend" = codex ]; then
  home="$HOME/.codex-review" auth="$HOME/.codex-review/auth.json"
  [ -f "$auth" ] && [ ! -L "$auth" ] || fail "no own reviewer login in $home; run once: CODEX_HOME=$home codex login --device-auth" 2
  [ -O "$auth" ] && [ "$(stat -c %a "$auth")" = 600 ] || fail "$auth must be yours with mode 600" 2
  for f in AGENTS.md AGENTS.override.md; do [ ! -e "$home/$f" ] || fail "$home/$f exists; the reviewer home must carry no instructions" 2; done
  if [ -e "$home/skills" ]; then
    [ ! -L "$home/skills" ] && [ ! -L "$home/skills/.system" ] || fail "$home/skills must not be a symlink" 2
    extra=$(find "$home/skills" -mindepth 1 -maxdepth 1 ! -name .system) || fail "cannot read $home/skills" 2
    [ -z "$extra" ] || fail "${extra%%$'\n'*} is a user skill; the reviewer home must carry only built-in skills" 2
  fi
  neutral=$(mktemp -d) || fail "could not create a working directory" 2; cwd=$neutral
  [ -z "$resume" ] || stored=$(find "$home/sessions" -type f -name "rollout-*$resume.jsonl" 2>/dev/null | head -n 1 || true)
else
  cwd="$HOME/.cache/using-harnesses/claude-review"
  mkdir -p "$cwd" && chmod 700 "$cwd" || fail "cannot create $cwd" 2
  [ -z "$resume" ] || stored=$(ls -1 "$HOME"/.claude/projects/*-using-harnesses-claude-review/"$resume.jsonl" 2>/dev/null | head -n 1 || true)
fi
# codex reads AGENTS.md from the enclosing git root down to its working directory.
! git -C "$cwd" rev-parse --git-dir >/dev/null 2>&1 || fail "working directory $cwd lies inside a git repository" 2
if [ -n "$resume" ]; then
  [ -n "${stored:-}" ] || fail "session $resume was not started by review.sh for $backend; start a new one" 2
  pyh first "$backend" "$stored" "$head_line" || fail "session $resume does not open with the role lock; start a new one" 2
fi
echo "$outdir"

# Runs the reviewer and leaves its exit status in $outdir/rc; the caller collects it with `wait`.
run_reviewer() {
  local rc=0
  echo "$BASHPID" > "$outdir/pid"
  [ -z "$neutral" ] || echo "$neutral" > "$outdir/neutral"
  # No tools at all: with a shell, read-only still lets codex read any file of the user (measured).
  local codex_common=(--json --skip-git-repo-check --ignore-rules --ignore-user-config --disable memories
    --disable shell_tool --disable unified_exec --disable view_image --disable apps --disable plugins
    --disable browser_use --disable computer_use --disable in_app_browser -c web_search='"disabled"'
    -m "$model" -c model_reasoning_effort="$effort" -o "$outdir/out.md")
  case "$backend" in
    codex)
      if [ -z "$resume" ]; then set -- exec "${codex_common[@]}" -C "$cwd" -s read-only -
      else set -- exec resume "${codex_common[@]}" -c sandbox_mode='"read-only"' "$resume" -; fi
      # HOME=the empty cwd: codex also discovers user skills in $HOME/.agents/skills (measured, 0.160.1).
      ( cd "$cwd" && HOME="$cwd" CODEX_HOME="$home" exec timeout --kill-after=10 "$deadline" codex "$@" \
        < "$payload" > "$outdir/log.jsonl" 2> "$outdir/err.txt" ) || rc=$? ;;
    claude)
      set -- -p --safe-mode --setting-sources project --tools "" --output-format json --model "$model" --effort "$effort"
      [ -z "$resume" ] || set -- "$@" --resume "$resume"
      ( cd "$cwd" && exec env -u CLAUDE_CONFIG_DIR -u CLAUDE_CODE_PROJECT_DIR_NAME -u CLAUDE_CODE_RESUME_FROM_SESSION \
        -u CLAUDE_CODE_SESSION_LOG -u XDG_CONFIG_HOME -u XDG_DATA_HOME -u XDG_STATE_HOME -u XDG_CACHE_HOME \
        timeout --kill-after=10 "$deadline" claude "$@" < "$payload" > "$outdir/log.json" 2> "$outdir/err.txt" ) || rc=$? ;;
  esac
  [ "$rc" -ne 0 ] || pyh extract "$backend" "$outdir" 2>> "$outdir/err.txt" || rc=4
  if [ "$rc" -eq 0 ] && [ ! -s "$outdir/out.md" ]; then echo "review.sh: no answer; see $outdir/err.txt" >> "$outdir/why"; rc=4; fi
  # The last non-blank line exactly, trailing whitespace and CR forgiven: a quoted brief contains the marker too.
  if [ "$rc" -eq 0 ] && [ "$(grep -v '^[[:space:]]*$' "$outdir/out.md" | tail -n 1 | sed 's/[[:space:]]*$//')" != "===REVIEW COMPLETE===" ]; then
    echo "review.sh: answer lacks the closing ===REVIEW COMPLETE=== line; the round failed" >> "$outdir/why"; rc=5
  fi
  [ -z "$neutral" ] || rm -rf "$neutral"
  echo "$rc" > "$outdir/rc.tmp" && mv "$outdir/rc.tmp" "$outdir/rc"
  return "$rc"
}

if [ "$foreground" = 1 ]; then
  rc=0; run_reviewer || rc=$?
  [ ! -s "$outdir/why" ] || cat "$outdir/why" >&2
  exit "$rc"
fi
# Detached: a new session, so the caller's tool call returns now and cannot take the reviewer down.
# The child gets the function and the checked values as script text, not through an entry point.
command -v setsid >/dev/null 2>&1 || fail "setsid not found; use --foreground" 2
callid=$(basename -- "$outdir")
setsid -f bash -c "$(declare -p callid backend model effort resume cwd home deadline payload outdir neutral PYSRC py); \
$(declare -f pyh run_reviewer); run_reviewer" < /dev/null > /dev/null 2>> "$outdir/err.txt"
neutral=""   # the child removes it
exit 0
