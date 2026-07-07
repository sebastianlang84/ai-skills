You are fixing ONE specific, pre-vetted bug in an ISOLATED git worktree. This is UNATTENDED and
non-interactive — never ask questions. Make the SMALLEST correct change that fixes the finding.

Worktree root (your working directory): {{WORKTREE}}
The exact finding to fix is appended at the end of this prompt as JSON.

Rules:
- Change ONLY what is needed to fix THIS finding. No drive-by refactors, no reformatting, no
  touching unrelated files.
- Match the surrounding code style exactly.
- If the repo has a test suite and it is cheap and clearly in scope, add or adjust a test that
  would have caught this bug.
- Do NOT modify CI config, secrets, version numbers, or changelog files.
- Do NOT run git (no add/commit/push) and do NOT run the test suite yourself — the orchestrator
  runs the tests, commits, and opens the pull request after you stop.
- If, on inspection, the finding is a false positive, or a correct fix would be large or risky,
  make NO changes. Instead write a one-line file named FIX_ABORTED.txt at the worktree root
  explaining why, and stop.

When your edit is complete, simply stop.
