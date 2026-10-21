# Calling codex

For a review, use `scripts/review.sh codex …` ([review.md](review.md)); it fixes every flag below.
Every other Codex call — a question, a scouting search, a worker that writes — goes through
`scripts/codex_call.py` ([Other calls](#other-calls-codex_callpy)).

## The reviewer home

codex reads `AGENTS.md` and user skills from `$CODEX_HOME` on every run, and `--ignore-user-config`
skips only `config.toml`. Reviews therefore run with `CODEX_HOME=~/.codex-review`: its own login, no
`AGENTS.md`, nothing in `skills/` but codex's built-in `.system`. `review.sh` refuses a home that
breaks any of that, and an `auth.json` that is a symlink or readable by others (mode 600; on Windows
no grant beyond you, SYSTEM and Administrators). Set it up once:

```bash
mkdir -m 700 ~/.codex-review
CODEX_HOME=~/.codex-review codex login --device-auth
# Windows (Git Bash): chmod changes nothing there; drop inherited grants such as CodexSandboxUsers
icacls "$(cygpath -w ~/.codex-review/auth.json)" //inheritance:r //grant:r "$(whoami):F" '*S-1-5-18:F'
```

Never copy the everyday `auth.json` there: codex rotates the refresh token on renewal, and the copy
that renews second is logged out. Use this home for nothing but reviews; `--resume` trusts the
sessions stored in it.

## Flags review.sh passes

| Flag | Why |
|---|---|
| `exec --json` | non-interactive; the event stream carries the thread id (`thread.started`) |
| `-C <empty dir>` / `cd` | codex loads `AGENTS.md` from its working directory up to the git root; an empty directory outside git loads none |
| `HOME=<that empty dir>` | codex also lists user skills from `$HOME/.agents/skills`, whatever `CODEX_HOME` says (measured on 0.160.1: 70 skills leaked; `--enable skip_host_skill_discovery` and `-c skills.enabled=false` did not stop it). `CODEX_HOME` stays absolute, so the login still works |
| `-s read-only` (new), `-c sandbox_mode="read-only"` (resume) | second line of defence; `exec resume` accepts neither `-s` nor `-C` |
| `timeout --kill-after=10 1800` | the deadline holds even for a process that ignores TERM |
| `--ignore-rules --ignore-user-config` | no execpolicy rules, no `config.toml`; auth still comes from `CODEX_HOME` |
| `--disable memories` | no content carried from one review thread into another |
| `--disable shell_tool unified_exec view_image apps plugins browser_use computer_use in_app_browser`, `-c web_search="disabled"` | no tools: read-only blocks writes, not reads, so with a shell codex reads any file of the user (measured on 0.160.1: `cat /etc/hostname` ran with the shell, `NO_SHELL` without). The reviewer sees the payload and nothing else |
| `-m`, `-c model_reasoning_effort=` | the configured model and an allowed effort |
| `-o out.md` | the final answer alone |
| `-` | prompt from stdin; a direct call with the prompt as argument waits on an inherited open stdin, so close it with `< /dev/null` |

A feature renamed in a later codex release makes `--disable` fail and the round exit non-zero; check
the names with `CODEX_HOME=~/.codex-review codex features list` and update `review.sh`, never drop the
flag. Sessions persist under `~/.codex-review/sessions/YYYY/MM/DD/rollout-<time>-<id>.jsonl`; they hold the
payload.

## Resume

`codex exec resume <id> -` continues a thread in the same `CODEX_HOME`. Pass the sandbox and the
memories flag again; a resume does not inherit flags reliably. `review.sh --resume` accepts an id only
when its rollout file exists under `~/.codex-review/sessions/` and the session's first user message
opens with the role lock, so a mistyped id or an ordinary session is refused.

## Other calls: codex_call.py

`C=~/.agents/skills/using-harnesses/scripts/codex_call.py` pins model `gpt-6.1-sol`, effort
`medium`, read-only sandbox, hooks off, thread kept, and runs in the everyday `CODEX_HOME` (with
`AGENTS.md` and skills, which a worker needs and a reviewer must not have). Prompts go in as a file
or `-` for stdin. Its state is under `~/.agents/state/codex-call/`.

- Start: `python3 $C new --cwd <dir> --label <name> --detach <prompt-file>` prints a call dir.
- Collect: `python3 $C wait <call-dir>` prints `thread:`, `result:` and the answer. Exit 3 means
  still running, so call `wait` again. Exit 1 is a failure with its reason.
- Follow up in the same thread: `python3 $C resume <thread-id> --detach <prompt-file>`, then `wait`.
  A resume does not inherit the first call's `--cwd`: without it the worker runs in its call
  directory, and `workspace-write` then covers only that directory (measured 2026-10-21, kb #286:
  the target worktrees were read-only). Pass `--cwd` and `--sandbox` again on every resume of a
  worker that writes.
- Without `--detach` a call blocks; only do that for calls under 10 min.
- `python3 $C cancel <call-dir>` stops a detached call; `list` shows recent calls.
- `--search` gives Codex its native web search; `--sandbox workspace-write|danger-full-access`
  widens the sandbox for callers that must write (market-digest's fixer, peer-debate sides). Never
  use it for a review: reviews go through `review.sh`, which has no such option.
- `--model`, `--effort`, `--sandbox` or `CODEX_CALL_MODEL` / `CODEX_CALL_EFFORT` override the pins;
  `gpt-6-sol` and `gpt-6-astra` are refused.

Scouting ("where is this"): pass `--model gpt-6-luna --effort low` and append
[scout-rules.md](scout-rules.md). Pass the same two flags to every `resume` of a scout thread, or the
follow-up silently runs on the sol/medium defaults.

After a Codex update, or when a call fails in a way that looks like the CLI changed, run
`python3 $C selftest`; it checks new, an immediate resume and the sandbox against the live CLI and
records the verified version in `~/.agents/state/codex-call/selftest.json`.

## Windows

`review.sh` only starts `scripts/review.py`, which runs the same on Windows: from Git Bash, or as
`python review.py …` from PowerShell or cmd. The detached start, `wait` and `cancel` work there; the
runner holds its reviewer in a job object, so a runner that is killed takes the reviewer along; if
that job cannot be created, nothing runs (exit 2). npm's `codex.cmd` would hand every argument to
cmd.exe, so both scripts start node with the package's script directly, and refuse an argument with
`& | < > ^ %` if only the shim is found. Two
differences remain. The reviewer login is checked by its ACL instead of mode 600 (setup above). And
codex still lists the user skills in `~/.agents/skills`: `HOME` does not hide them there (measured
with codex-cli 0.160.0, also with `USERPROFILE`). The reviewer has no tools, so it sees their names
and descriptions, not any file. Over ssh to beelink, use a login shell (`bash -lc`) so `codex` is on
the `PATH`. `python3` from the Microsoft Store alias is only a placeholder: install Python, and
`review.sh` falls back to `python`.
