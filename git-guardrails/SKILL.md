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
| `push --delete`, `push :ref` | — |
| `reset --hard` | `reset` soft/mixed |
| `clean -f` (any bundling) | `clean -n` |
| `checkout .` / `restore .` | targeted paths (`restore src/foo.ts`) |
| `stash drop` / `stash clear` | `stash list` / `pop` |
| `branch -D` | `branch -d` (refuses unmerged) |
| `filter-branch` / `filter-repo` | — |

A blocked call exits 2, so the model receives the reason and the safe alternative instead of the command running.

Commit and tag messages are blanked before matching, so `git commit -m "undo reset --hard"` is not mistaken for a reset.

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

The script has no side effects, so test it directly — a rule that does not fire is worse than no rule:

```bash
printf '{"tool_input":{"command":"git reset --hard"}}' | python3 scripts/block-dangerous-git.py; echo "exit=$?"   # expect 2
printf '{"tool_input":{"command":"git status"}}'       | python3 scripts/block-dangerous-git.py; echo "exit=$?"   # expect 0
```

Check both directions: every command you meant to block exits 2, and the safe variant beside it still exits 0.
