---
name: newsletter-delivery
description: Fetch, audit, and deliver the daily Market Digest newsletter via Telegram.
metadata:
  openclaw:
    emoji: "🦞"
    requires:
      config:
        - channels.telegram.botToken
allowed-tools:
  - message
  - fetch
---

# newsletter-delivery

Fetch the daily Market Digest from the newsletter-writer API, audit it, and send it to the Telegram channel.

## Sources

- Newsletter API: `http://localhost:8100/newsletters/latest` → `{ date, text }`
- Risk Tracker API: `http://localhost:8100/risk-tracker` → `{ text }` (may return 404 — non-blocking)
- Telegram channel: `-1003676013069`
- Token: in `channels.telegram.botToken` (openclaw.json) — kein Env var nötig

## Workflow

### 1. Fetch

```
GET http://localhost:8100/newsletters/latest
GET http://localhost:8100/risk-tracker   (ignore 404)
```

### 2. Freshness check

Compare `date` field from `/newsletters/latest` against today's date (UTC).
If not today: **abort**, report "Newsletter nicht aktuell — kein Run heute?"

### 3. Audit

Check all of the following. On hard failure: **abort, do not send**.

| Check | Pass |
|---|---|
| Contains `# 🦞 Market Digest` | required |
| Section `## 📈 Stocks` present | required |
| Section `## 🌐 Macro` present | required |
| Section `## ₿ Crypto` present | required |
| Each section has `**Sources:**` line | required |
| No unverified high-risk claims (war, crash, sovereign default) without explicit source | required |
| If risk tracker present: no contradiction with newsletter | required |

Soft issues (log, don't block): missing `## ⚠️ Anomalie` section, fewer than 3 sources per section.

### 4. Send

Use the `message` tool:

```json
{
  "action": "send",
  "channel": "telegram",
  "to": "channel:-1003676013069",
  "message": "<newsletter text>"
}
```

Telegram renders Markdown. The newsletter uses `**bold**` and `##` headings — send as-is.

### 5. Report

Reply with:
- Status: `sent` / `blocked` / `aborted`
- Audit findings (1–2 sentences)
- Newsletter date
- If blocked/aborted: exact reason

## Notes

- newsletter-writer runs daily at 07:00 CET via systemd timer, writes artefacts only — no delivery.
- **newsletter-writer braucht keinen Telegram-Token** — Delivery wurde vollständig entfernt. Der Token lebt ausschließlich in openclaw.json und wird nur hier verwendet.
- Token-Resolution-Reihenfolge (telegram plugin): `accounts.<id>.tokenFile` → `accounts.<id>.botToken` → `channels.telegram.tokenFile` → `channels.telegram.botToken` → `TELEGRAM_BOT_TOKEN` env var (nur Default-Account). Da `channels.telegram.botToken` in openclaw.json gesetzt ist, wird kein Env var benötigt.
- Risk Tracker (`RISK_TRACKER.md`) is updated each run and reflects the current rolling risk state.
- Risk Tracker history (one snapshot per day): `http://localhost:8100/risk-tracker` is always latest; historical snapshots are at `ai_stack_data/newsletter-writer/risk_tracker/YYYY-MM-DD.md` on the host.
- If the API is unreachable: report "newsletter-writer service nicht erreichbar (localhost:8100)".
