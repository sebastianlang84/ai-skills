---
name: newsletter-delivery
description: Fetch and audit Market Digest artifacts, diagnose stale runs, and run an explicitly authorized private unified smoke. The retired production Telegram path must not be re-enabled.
disable-model-invocation: true
allowed-tools:
  - message
  - fetch
  - read
  - bash
---

# newsletter-delivery

Use this skill for Market Digest/newsletter tasks: fetch latest output, check whether it is current, diagnose stale runs, audit content, and optionally run an explicitly authorized private unified smoke.

## Choose the product contract first

Unified is the only product path. The old Letter, Risk Tracker, Radar, audit and
delivery code were removed (repo commit `3df7c2a`, 2026-08-26); old run directories
may still hold their artifacts, but nothing writes or sends them anymore. Never
confuse artifact availability with an active delivery contract:

- **Unified target:** one category-free Market Digest with 1-3 jointly ranked insights.
  There is no fixed Radar section and no second reader-facing message. Requests for
  the "new", "unified", "combined" or "better" format mean this branch.

For repo-local work, confirm the current contract in
`services/newsletter-writer/README.md#product-north-star` and the one-public-letter
ADR before choosing. The repo exposes no private Legacy/Radar smoke anymore;
`private-unified-digest-smoke.sh` is the only private end-to-end product smoke. If the requested unified artifact fails its
gates, repair and re-run those gates or report blocked. Never fall back to Legacy.

## Safety defaults

- **Production Telegram delivery is retired.** An instruction to inspect, debug, or
  run Market Digest does not authorize restoring it. A new public delivery contract
  needs an explicit cutover change in the repo.
- **Never send to the production channel** (`telegram.channel_id` has subscribers). Before any send, have the operator confirm the exact target id.
- Rendering tests may go to the operator's private Telegram DM after explicit confirmation. The DM chat id comes from `.env` (`NW_OPERATOR_TELEGRAM_CHAT_ID`); never print/store it. OpenClaw is removed — do not use it.
- If the newsletter is stale, incomplete, contradictory, or unaudited: **abort/blocked, do not send**.
- Never print or store Telegram token values. The bot token lives in the repo `.env` (`NW_TELEGRAM_BOT_TOKEN`; `OPENCLAW_TELEGRAM_BOT_TOKEN` — legacy name, plain bot token — and `TELEGRAM_BOT_TOKEN` also accepted).
- When this skill materially guides the answer, say so briefly (for example: `Skill genutzt: newsletter-delivery`).

## Sources

- Latest accepted digest: `GET http://127.0.0.1:8100/digests/latest` → `{ status, date, run_id, text }`; 404 when no run has an accepted digest (`unified_shadow_report.status=ok`, `stable_reader_ok=true`).
- Runs: `GET http://127.0.0.1:8100/runs` (newest first) and `GET /runs/<run_id>`; each item is the run's `status.json` (`state`, `result_status`, `delivery_status`, `run_date`, `error`).
- Run directory: `/home/wasti/ai_stack_data/newsletter-writer/runs/<run_id>/` (`status.json`, `unified_shadow_report.json`, `newsletter_unified.shadow.md`); the timer pipeline adds `runs/pipeline-<ts>/pipeline_status.json`, which links its `digest_run_id`.
- Health: `GET http://127.0.0.1:8100/healthz`.
- User systemd units: `market-digest-news-pipeline.timer`, `market-digest-news-pipeline.service`, `newsletter-writer.service`, `tm.service`

## Workflow

### 1. Fetch latest

Fetch:

```text
GET http://127.0.0.1:8100/digests/latest
GET http://127.0.0.1:8100/runs
```

If the API is unreachable, report: `newsletter-writer service nicht erreichbar (localhost:8100)`.

### 2. Freshness check

Compare `date` from `/digests/latest` against today's UTC date. UTC is the authoritative freshness gate; include local date/time in the report when local/UTC rollover may confuse the operator.

- If date is today: continue to audit.
- If date is not today: **abort delivery** and check today's runs in `/runs`. A finished run with `result_status` `reader_rejected`, `deterministic_rejected` or `abstained` is a deliberate no-send (a daily run does not imply a daily send); report it as such. A failed or missing run goes to the stale-diagnosis branch.

### 3. Stale-diagnosis branch

For stale latest output, gather only safe metadata:

1. Report latest newsletter date and today's UTC/local date.
2. Find the last run with `result_status=ok` and the most recent failed runs via `/runs` (or `runs/*/status.json`); for timer runs also read `runs/pipeline-*/pipeline_status.json` (`state`, `digest_run_id`, `fresh_failure_reason`).
3. Check `systemctl --user status market-digest-news-pipeline.timer market-digest-news-pipeline.service newsletter-writer.service tm.service --no-pager` when available.
4. Summarize only redacted metadata; do not paste raw `systemctl` output, raw artifact JSON, tokens, command lines containing secrets, or unredacted exception blobs.
5. Classify the likely blocker:
   - `insufficient fresh newsletter inputs` → fresh-input coverage issue
   - `gemini CLI failed` with `429` → Gemini quota/rate-limit
   - `codex CLI failed` with `Unauthorized`/refresh token → Codex auth issue
   - otherwise quote only the non-secret, redacted error summary
6. Do not trigger a new run or change timers unless the operator asks.

### 4. Audit the unified digest

Use the run's `newsletter_unified.shadow.md`, `newsletter_unified.shadow.validation.json`
and `unified_shadow_report.json`. Resolve the reader verdicts from
`unified_shadow_report.reader_gates` (`round`, `gate`, `verdict`, `blocks_newsletter`);
the files are `newsletter_unified.shadow.reader_round<N>_<gate>.json`. Hard
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

Do not send old Digest, Radar, Top Stocks, Risk Tracker or watchdog artifacts from
old run directories to Telegram. Keep research runs artifact-only.

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

For ad-hoc layout tests, avoid the production channel and send to the operator's private Telegram DM (no OpenClaw). Use the helper so target resolution and redaction are not rediscovered each time:

```bash
# dry-run first
/home/wasti/.agents/skills/newsletter-delivery/scripts/send_oberhummer_dm.sh /tmp/message.md

# real send only after explicit operator confirmation
/home/wasti/.agents/skills/newsletter-delivery/scripts/send_oberhummer_dm.sh --send /tmp/message.md
```

The helper reads the DM target and bot token from the repo `.env` (`NW_OPERATOR_TELEGRAM_CHAT_ID` + a bot-token env). It dry-runs by default (prints `dry_run=1 target=<private-dm> chars=N`, sends nothing); pass `--send` only after explicit operator confirmation. No OpenClaw log scraping, no daily DM bootstrapping, no chat id/token ever printed.

**Known break:** `--send` (and therefore the smoke's `--send-private`) imports `newsletter_writer.delivery.send_telegram`, which was removed with the retired product path (`3df7c2a`); a real send fails at import. Dry-run works. Restoring a private sender is a repo change, not a skill workaround — report it as blocked.

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
- Old patterns (removed, do not use): `/newsletters/latest`, `/risk-tracker`, the category audit (`## 📈 Stocks` / `## 🌐 Macro` / `## ₿ Crypto`), `RISK_TRACKER.md`, `newsletter_unified.shadow.reader_r*.json`. `risk_tracker/YYYY-MM-DD.md` snapshots end on 2026-08-25 and are history only.
