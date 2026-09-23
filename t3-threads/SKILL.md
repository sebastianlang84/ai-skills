---
name: t3-threads
description: Find, read and message other T3 Code threads on this machine (Claude, Codex or any harness T3 runs). Use when the user mentions T3 Code or a T3 thread, or, while working inside T3 Code, names another thread by its title ("den X-Thread einlesen") and wants it read, summarised, continued or written to. Not for ChatGPT, claude.ai or e-mail threads.
---

# t3-threads

T3 Code is the local app that runs agent harnesses as threads (`t3 serve`, port 3773, data in
`~/.t3/userdata`). It is neither ChatGPT/Codex chat history nor Claude Code sessions: every T3 thread,
whatever its model, lives in T3's SQLite projection `~/.t3/userdata/state.sqlite`. The `t3-code` MCP
server of a session only offers preview, device and PR tools; it cannot list or message threads.

`D=~/.agents/skills/t3-threads/scripts`

## Read (no approval, read-only)

- `$D/t3-threads.mjs list [--project <name>] [--limit N] [--json]`: newest threads with id, project,
  harness/model and status (`running`, `waiting-for-input`, `idle`, `archived`).
- `$D/t3-threads.mjs find <text> [--limit N] [--json]`: threads whose title or messages contain `<text>`.
- `$D/t3-threads.mjs show <thread> [--last N]`: the messages of one thread. `<thread>` is an id, an id
  prefix of 6+ characters or a title fragment matching exactly one thread; on ambiguity it lists the
  candidates and exits 1. Pick by id then, and ask the user only if the candidates really compete.

The user's title may carry typos; retry with a shorter fragment or `find` before saying it is missing.
The current thread is in the list too (usually `running`); do not mistake it for the target.

## Write (only on the user's explicit request, with their text)

Sending starts a turn in the other thread and can change files there, so send exactly what the user
asked for. Get a short-lived bearer token into a private file first; it carries admin scope
(`access:write`), so never print it and keep the TTL short:

```bash
T=<session scratchpad>/t3.token
(umask 077; rm -f "$T"; t3 auth session issue --ttl 15m --label t3-threads --token-only > "$T")
T3_TOKEN_FILE="$T" $D/t3-send.mjs send <threadId> "<text>"
T3_TOKEN_FILE="$T" $D/t3-send.mjs new <projectId> <instanceId> <model> "<text>"
```

`t3-send.mjs` refuses a busy thread and a `full-access` thread unless `T3_ALLOW_FULL_ACCESS=1`. Set that
only when the user wants that thread written to. It waits for the reply (`T3_TIMEOUT_S`, default 300)
and prints JSON with `status` and `reply`. Exit codes: 3 blocked on approval/input, 4 timeout,
5 turn failed or ended without reply. Report the reply or the blocking state; a timeout does not
mean the message was lost, so check with `show <thread> --last 2`.

A live Claude Code session in T3 can also be reached with `ListAgents` / `SendMessage`, but its name
changes when T3 restarts it; the T3 route works for every harness.

## When it breaks

Both scripts need Node 22.5+ (`node:sqlite`) and read T3's internal schema, checked against T3 0.0.42.
`T3 schema changed: …` after a T3 update means the projection moved: inspect the tables with
`sqlite3 -readonly` and adapt the scripts rather than guessing.
