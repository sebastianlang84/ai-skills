#!/usr/bin/env bash
# doctor.sh — start one doctor round on an agent session, detached; the caller stays responsive.
#
#   doctor.sh [--session <path|id>] [--focus <from>-<to>]... [--extra <file>]... <brief-file>
#
# Collects the redacted evidence with collect.py into a private directory, then hands brief and
# evidence to using-harnesses' review.sh at effort medium. The doctor is the other vendor than
# the patient session (read from its transcript): a Claude Code transcript gets codex, a Codex
# rollout gets claude. Prints the review.sh call directory; collect the answer with
# `review.sh wait <dir>` (exit 75 = still running). Exit codes are review.sh's, 2 = usage.
set -euo pipefail
die() { echo "doctor.sh: $1" >&2; exit "${2:-2}"; }
here=$(cd "$(dirname "$(readlink -f "$0")")" && pwd -P)
review="$here/../../using-harnesses/scripts/review.sh"
[ -x "$review" ] || die "using-harnesses/scripts/review.sh not found next to this skill; no fallback to another call path"

collect=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --session|--focus|--extra) [ "$#" -ge 2 ] || die "usage: $1 <value>"; collect+=("$1" "$2"); shift 2 ;;
    -*) die "unknown option $1" ;;
    *) break ;;
  esac
done
[ "$#" -eq 1 ] && [ -f "$1" ] || die "usage: doctor.sh [--session <path|id>] [--focus <from>-<to>]... [--extra <file>]... <brief-file>"
brief=$1

umask 077
work=$(mktemp -d "${TMPDIR:-/tmp}/doctor.XXXXXXXX")
trap 'rm -rf "$work"' EXIT
patient=$(python3 "$here/collect.py" "${collect[@]}" "$work/evidence.md" | sed -n 's/^vendor: //p')
case "$patient" in claude) doctor=codex ;; codex) doctor=claude ;; *) die "collect.py named no patient vendor" ;; esac
# review.sh copies brief and evidence into its own payload.md before it returns.
"$review" "$doctor" --effort medium "$brief" "$work/evidence.md"
