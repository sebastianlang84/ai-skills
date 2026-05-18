#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: send_oberhummer_dm.sh [--send] <message-file>

Dry-runs by default. Use --send only after explicit operator confirmation.
Sends via OpenClaw to the latest private/direct Telegram DM chat that messaged the bot.
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
if ! command -v openclaw >/dev/null 2>&1; then
  echo "ERROR: openclaw CLI not found" >&2
  exit 1
fi
if ! command -v rg >/dev/null 2>&1; then
  echo "ERROR: rg not found" >&2
  exit 1
fi

log_file="/tmp/openclaw/openclaw-$(date +%F).log"
if [[ ! -f "${log_file}" ]]; then
  echo "ERROR: OpenClaw log not found: ${log_file}" >&2
  echo "Ask the operator to DM the bot once, then retry." >&2
  exit 1
fi

chat_id="$(rg -o 'Inbound message telegram:[0-9]+' "${log_file}" | tail -1 | sed 's/.*telegram://' || true)"
if [[ -z "${chat_id}" ]]; then
  echo "ERROR: no recent direct Telegram inbound found in ${log_file}" >&2
  echo "Ask the operator to DM the bot once, then retry." >&2
  exit 1
fi

args=(message send --channel telegram --target "${chat_id}" --message "$(cat "${message_file}")" --json)
if [[ "${send}" != "1" ]]; then
  args+=(--dry-run)
fi

# Redact chat ids and bot tokens from CLI output. Do not echo ${chat_id}.
openclaw "${args[@]}" 2> >(sed -E 's/[0-9]{8,}/<id>/g; s/(bot)[0-9]+:[A-Za-z0-9_-]+/\1<TOKEN>/g' >&2) \
  | sed -E 's/[0-9]{8,}/<id>/g; s/"to":"[^"]+"/"to":"<private-dm>"/g; s/"target":"[^"]+"/"target":"<private-dm>"/g'
