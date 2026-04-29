# Secrets and Env Checklist

## Classification

Treat as secrets:

- API keys, tokens, passwords, private keys, client secrets, signing keys
- database credentials and connection strings containing credentials
- session secrets, JWT signing material, OAuth client secrets
- production-only credentials or anything granting privileged access

Treat as non-secret config when it is safe to publish but still environment-specific:

- ports, feature flags, log levels, public base URLs, service names
- non-sensitive timeouts, limits, runtime modes, public identifiers

When unsure, classify conservatively and ask.

## File boundaries

Common safe pattern:

- `.env`: runtime secrets; gitignored
- `.config.env`: runtime non-secrets; often gitignored if host-specific
- `<service>/.config.env`: service-local non-secrets; often gitignored if host-specific
- `*.example`: committed placeholders and documentation only

Rules:

- Do not commit real secrets.
- Do not print secrets in chat, docs, logs, or validation output.
- Commit examples with fake values such as `change-me`, `example-token`, or empty placeholders.
- Ensure ignore rules cover files that may contain runtime secrets.
- Keep required variable names discoverable from examples or docs.

## Compose and env files

- Pass env files explicitly in commands when reproducibility matters.
- Keep secret and non-secret values separate when practical.
- Do not rely on implicit shell state in documented startup commands.
- Redact or suppress rendered config output when it may include secrets.

## Review checklist

- secret-like names are absent from committed values
- examples contain only fake placeholders
- docs explain where operators put real secrets without exposing them
- ignore rules cover sensitive env files
- generated logs or validation snippets do not include secret values
- no application default silently weakens auth or uses a shared public credential

## Targeted checks

Use repository-appropriate searches and avoid printing values unnecessarily. Examples:

```bash
rg -n --hidden --glob '!*.lock' --glob '!.git/**' 'API_KEY|TOKEN|PASSWORD|SECRET|PRIVATE_KEY|BEGIN [A-Z ]*PRIVATE KEY'
rg -n --hidden --glob '!.git/**' '^\.env|\.env$|\.config\.env$' .gitignore
```

If a likely real secret is found, do not reproduce it. Report path, line number when safe, variable name if safe, and recommended containment steps.
