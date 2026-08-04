#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: send_oberhummer_dm.sh [--send] <message-file>

Dry-runs by default (prints target placeholder + char count, sends nothing).
Use --send only after explicit operator confirmation.

Sends natively via newsletter_writer.delivery.send_telegram (Telegram Bot API)
to the operator's private DM. No OpenClaw dependency. The DM target and bot
token are read from the repo .env; nothing is scraped from OpenClaw logs and
no chat id / token is ever printed.
EOF
}

send=0
if [[ "${1:-}" == "--send" ]]; then
  send=1
  shift
fi

message_file="${1:-}"
if [[ -z "${message_file}" || "${message_file}" == "-h" || "${message_file}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ ! -f "${message_file}" ]]; then
  echo "ERROR: message file not found: ${message_file}" >&2
  exit 1
fi

repo_root="/home/wasti/dev/market-digest"
service_dir="${repo_root}/services/newsletter-writer"
env_file="${repo_root}/.env"
if [[ -f "${env_file}" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "${env_file}"
  set +a
fi

MSG_FILE="${message_file}" SEND="${send}" \
  "${service_dir}/.venv/bin/python" - <<'PY'
import os
import sys

sys.path.insert(0, "/home/wasti/dev/market-digest/services/newsletter-writer/src")


def first_env(keys):
    for key in keys:
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


chat_id = first_env(["NW_OPERATOR_TELEGRAM_CHAT_ID", "OPERATOR_TELEGRAM_CHAT_ID"])
token = first_env(["NW_TELEGRAM_BOT_TOKEN", "OPENCLAW_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"])
if not chat_id:
    print("ERROR: no operator DM chat id (set NW_OPERATOR_TELEGRAM_CHAT_ID)", file=sys.stderr)
    sys.exit(1)
if not token:
    print("ERROR: no telegram bot token env set", file=sys.stderr)
    sys.exit(1)

text = open(os.environ["MSG_FILE"], encoding="utf-8").read()
if os.environ.get("SEND") != "1":
    print(f"dry_run=1 target=<private-dm> chars={len(text)} (no message sent)")
    sys.exit(0)

from newsletter_writer.delivery import send_telegram

send_telegram(text, channel_id=chat_id, bot_token=token)
print("private_send=sent (native delivery.py, operator DM)")
PY
