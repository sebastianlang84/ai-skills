#!/usr/bin/env bash
# review.sh — starts review.py, which does the work on Linux and on Windows (Git Bash); same arguments:
#
#   review.sh <codex|claude> [--foreground] [--resume <id>] [--effort <level>] <brief-file> <artifact-file>...
#   review.sh wait <dir> [--timeout <s>]  |  review.sh cancel <dir>
#   review.sh --print-config | --get <KEY>
#
# Kept so callers and documentation keep one path. Interface and exit codes: review.py.
here=$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")" && pwd -P)
# The first interpreter that really runs: on Windows, python3 may be a Store stub that only prints a hint.
for c in python3 python; do
  "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null && exec "$c" "$here/review.py" "$@"
done
echo "review.sh: python 3.9 or newer not found" >&2
exit 2
