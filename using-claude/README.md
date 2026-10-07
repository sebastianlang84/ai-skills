# using-claude (retired)

Retired on 2026-10-07 and replaced by [`using-harnesses`](../using-harnesses/SKILL.md): Claude calls
run through `using-harnesses/scripts/review.sh claude`, which gives Claude no tools, refuses secrets
and runs it in safe mode. `claude-call.sh` is gone: it gave the reviewer read access to caller
directories without a secret check (kb #202).
