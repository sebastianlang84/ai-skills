# Adaptive cadence

Why this exists: a fixed nightly cron re-reviews repos that haven't changed and have no new findings,
burning `claude` runs for nothing. The orchestrator instead decides, per repo and per lens, whether
tonight is worth it. This is the logic a dumb scheduler cannot do — hence the bash orchestrator.

## The decision each night, per lens

1. Compute `new_commits` = current HEAD differs from the SHA saved at the last run (or first run).
2. **Eligible to run tonight?**
   - `new_commits` → **always run** (the surface changed; re-check it).
   - otherwise → run only if today ≥ the saved `next-eligible` date.
3. After a run, update backoff from the yield:
   - findings > 0 **or** new commits → reset `empty-streak` to 0, `next-eligible` = tomorrow.
   - empty run → `empty-streak++`. Once it reaches `EMPTY_RUNS_BEFORE_BACKOFF` (K), the interval
     doubles each further empty run: 2, 4, 8, … days, capped at `BACKOFF_MAX_DAYS`.

Net effect: an actively developed repo is reviewed nightly; a quiet repo that keeps yielding nothing
is checked ever more rarely — and **any new commit instantly resets it to nightly**. This is exactly
"stop scheduling a lens that finds nothing, restart it when there's new work" without ever editing a
cron entry by hand.

## State files (per repo, under `$STATE_DIR/<slugged-path>/`)

| file | meaning |
|------|---------|
| `<lens>.last-sha` | HEAD at the last completed run of this lens |
| `<lens>.empty-streak` | consecutive empty runs (drives backoff) |
| `<lens>.next-eligible` | epoch date; lens is skipped until then unless new commits |
| `seen-findings.txt` | dedup hashes (`lens|repo|{file,line,area,kind,summary}`) — never re-report/re-PR |
| `prs.tsv` | `finding-id <tab> pr-url <tab> summary` for fixes already turned into PRs |

## Tuning

- **More aggressive latent-bug hunting:** raise `BACKOFF_MAX_DAYS` down (e.g. 7) so quiet repos still
  get a full re-audit at least weekly, or raise `EMPTY_RUNS_BEFORE_BACKOFF` so backoff kicks in later.
- **Cost-sensitive:** lower `BACKOFF_MAX_DAYS`'s effect by lowering `EMPTY_RUNS_BEFORE_BACKOFF` to 1
  so quiet repos back off fast.
- **Force a fresh full pass:** delete that lens's `last-sha`/`next-eligible` in the state dir, or the
  whole per-repo state dir to also clear dedup memory.
