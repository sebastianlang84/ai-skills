---
name: secrets-env
description: Use this skill when the user wants to design, review, or fix secrets and environment-variable handling. Covers .env boundaries, committed examples, secret-safe documentation, Compose env files, and leak-prevention checks.
---

# Secrets and Env

Use this skill for tasks involving `.env`, `.env.example`, config examples, secret boundaries, runtime configuration, or suspected secret exposure.

## Workflow

1. Classify each variable as secret, sensitive non-secret, or ordinary config.
2. Apply `references/secrets-env-checklist.md`.
3. Keep real secrets out of tracked files, logs, docs, prompts, and final responses.
4. Use placeholders in examples; never invent plausible-looking credentials.
5. Stop and ask before changing authentication, credential rotation, production secrets, or secret-manager behavior.
6. Verify with targeted searches or config rendering where safe, without printing secret values.

## Output expectations

- Clear source-of-truth boundaries for secret and non-secret config.
- Safe example files with fake values only.
- Any residual exposure risk called out without revealing sensitive data.
