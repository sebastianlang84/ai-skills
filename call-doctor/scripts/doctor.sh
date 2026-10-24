#!/usr/bin/env bash
# doctor.sh — start one doctor round on an agent session, detached; the caller stays responsive.
#
#   doctor.sh [--session <path|id>] [--focus <from>-<to>]... [--extra <file>]... <brief-file>
#
# Collects the redacted evidence with collect.py into a private directory, then hands brief and
# evidence to using-harnesses' review.py at effort medium. The doctor is the other vendor than
# the patient session (read from its transcript): a Claude Code transcript gets codex, a Codex
# rollout gets claude. Prints the review.py call directory; collect the answer with
# `review.py wait <dir>` (exit 75 = still running). Exit codes are review.py's, 2 = usage.
set -euo pipefail
die() { echo "doctor.sh: $1" >&2; exit "${2:-2}"; }
here=$(cd "$(dirname "$(readlink -f "$0")")" && pwd -P)
# The first interpreter that really runs: on Windows, python3 may be a Store stub that only prints a hint.
py=""; for c in python3 python; do "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null && { py=$c; break; }; done
[ -n "$py" ] || die "python 3.9 or newer not found"
review="$here/../../using-harnesses/scripts/review.py"
[ -f "$review" ] || die "using-harnesses/scripts/review.py not found next to this skill; no fallback to another call path"

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
patient=$("$py" "$here/collect.py" "${collect[@]}" "$work/evidence.md" | sed -n 's/^vendor: //p')
case "$patient" in claude) doctor=codex ;; codex) doctor=claude ;; *) die "collect.py named no patient vendor" ;; esac
# review.py copies brief and evidence into its own payload.md before it returns.
"$py" "$review" "$doctor" --effort medium "$brief" "$work/evidence.md"
