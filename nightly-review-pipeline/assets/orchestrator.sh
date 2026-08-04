#!/usr/bin/env bash
# Nightly review + auto-fix orchestrator.
#
# The scheduler (systemd timer / cron) fires this once a night. THIS script decides,
# per repo and per lens, whether to actually spend a `claude` run — using saved state
# and adaptive backoff — then dedups findings, renders markdown, and (bug lens only)
# opens draft-PR fixes for high-confidence findings whose tests pass.
#
# STARTER TEMPLATE: run with --dry-run first, set per-repo test commands, and verify the
# `claude` flag syntax for your installed version. No `set -e`: one failing sub-step must
# not abort the whole night; return codes are handled explicitly.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_CLAUDE="$HERE/run-claude.sh"
PROMPT_DIR="$HERE/prompts"

DRY_RUN=0
CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG=$2; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    *) echo "orchestrator: unknown arg: $1" >&2; exit 2;;
  esac
done
[[ -n "$CONFIG" && -f "$CONFIG" ]] || { echo "orchestrator: need --config FILE" >&2; exit 2; }
# shellcheck disable=SC1090
source "$CONFIG"

# ---- defaults (config may override) ----------------------------------------
: "${STATE_DIR:=$HOME/.local/state/nightly-review}"
: "${LOG_DIR:=$STATE_DIR/logs}"
: "${MODEL:=}"
: "${BACKOFF_MAX_DAYS:=14}"
: "${EMPTY_RUNS_BEFORE_BACKOFF:=2}"
: "${AUTO_FIX:=1}"
: "${MIN_FIX_SEVERITY:=high}"
: "${MIN_FIX_CONFIDENCE:=high}"
: "${FIX_BASE_BRANCH:=main}"
: "${TEST_CMD_DEFAULT:=}"
: "${REVIEW_MAX_TURNS:=40}"
: "${REVIEW_TIMEOUT:=1800}"
: "${FIX_MAX_TURNS:=60}"
: "${FIX_TIMEOUT:=2400}"
: "${TEST_TIMEOUT:=1200}"
# Where review findings are written:
#   REPORT_IN_REPO=1 -> into the repo, reusing its EXISTING task/ideas file (case-detected)
#   REPORT_IN_REPO=0 -> out of the repo, under REPORTS_DIR/<repo-slug>/ (no repo side effects)
: "${REPORT_IN_REPO:=1}"
: "${REPORTS_DIR:=$STATE_DIR/reports}"
: "${TASK_FILE:=TODO.md}"     # bug lens target basename (matched case-insensitively in-repo)
: "${IDEAS_FILE:=IDEAS.md}"   # usability lens target basename
export MODEL CLAUDE_BIN 2>/dev/null || true
mkdir -p "$STATE_DIR" "$LOG_DIR"
RUN_LOG="$LOG_DIR/run-$(date +%Y%m%d-%H%M%S).log"

# ---- helpers ---------------------------------------------------------------
log(){ printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$RUN_LOG" >&2; }
slug(){ printf '%s' "$1" | sed 's#[^A-Za-z0-9]#_#g'; }
today_epoch(){ date -d "$(date +%Y-%m-%d)" +%s; }
sev_rank(){ case "$1" in low)echo 1;; medium)echo 2;; high)echo 3;; critical)echo 4;; *)echo 0;; esac; }
conf_rank(){ case "$1" in low)echo 1;; medium)echo 2;; high)echo 3;; *)echo 0;; esac; }
# Strip a leading ```json / ``` fence and trailing ``` if the model added one.
strip_fences(){ sed -e 's/^[[:space:]]*```json[[:space:]]*//' -e 's/^[[:space:]]*```[[:space:]]*//' -e 's/```[[:space:]]*$//'; }

# Eligible tonight? new commits => always; else only if past next-eligible date.
eligible(){ # $1 statedir  $2 lens  $3 new_commits(0/1)  -> echoes run|skip
  local sd=$1 lens=$2 newc=$3 ne=0
  [[ "$newc" == "1" ]] && { echo run; return; }
  [[ -f "$sd/$lens.next-eligible" ]] && ne=$(cat "$sd/$lens.next-eligible")
  if [[ "$(today_epoch)" -ge "$ne" ]]; then echo run; else echo skip; fi
}

# Update backoff state after a lens ran.
update_cadence(){ # $1 statedir  $2 lens  $3 new_findings_count  $4 new_commits(0/1)
  local sd=$1 lens=$2 count=$3 newc=$4 interval=1 streak
  streak=$(cat "$sd/$lens.empty-streak" 2>/dev/null || echo 0)
  if [[ "$count" -gt 0 || "$newc" == "1" ]]; then
    streak=0
  else
    streak=$((streak + 1))
    if [[ "$streak" -ge "$EMPTY_RUNS_BEFORE_BACKOFF" ]]; then
      interval=$(( 1 << (streak - EMPTY_RUNS_BEFORE_BACKOFF + 1) ))   # 2,4,8,...
      [[ "$interval" -gt "$BACKOFF_MAX_DAYS" ]] && interval=$BACKOFF_MAX_DAYS
    fi
  fi
  echo "$streak" > "$sd/$lens.empty-streak"
  echo $(( $(today_epoch) + interval * 86400 )) > "$sd/$lens.next-eligible"
  log "  cadence[$lens]: findings=$count new_commits=$newc empty_streak=$streak next_in=${interval}d"
}

# Resolve the markdown target for a lens. In-repo mode reuses the repo's EXISTING file
# (case-insensitive: an existing TODO.md is used, not a competing todo.md); otherwise it
# falls back to the configured basename. Out-of-repo mode writes under REPORTS_DIR.
resolve_target(){ # $1 repo  $2 lens  -> echoes absolute path
  local repo=$1 lens=$2 base found rd
  if [[ "$lens" == "bug" ]]; then base="$TASK_FILE"; else base="$IDEAS_FILE"; fi
  if [[ "$REPORT_IN_REPO" == "1" ]]; then
    found=$(cd "$repo" 2>/dev/null && ls -1 2>/dev/null | grep -ixF "$base" | head -1 || true)
    [[ -n "$found" ]] && { printf '%s/%s' "$repo" "$found"; return; }
    printf '%s/%s' "$repo" "$base"
  else
    rd="$REPORTS_DIR/$(slug "$repo")"; mkdir -p "$rd"; printf '%s/%s' "$rd" "$base"
  fi
}

# Render this run's new items as a dated markdown subsection (to stdout).
render_body(){ # $1 lens  $2 jsonl
  local lens=$1 jsonl=$2 o
  echo
  echo "### $(date +%Y-%m-%d) — nightly-review ($lens)"
  echo
  while IFS= read -r o; do
    if [[ "$lens" == "bug" ]]; then
      printf -- '- [ ] **%s/%s** `%s:%s` — %s\n' \
        "$(jq -r '.severity' <<<"$o")" "$(jq -r '.confidence' <<<"$o")" \
        "$(jq -r '.file' <<<"$o")" "$(jq -r '.line' <<<"$o")" "$(jq -r '.summary' <<<"$o")"
      printf -- '    - scenario: %s\n' "$(jq -r '.failure_scenario // "-"' <<<"$o")"
    else
      printf -- '- [ ] _%s_ (%s) — %s\n' \
        "$(jq -r '.kind' <<<"$o")" "$(jq -r '.area' <<<"$o")" "$(jq -r '.summary' <<<"$o")"
      printf -- '    - %s\n' "$(jq -r '.suggested_change // .rationale // "-"' <<<"$o")"
    fi
  done < "$jsonl"
}

# Write new items into a marker-delimited managed block in the target file. Everything the
# pipeline owns lives between the markers; the rest of the file (human content) is never
# touched. New subsections are inserted just before the end marker, so history accumulates
# inside the block instead of a second competing file being created.
write_report(){ # $1 target  $2 lens  $3 jsonl
  local target=$1 lens=$2 jsonl=$3 bf
  local start="<!-- nightly-review:$lens:start -->" end="<!-- nightly-review:$lens:end -->"
  [[ -s "$jsonl" ]] || return 0
  [[ -f "$target" ]] || : > "$target"
  if ! grep -qF "$start" "$target"; then
    printf '\n%s\n%s\n' "$start" "$end" >> "$target"
  fi
  bf=$(mktemp); render_body "$lens" "$jsonl" > "$bf"
  awk -v endm="$end" -v bf="$bf" '
    index($0, endm) && !done { while ((getline l < bf) > 0) print l; done=1 }
    { print }
  ' "$target" > "$target.nrp.tmp" && mv "$target.nrp.tmp" "$target"
  rm -f "$bf"
  log "  wrote $(wc -l < "$jsonl" | tr -d ' ') new item(s) into managed $lens block of $target"
}

# Run one review lens. Writes new (deduped) items to $sd/$lens.new.jsonl and echoes their count.
# Echoes -1 if the lens was skipped (backoff) or failed.
run_review(){ # $1 repo  $2 statedir  $3 lens  $4 promptfile  $5 new_commits  $6 last_sha  $7 cur_sha
  local repo=$1 sd=$2 lens=$3 pf=$4 newc=$5 last=$6 sha=$7
  : > "$sd/$lens.new.jsonl"

  if [[ "$(eligible "$sd" "$lens" "$newc")" == "skip" ]]; then
    log "  [$lens] skip: backoff active, no new commits"; echo "-1"; return
  fi

  local scope
  if [[ -z "$last" ]]; then
    scope="Full repository scan (first run)."
  elif [[ "$newc" == "1" ]]; then
    scope="Prioritise changes since last run: git diff ${last}..${sha}. Also flag regressions those changes could cause elsewhere."
  else
    scope="Full repository re-audit (no new commits since last run)."
  fi

  local prompt="$sd/.$lens.prompt.txt"
  sed -e "s#{{REPO_PATH}}#${repo}#g" -e "s#{{SCOPE}}#${scope}#g" "$pf" > "$prompt"

  if [[ "$DRY_RUN" == "1" ]]; then
    log "  [$lens] DRY-RUN: would review $repo — $scope"; echo "0"; return
  fi

  local raw="$sd/$lens.raw.json"
  if ! "$RUN_CLAUDE" --cwd "$repo" --prompt-file "$prompt" --raw "$raw" --log "$RUN_LOG" \
        --output-format json --permission-mode plan \
        --max-turns "$REVIEW_MAX_TURNS" --timeout "$REVIEW_TIMEOUT"; then
    log "  [$lens] claude run failed (see log)"; echo "-1"; return
  fi

  local items="$sd/$lens.items.json"
  if ! jq -e '.result' "$raw" >/dev/null 2>&1; then
    log "  [$lens] no .result field in claude output"; echo "0"; return
  fi
  if ! jq -r '.result' "$raw" | strip_fences | jq -c 'if type=="array" then . else [] end' > "$items" 2>>"$RUN_LOG"; then
    log "  [$lens] model result was not valid JSON; skipping"; echo "0"; return
  fi
  echo "$sha" > "$sd/$lens.last-sha"

  # Dedup against seen-findings and collect this run's new items.
  local seen="$sd/seen-findings.txt"; touch "$seen"
  local n new=0 i obj key hash
  n=$(jq 'length' "$items")
  for ((i=0; i<n; i++)); do
    obj=$(jq -c ".[$i]" "$items")
    key=$(jq -S -c '{file, line, area, kind, summary}' <<<"$obj")
    hash=$(printf '%s|%s|%s' "$lens" "$repo" "$key" | sha1sum | cut -c1-16)
    grep -q "$hash" "$seen" && continue
    echo "$hash" >> "$seen"
    printf '%s\n' "$obj" >> "$sd/$lens.new.jsonl"
    new=$((new + 1))
  done
  echo "$new"
}

# ---- fix flow (bug lens only) ----------------------------------------------
fix_one(){ # $1 repo  $2 statedir  $3 finding_json  $4 test_cmd
  local repo=$1 sd=$2 obj=$3 testcmd=$4 id branch wt summary
  id=$(jq -S -c '{file, summary}' <<<"$obj" | sha1sum | cut -c1-8)
  branch="nightly/fix-$id"
  summary=$(jq -r '.summary' <<<"$obj")

  if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch" \
     || grep -q "^$id	" "$sd/prs.tsv" 2>/dev/null; then
    log "    fix $id: branch/PR already exists, skip"; return
  fi
  if [[ "$DRY_RUN" == "1" ]]; then log "    fix $id: DRY-RUN — would fix: $summary"; return; fi

  wt=$(mktemp -d "$STATE_DIR/wt-${id}-XXXXXX")
  if ! git -C "$repo" worktree add -b "$branch" "$wt" "$FIX_BASE_BRANCH" >>"$RUN_LOG" 2>&1; then
    log "    fix $id: worktree add failed"; rm -rf "$wt"; return
  fi

  local prompt="$sd/.fix.$id.txt"
  sed -e "s#{{WORKTREE}}#${wt}#g" "$PROMPT_DIR/fix.prompt.md" > "$prompt"
  printf '\n\nFINDING (JSON):\n%s\n' "$obj" >> "$prompt"

  # Agent edits only; orchestrator runs tests/git. acceptEdits => no dangerous skip needed.
  "$RUN_CLAUDE" --cwd "$wt" --prompt-file "$prompt" --log "$RUN_LOG" \
      --output-format json --permission-mode acceptEdits \
      --max-turns "$FIX_MAX_TURNS" --timeout "$FIX_TIMEOUT" || log "    fix $id: claude run returned nonzero"

  if [[ -f "$wt/FIX_ABORTED.txt" ]]; then
    log "    fix $id: agent aborted — $(head -1 "$wt/FIX_ABORTED.txt")"
    git -C "$repo" worktree remove --force "$wt" >>"$RUN_LOG" 2>&1
    git -C "$repo" branch -D "$branch" >>"$RUN_LOG" 2>&1; return
  fi
  if git -C "$wt" diff --quiet && git -C "$wt" diff --cached --quiet; then
    log "    fix $id: no changes produced"
    git -C "$repo" worktree remove --force "$wt" >>"$RUN_LOG" 2>&1
    git -C "$repo" branch -D "$branch" >>"$RUN_LOG" 2>&1; return
  fi

  if [[ -n "$testcmd" ]]; then
    if ! ( cd "$wt" && timeout "${TEST_TIMEOUT}s" bash -lc "$testcmd" ) >>"$RUN_LOG" 2>&1; then
      log "    fix $id: TESTS FAILED — discarding (no PR)"
      git -C "$repo" worktree remove --force "$wt" >>"$RUN_LOG" 2>&1
      git -C "$repo" branch -D "$branch" >>"$RUN_LOG" 2>&1; return
    fi
    log "    fix $id: tests passed"
  else
    log "    fix $id: no test command set — opening PR UNVERIFIED (set a test cmd!)"
  fi

  ( cd "$wt" \
    && git add -A \
    && git commit -q -m "fix: ${summary}

Auto-generated by nightly-review-pipeline (finding ${id}).
Scenario: $(jq -r '.failure_scenario // empty' <<<"$obj")

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" ) >>"$RUN_LOG" 2>&1

  if ! git -C "$wt" push -u origin "$branch" >>"$RUN_LOG" 2>&1; then
    log "    fix $id: push failed"; git -C "$repo" worktree remove --force "$wt" >>"$RUN_LOG" 2>&1; return
  fi

  local body prurl
  body=$(printf 'Automated **draft** fix from nightly-review-pipeline. Review before merge; never auto-merge.\n\n**Finding %s**\n\n```json\n%s\n```\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)' "$id" "$obj")
  if prurl=$( cd "$wt" && gh pr create --draft --base "$FIX_BASE_BRANCH" --head "$branch" \
                --title "[nightly] fix: ${summary}" --body "$body" 2>>"$RUN_LOG" ); then
    printf '%s\t%s\t%s\n' "$id" "$prurl" "$summary" >> "$sd/prs.tsv"
    log "    fix $id: draft PR $prurl"
  else
    log "    fix $id: gh pr create failed (branch pushed; open PR manually)"
  fi
  git -C "$repo" worktree remove --force "$wt" >>"$RUN_LOG" 2>&1
}

do_fixes(){ # $1 repo  $2 statedir  $3 test_cmd
  local repo=$1 sd=$2 testcmd=$3 obj sev conf
  [[ "$AUTO_FIX" == "1" ]] || { log "  auto-fix disabled"; return; }
  [[ -s "$sd/bug.new.jsonl" ]] || return
  while IFS= read -r obj; do
    sev=$(jq -r '.severity // "low"' <<<"$obj")
    conf=$(jq -r '.confidence // "low"' <<<"$obj")
    [[ "$(sev_rank "$sev")"  -ge "$(sev_rank "$MIN_FIX_SEVERITY")"  ]] || continue
    [[ "$(conf_rank "$conf")" -ge "$(conf_rank "$MIN_FIX_CONFIDENCE")" ]] || continue
    [[ "$(jq -r '.category // "correctness"' <<<"$obj")" != "style" ]] || continue
    fix_one "$repo" "$sd" "$obj" "$testcmd"
  done < "$sd/bug.new.jsonl"
}

# ---- main loop -------------------------------------------------------------
log "=== nightly-review run start (dry_run=$DRY_RUN, config=$CONFIG) ==="
for entry in "${REPOS[@]}"; do
  IFS='|' read -r repo lenses testcmd <<< "$entry"
  [[ -n "${testcmd:-}" ]] || testcmd="$TEST_CMD_DEFAULT"
  if [[ ! -d "$repo/.git" ]]; then log "skip: not a git repo: $repo"; continue; fi
  sd="$STATE_DIR/$(slug "$repo")"; mkdir -p "$sd"
  log "repo: $repo  (lenses: $lenses)"
  git -C "$repo" fetch --quiet origin >>"$RUN_LOG" 2>&1 || true

  IFS=',' read -ra LENSES <<< "$lenses"
  for lens in "${LENSES[@]}"; do
    sha=$(git -C "$repo" rev-parse HEAD 2>/dev/null || echo "")
    last=$(cat "$sd/$lens.last-sha" 2>/dev/null || echo "")
    newc=0; { [[ -z "$last" ]] || [[ "$last" != "$sha" ]]; } && newc=1

    case "$lens" in
      bug)
        cnt=$(run_review "$repo" "$sd" bug "$PROMPT_DIR/bug-review.prompt.md" "$newc" "$last" "$sha")
        [[ "$cnt" == "-1" ]] && continue
        write_report "$(resolve_target "$repo" bug)" bug "$sd/bug.new.jsonl"
        update_cadence "$sd" bug "$cnt" "$newc"
        do_fixes "$repo" "$sd" "$testcmd"
        ;;
      usability)
        cnt=$(run_review "$repo" "$sd" usability "$PROMPT_DIR/usability-review.prompt.md" "$newc" "$last" "$sha")
        [[ "$cnt" == "-1" ]] && continue
        write_report "$(resolve_target "$repo" usability)" usability "$sd/usability.new.jsonl"
        update_cadence "$sd" usability "$cnt" "$newc"
        ;;
      *) log "  unknown lens: $lens";;
    esac
  done
done
log "=== nightly-review run done ==="
