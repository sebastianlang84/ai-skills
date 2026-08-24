---
name: git-guardrails
description: "Install or adjust the hook that blocks irreversible git commands before Claude Code can run them."
disable-model-invocation: true
---

# Git Guardrails

`git-workflow` says destructive Git needs the operator's approval. That is prose — the agent can ignore it, and broad permission rules like `Bash(git push:*)` pre-approve the dangerous forms anyway. This skill installs the enforcement: a `PreToolUse` hook that inspects every Bash command and refuses the irreversible ones before they execute.

The script is [scripts/block-dangerous-git.py](scripts/block-dangerous-git.py).

## The rule it encodes

**Block the force variant, allow the guarded one.** Anything that only turns dangerous once pushed — `rebase`, `commit --amend` — stays allowed, because force-push itself is blocked.

| Blocked | Still allowed |
|---|---|
| `push --force` / `-f` / `+refspec` | `push --force-with-lease` (refuses if the remote moved) |
| `push --delete`, `push :ref` | the same, when every named branch is *provably contained* in the remote's default branch (see below) |
| `reset --hard` | `reset` soft/mixed |
| `clean -f` (any bundling) | `clean -n` |
| `checkout .` / `restore .` | targeted paths (`restore src/foo.ts`) |
| `stash drop` / `stash clear` | `stash list` / `pop` |
| `branch -D` | `branch -d`; and the forced form when the branch is *provably absorbed* (see below) |
| `filter-branch` / `filter-repo` | — |

A blocked call exits 2, so the model receives the reason and the safe alternative instead of the command running.

Commit and tag messages are blanked before matching, so `git commit -m "undo reset --hard"` is not mistaken for a reset.

## The one exception: deleting a branch that is provably absorbed

Every other rule guards something the guard cannot re-derive. Branch deletion is different: "this destroys nothing" is a *checkable fact*, and leaving it unfixable made the guard cost real work — merged branches piled up on remotes because only the operator could ever remove them, and in nightshift's case a leftover ref silently held its throughput cap at zero for nights.

Two rules carry the exception: `deletion_is_provably_merged` for `push --delete`, and `branch_delete_is_provably_absorbed` for the local forced delete. Each allows the command when **every** named branch is contained in the default branch, so the content survives in the base and the ref is recreatable from it.

`_absorbed_into` is the shared proof, and it asks two questions in turn:

1. **`merge-base --is-ancestor`** — the cheap answer, covering fast-forward and merge-commit integration.
2. **`merge-tree --write-tree`** — merge the branch into the default branch in memory. An identical tree means the branch can no longer contribute anything the base lacks.

The second question exists because a **squash merge is not an ancestor**. The change is in the default branch byte for byte, under a commit that lists the branch nowhere in its ancestry — so an ancestry-only test blocks every cleanup in a repository that squash-merges, which is most review flows. Measured on 2026-08-24 in `nightshift`: four consecutive squash merges, four refs the guard would never release. Question 2 is not a weaker bar than question 1; it is the same bar, asked in a way a squash can answer.

What it does **not** preserve is the branch's own history — commit messages, authorship, the order of the work. A squash merge has already discarded those, which is why proving the content is the right bar here and not a lowered one.

Both rules are built to answer "no" whenever they are not certain:

- For the remote case the sha comes from **`ls-remote`, the live remote** — never from a remote-tracking ref, which may be stale and hide commits pushed since the last fetch. For the local case the branch must resolve under `refs/heads/`.
- A conflict, an unrelated history, or any git failure during the in-memory merge answers "cannot prove" and stays blocked. So does a branch whose change the default branch has since reverted.
- One unqualified ref voids the whole batch — deletions are not partially allowed.
- Never: tags, the default branch itself, the checked-out branch, URL remotes, `--mirror`/`--all`/`--tags`, `-r`/`-a` on `git branch`, or a command line carrying any shell metacharacter (composition and substitution defeat single-command parsing). `cd repo && git push --delete x` is therefore blocked; write `git -C repo push --delete x`.
- Any probe that errors, any option the parser does not recognise, any repo it cannot locate → blocked.

If you want the strict old behaviour back, delete the `DELETE_RULE` and `BRANCH_DELETE_RULE` handling from `check()`.

## Install

Add to the `hooks` block of `~/.claude/settings.json` (project scope: `.claude/settings.json`). Merge into any existing `PreToolUse` array rather than replacing it:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/wasti/.agents/skills/git-guardrails/scripts/block-dangerous-git.py"
          }
        ]
      }
    ]
  }
}
```

Pointing at the repo copy means `git pull` updates the guard. Note that `~/.claude/settings.json` itself is not version-controlled — the hook registration has to be re-added on a fresh machine.

## Adjust the list

Edit `RULES` in the script: each entry is `(regex, what it destroys, what to do instead)`. The last two strings are what the model is told, so write the alternative as an instruction it can follow.

## Verify after any change

Run the suite first — it builds real repositories, because the exceptions are proved against live git state and a mocked git would only test the mock:

```bash
python3 /home/wasti/.agents/skills/git-guardrails/scripts/test_block_dangerous_git.py
```

It covers both directions of both exceptions: a squash-merged branch is released, a branch carrying work the default branch lacks is not, and neither is one whose change was landed and then reverted.

The script has no side effects, so single cases can also be tested directly — a rule that does not fire is worse than no rule:

```bash
printf '{"tool_input":{"command":"git reset --hard"}}' | python3 scripts/block-dangerous-git.py; echo "exit=$?"   # expect 2
printf '{"tool_input":{"command":"git status"}}'       | python3 scripts/block-dangerous-git.py; echo "exit=$?"   # expect 0
```

Check both directions: every command you meant to block exits 2, and the safe variant beside it still exits 0.

The deletion exception needs a real repo to judge, so pass a `cwd` and point it at a throwaway sandbox — a bare remote with a `merged` branch at the tip of `main`, an `unmerged` branch ahead of it, and a tag:

```bash
printf '{"tool_input":{"command":"git push origin --delete merged"},"cwd":"/tmp/sandbox/repo"}'   | python3 scripts/block-dangerous-git.py; echo "exit=$?"   # expect 0
printf '{"tool_input":{"command":"git push origin --delete unmerged"},"cwd":"/tmp/sandbox/repo"}' | python3 scripts/block-dangerous-git.py; echo "exit=$?"   # expect 2
```

Note that an agent cannot run these two itself: the hook inspects its own Bash command line, sees the quoted `git push --delete` inside the `printf`, and blocks it. Verify the exception by attempting the real deletion in a throwaway sandbox instead, where a wrong "allow" costs nothing.
