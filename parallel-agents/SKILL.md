---
name: parallel-agents
description: Coordinating several agent sessions working the same repo at once — detecting that another session is already on your topic, claiming work, and the hook that refuses to create a file another live session already has. Use when several sessions run in parallel, when a merge turns up duplicate work, when a Write is refused as a collision, or when deciding whether to start on something another agent may already hold.
---

# Parallel agents on one repo

Three to five sessions run on this machine at once, in sibling worktrees of the same repo. The
failure mode is not what the isolation rules address.

**Worktrees prevent interference. They do not prevent duplication.** Two sessions creating the same
new file is invisible to Git — an add/add divergence does not exist until both sides do — so it
surfaces at merge, after both sides have paid. That has happened once here, to two sessions that
were each following the isolation rules perfectly.

The argument, the incident and the list of what still has no rule live in
`~/.agents/brain/preferences/parallel-agents-git.md`.

## Who holds what, right now

```bash
python3 ~/.agents/skills/parallel-agents/scripts/ownership.py         # this repo
python3 ~/.agents/skills/parallel-agents/scripts/ownership.py --all   # every live session
```

Joins `git worktree list`, the harness session files (`~/.claude/sessions/<pid>.json`) and
`kill -0` into worktree → branch → live session. **Nothing is stored**, so nothing goes stale and
the answer is correct the instant a session dies. A registry file would have to be written,
refreshed and cleaned up, and every one of those is a way for it to lie — a stale claim blocks real
work with the authority of a fact. Pid reuse is checked, not assumed away, via the recorded process
start time.

What follows from it:

- **A branch with a live owner is not yours** — do not push to it, rebase it, or check it out
  elsewhere. `SendMessage` to the printed session name.
- **A non-fast-forward push rejection**: live owner → stop and talk to them, someone is building on
  the history you would rewrite. No owner → the branch is unattended, `fetch` and rebase, no human
  needed.
- It reports that a session is live, not what it is *thinking about*. Intent is what messaging is
  for.

## Before substantial work

```bash
git worktree list                                 # sibling checkouts of this repo
git branch -a --sort=-committerdate | head        # who has been working, and on what
git fetch && git log --oneline -5 origin/<base>   # did the base move under you
```

`ListAgents` names the live sessions, and is the only probe that sees a session which has not
committed anything yet. When one of them is in your repo, say which files you are taking
(`SendMessage`) before writing, and answer in kind when someone tells you.

Re-check the base **before merging**, not only before starting.

## If a Write is refused

`scripts/warn-duplicate-write.py` runs as a `PreToolUse` hook on `Write`. When the file you are
about to create already exists in a sibling worktree as recent, newly added work, the write is
**denied** and the message names the file to read.

Do exactly that: read their version. The denial lifts as soon as you have (a `PostToolUse` hook on
`Read` records it). **A plain retry stays denied** — retrying is not reading. Then decide
deliberately: extend their version, or use `SendMessage` to agree who owns the file.

If their version changes after you read it, the gate re-arms — you approved specific bytes, not a
filename.

## Why it denies instead of warning

The first version allowed the write and attached a note. A cross-vendor review pointed out that
"read their version first" is temporally impossible that way, and a live test confirmed it: the file
is created, and the model only sees the note on the next turn. The merge risk was caught; the
duplicated file and the duplicated work — the actual costs — were not.

Denying costs the operator nothing. It cancels one tool call and hands the reason to the model,
which can resolve it unattended. It is not a permission prompt and does not wake anyone.

## What it deliberately does not do

- **Weak evidence is silent.** Only a path that exists in an *attached sibling worktree*, is a *new
  addition* there relative to the merge base, and whose worktree is held by a **live session** will
  gate. Liveness is a fact from `ownership.py`, not the file-mtime guess the first version used, so
  an abandoned worktree never blocks a legitimate recreation. An earlier draft also searched all
  history; that reports a file deleted two years ago forever, so it was removed. A check that cries
  wolf gets routed around.
- **It fails open.** Every internal error, timeout or unreadable state allows the write. The whole
  hook runs under a single 250 ms budget. Only a *detected* collision fails closed.
- **It is opt-in per repository**, so no repo policy is baked into a machine-wide hook:

  ```bash
  git config --local agents.duplicate-write-guard true
  ```

  Local config lives in the common git dir, so every linked worktree inherits it. Enabled for
  `~/dev/brain`.

## Known gaps

- A millisecond-wide check-then-write race remains; the real incident was minutes wide, so the
  `O_EXCL` reservation that would close it is not bought yet.
- Files created through Bash (`>`, `tee`, `cp`) bypass it — `Write` is the only deterministic event
  that knows the intended path.
- Two sessions appending to the same *existing* file (`log.md`) never trigger it. That one is an
  ordinary content conflict and does surface at merge.
- Different filenames for the same work defeat it entirely. This is an exact-path last line of
  defence, not a solution to semantic duplication — that stays with cross-session messaging.

Test it without waiting for a real collision:

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","cwd":"<repo>","session_id":"t",
       "tool_input":{"file_path":"<path>"}}' \
  | python3 ~/.agents/skills/parallel-agents/scripts/warn-duplicate-write.py
```

Silence means no collision. Median 53 ms, p95 79 ms measured under load 4 with nine live sessions;
bare Python start-up is 14 ms of that.
