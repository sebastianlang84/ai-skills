---
name: handoff
description: Compact the current conversation into a handoff document so another agent or another harness can continue the work.
disable-model-invocation: true
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save it to the session scratchpad directory (or the OS temp directory if none is set) — never into the user's repo.

Include:

- **State**: what is done, what is in flight, what is untouched.
- **Decisions taken and why** — especially ones that are not visible in the diff.
- **Open questions** the next session must resolve before acting.
- **Suggested skills** the next agent should invoke.
- **Git state**: branch, whether the tree is dirty, what is committed vs not.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact secrets, API keys, tokens, passwords, and personal data — the document may be pasted into another harness.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the document accordingly.

Print the absolute path of the file when done.
