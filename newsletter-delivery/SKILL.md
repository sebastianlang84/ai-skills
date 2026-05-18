---
name: newsletter-delivery
description: Fetch the Market Digest, check freshness, diagnose stale newsletter runs, audit content, and optionally deliver via Telegram only after explicit operator authorization.
metadata:
  openclaw:
    emoji: "🦞"
    requires:
      config:
        - channels.telegram.botToken
allowed-tools:
  - message
  - fetch
  - read
  - bash
---

# newsletter-delivery

Use this skill for Market Digest/newsletter tasks: fetch latest output, check whether it is current, diagnose stale runs, audit content, and only then deliver if explicitly authorized.

## Safety defaults

- **Default: do not send to the production Telegram channel.** Delivery requires an explicit operator instruction for this specific send.
- Rendering tests may go to the operator's private Oberhummer Telegram DM via OpenClaw after explicit confirmation; derive the private chat id from recent inbound logs, but never print/store it.
- If the newsletter is stale, incomplete, contradictory, or unaudited: **abort/blocked, do not send**.
- Never print or store Telegram token values. Token lives in `openclaw.json`/Telegram plugin config, not in `newsletter-writer`.
- When this skill materially guides the answer, say so briefly (for example: `Skill genutzt: newsletter-delivery`).

## Sources

- Newsletter API: `http://localhost:8100/newsletters/latest` → `{ date, text }`
- Risk Tracker API: `http://localhost:8100/risk-tracker` → `{ text }` (404 is non-blocking)
- Pipeline status artifacts: `/home/wasti/ai_stack_data/newsletter-writer/runs/*/pipeline_status.json`
- User systemd units: `ai-stack-news-pipeline.timer`, `ai-stack-news-pipeline.service`, `newsletter-writer.service`, `tm.service`
- Protected production Telegram channel: `-1003676013069` (only use after explicit authorization)

## Workflow

### 1. Fetch latest

Fetch:

```text
GET http://localhost:8100/newsletters/latest
GET http://localhost:8100/risk-tracker   (ignore 404)
```

If the API is unreachable, report: `newsletter-writer service nicht erreichbar (localhost:8100)`.

### 2. Freshness check

Compare `date` from `/newsletters/latest` against today's UTC date. UTC is the authoritative freshness gate; include local date/time in the report when local/UTC rollover may confuse the operator.

- If date is today: continue to audit.
- If date is not today: **abort delivery** and run the stale-diagnosis branch before replying.

### 3. Stale-diagnosis branch

For stale latest output, gather only safe metadata:

1. Report latest newsletter date and today's UTC/local date.
2. Find the last successful pipeline run and most recent failed runs under `/home/wasti/ai_stack_data/newsletter-writer/runs/*/pipeline_status.json`.
3. Check `systemctl --user status ai-stack-news-pipeline.timer ai-stack-news-pipeline.service newsletter-writer.service tm.service --no-pager` when available.
4. Summarize only redacted metadata; do not paste raw `systemctl` output, raw artifact JSON, tokens, command lines containing secrets, or unredacted exception blobs.
5. Classify the likely blocker:
   - `insufficient fresh newsletter inputs` → fresh-input coverage issue
   - `gemini CLI failed` with `429` → Gemini quota/rate-limit
   - `codex CLI failed` with `Unauthorized`/refresh token → Codex auth issue
   - delivery report failure → Telegram delivery issue
   - otherwise quote only the non-secret, redacted error summary
6. Do not trigger a new run or change timers unless the operator asks.

### 4. Audit current content

Check all of the following. On hard failure: **blocked, do not send**.

| Check | Pass |
|---|---|
| Contains `# 🦞 Market Digest` | required |
| Section `## 📈 Stocks` present | required |
| Section `## 🌐 Macro` present | required |
| Section `## ₿ Crypto` present | required |
| Each section has `**Sources:**` line | required |
| No unverified high-risk claims (war, crash, sovereign default) without explicit source | required |
| If risk tracker present: no contradiction with newsletter | required |
| Risk Tracker stale-item handling follows operator windows | 0–7 days keep open; 8–14 days stale/watch; 15–21 days inactive/archive unless explicit contrary evidence |

Soft issues (log, do not block): missing `## ⚠️ Anomalie` section, fewer than 3 sources per section.

### 5. Optional send

Only after explicit authorization and only if freshness + audit pass, use the Telegram/message tool with the protected channel:

```json
{
  "action": "send",
  "channel": "telegram",
  "to": "channel:-1003676013069",
  "message": "<newsletter text>"
}
```

Telegram renders Markdown. The newsletter uses `**bold**` and `##` headings — send as-is.

### 5b. Private Telegram rendering test via Oberhummer DM

For render/layout tests, avoid the production channel and send to the operator's private Oberhummer DM via OpenClaw. Use the helper so the chat-id extraction and redaction are not rediscovered each time:

```bash
# dry-run first
/home/wasti/.pi/agent/skills/newsletter-delivery/scripts/send_oberhummer_dm.sh /tmp/message.md

# real send only after explicit operator confirmation
/home/wasti/.pi/agent/skills/newsletter-delivery/scripts/send_oberhummer_dm.sh --send /tmp/message.md
```

If the helper cannot find a recent direct inbound, ask the operator to DM the bot once. Oberhummer agent auth errors are non-blocking for pure `openclaw message send`.

### 6. Report

Reply concisely with:

- `Skill genutzt: newsletter-delivery`
- Status: `sent` / `blocked` / `aborted` / `stale`
- Newsletter date and today's date basis (UTC/local if relevant)
- Last successful run/send, if checked
- Main blocker classification, if stale/blocked
- Audit findings in 1–2 sentences
- If blocked/aborted: exact reason

## Notes

- `newsletter-writer` is the host-native production path; persistent artifacts live under `/home/wasti/ai_stack_data/newsletter-writer/`.
- Risk Tracker (`RISK_TRACKER.md`) is updated by successful runs and reflects rolling risk state.
- Risk Tracker history: API is latest only; historical snapshots are under `/home/wasti/ai_stack_data/newsletter-writer/risk_tracker/YYYY-MM-DD.md` on the host.
