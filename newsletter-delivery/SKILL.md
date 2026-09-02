---
name: newsletter-delivery
description: Fetch and audit Market Digest artifacts, diagnose stale runs, and run an explicitly authorized private unified smoke. The retired production Telegram path must not be re-enabled.
disable-model-invocation: true
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

Use this skill for Market Digest/newsletter tasks: fetch latest output, check whether it is current, diagnose stale runs, audit content, and optionally run an explicitly authorized private unified smoke.

## Choose the product contract first

Market Digest retains legacy artifacts while the replacement is measured. Never
confuse artifact availability with an active delivery contract:

- **Legacy artifacts:** category sections plus a separate Radar may still be written
  internally. Automatic public delivery, private previews, and the Telegram watchdog
  were retired on 2026-08-23. Do not re-enable or send them.
- **Unified target:** one category-free Market Digest with 1-3 jointly ranked insights;
  the Risk & Chance Tracker is internal. There is no fixed Radar section and no second
  reader-facing message. Requests for the "new", "unified", "combined" or "better"
  format mean this branch.

For repo-local work, confirm the current contract in
`services/newsletter-writer/README.md#product-north-star` and the one-public-letter
ADR before choosing. The repo exposes no private Legacy/Radar smoke anymore;
`private-unified-digest-smoke.sh` is the only private end-to-end product smoke. If the requested unified artifact fails its
gates, repair and re-run those gates or report blocked. Never fall back to Legacy.

## Safety defaults

- **Production Telegram delivery is retired.** An instruction to inspect, debug, or
  run Market Digest does not authorize restoring it. A new public delivery contract
  needs an explicit cutover change in the repo.
- Rendering tests may go to the operator's private Telegram DM after explicit confirmation, sent natively via `newsletter_writer.delivery.send_telegram` (Telegram Bot API). The DM chat id comes from `.env` (`NW_OPERATOR_TELEGRAM_CHAT_ID`); never print/store it. OpenClaw is removed — do not use it.
- If the newsletter is stale, incomplete, contradictory, or unaudited: **abort/blocked, do not send**.
- Never print or store Telegram token values. The bot token lives in the repo `.env` (`OPENCLAW_TELEGRAM_BOT_TOKEN` — legacy name, plain bot token; `NW_TELEGRAM_BOT_TOKEN`/`TELEGRAM_BOT_TOKEN` also accepted), read by `delivery.py`.
- When this skill materially guides the answer, say so briefly (for example: `Skill genutzt: newsletter-delivery`).

## Sources

- Newsletter API: `http://localhost:8100/newsletters/latest` → `{ date, text }`
- Risk Tracker API: `http://localhost:8100/risk-tracker` → `{ text }` (404 is non-blocking)
- Pipeline status artifacts: `/home/wasti/ai_stack_data/newsletter-writer/runs/*/pipeline_status.json`
- User systemd units: `market-digest-news-pipeline.timer`, `market-digest-news-pipeline.service`, `newsletter-writer.service`, `tm.service`

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
3. Check `systemctl --user status market-digest-news-pipeline.timer market-digest-news-pipeline.service newsletter-writer.service tm.service --no-pager` when available.
4. Summarize only redacted metadata; do not paste raw `systemctl` output, raw artifact JSON, tokens, command lines containing secrets, or unredacted exception blobs.
5. Classify the likely blocker:
   - `insufficient fresh newsletter inputs` → fresh-input coverage issue
   - `gemini CLI failed` with `429` → Gemini quota/rate-limit
   - `codex CLI failed` with `Unauthorized`/refresh token → Codex auth issue
   - delivery report failure → Telegram delivery issue
   - otherwise quote only the non-secret, redacted error summary
6. Do not trigger a new run or change timers unless the operator asks.

### 4a. Audit retained legacy artifacts

Use this branch only for historical comparison or diagnosis. A pass never
authorizes delivery.

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

### 4b. Audit the unified target

Use the run's `newsletter_unified.shadow.md`, `newsletter_unified.shadow.validation.json`,
`newsletter_unified.shadow.reader_r*.json`, and `unified_shadow_report.json`. Hard
requirements:

- exactly one reader-facing message;
- H1 `# Market Digest — <date>` and 1-3 `##` insights;
- no Stocks/Macro/Crypto Pflichtbereiche, no H3 signal headings, no public Radar;
- exactly one final `**Quellen:**` line and no internal IDs or process commentary;
- deterministic validation `ok=true`, within the configured word/page limits;
- `unified_shadow_report.status=ok`, `stable_reader_ok=true`, and every configured
  independent reader pass is non-blocking;
- selected claims remain covered by the frozen selection and its evidence references.

The unified path is non-delivering until the repo's cutover gates are met. Even after a
clean audit, send it only to the private operator DM unless the operator explicitly
authorizes a production cutover/send.

### 5. No legacy send

Do not send retained legacy Digest, Radar, Top Stocks, or watchdog messages to
Telegram. Keep research runs artifact-only.

### 5b. Private Unified Market Digest test via Oberhummer DM

Do not use renderer-only output, stale artifacts, the legacy newsletter, or a public Radar as proof of readiness. A private test is ready only after an isolated no-delivery end-to-end run produces a valid Unified Market Digest and all configured reader passes accept the same final bytes.

Preferred repo smoke test:

```bash
# Validate only; never sends to production Telegram or writes production artifacts.
/home/wasti/dev/market-digest/scripts/ops/private-unified-digest-smoke.sh

# Send exactly the validated Unified Digest to the private Oberhummer DM only after explicit operator approval.
/home/wasti/dev/market-digest/scripts/ops/private-unified-digest-smoke.sh --send-private
```

Required private-test gates:

- run uses isolated temp `AI_STACK_DATA_DIR` and `send_delivery=False`
- final `runs/<run_id>/newsletter_unified.shadow.md` exists
- deterministic validation is `ok`
- `unified_shadow_report.status=ok` and `stable_reader_ok=true`
- no fixed Stocks/Macro/Crypto or Radar section
- one Telegram page (`<=4096` chars)
- status shows `delivery_status=skipped_delivery_disabled`

For ad-hoc non-Radar layout tests, avoid the production channel and send to the operator's private Telegram DM natively (via `delivery.py`, no OpenClaw). Use the helper so target resolution and redaction are not rediscovered each time:

```bash
# dry-run first
/home/wasti/.agents/skills/newsletter-delivery/scripts/send_oberhummer_dm.sh /tmp/message.md

# real send only after explicit operator confirmation
/home/wasti/.agents/skills/newsletter-delivery/scripts/send_oberhummer_dm.sh --send /tmp/message.md
```

The helper reads the DM target and bot token from the repo `.env` (`NW_OPERATOR_TELEGRAM_CHAT_ID` + a bot-token env) and sends via `newsletter_writer.delivery.send_telegram`. It dry-runs by default (prints `dry_run=1 target=<private-dm> chars=N`, sends nothing); pass `--send` only after explicit operator confirmation. No OpenClaw log scraping, no daily DM bootstrapping, no chat id/token ever printed.

### 6. Report

Reply concisely with:

- `Skill genutzt: newsletter-delivery`
- Status: `artifact-only` / `blocked` / `aborted` / `stale`
- Newsletter date and today's date basis (UTC/local if relevant)
- Last successful run/send, if checked
- Main blocker classification, if stale/blocked
- Audit findings in 1–2 sentences
- If blocked/aborted: exact reason

## Notes

- `newsletter-writer` is the host-native artifact and shadow path; persistent artifacts live under `/home/wasti/ai_stack_data/newsletter-writer/`.
- Risk Tracker (`RISK_TRACKER.md`) is updated by successful runs and reflects rolling risk state.
- Risk Tracker history: API is latest only; historical snapshots are under `/home/wasti/ai_stack_data/newsletter-writer/risk_tracker/YYYY-MM-DD.md` on the host.
