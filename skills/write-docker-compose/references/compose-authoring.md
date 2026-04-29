# Docker Compose Authoring Reference

## Core guardrails

1. Do not put passwords, tokens, API keys, private keys, or other secrets directly in committed Compose files.
2. Separate secrets from non-secrets. A common pattern is:
   - `.env` for gitignored runtime secrets
   - `.config.env` or service-local `.config.env` for gitignored or environment-specific non-secret values
   - `*.example` files for committed placeholders and documentation
3. Prefer explicit `--env-file` arguments in run instructions instead of relying on unstated shell state.
4. Do not add host port exposure without rationale and matching documentation.
5. Prefer internal Docker networking over host exposure when only containers need access.
6. Name volumes and bind mounts clearly. Document backup-relevant persistent data.
7. Keep Compose changes isolated to the affected service or stack.
8. Validate with `docker compose ... config` before considering the work complete.
9. Do not paste rendered secrets into chat, docs, logs, or audit output.

## Context checklist

Before editing, determine:

- target Compose file and service scope
- whether this is a new file, small edit, or rewrite
- existing naming and layout conventions
- image tags or build contexts
- dependency and readiness relationships
- required env vars and whether each value is secret or non-secret
- ports that need host access versus internal-only ports
- persistent paths and backup expectations
- docs or example env files that must stay in sync

## Authoring guidance

- Pin image tags unless the project has a controlled alternative versioning policy.
- Prefer service names, network names, and volume names that explain purpose.
- Use `depends_on` only for real startup relationships; add healthchecks when a meaningful readiness probe exists.
- Keep comments sparse and focused on non-obvious operational decisions.
- Use `env_file` or variable substitution intentionally; avoid mixing many config sources without documenting precedence.
- Avoid broad default exposure such as `0.0.0.0` bindings unless explicitly required.
- Keep local-development conveniences out of production Compose files unless clearly profiled or documented.

## Secrets and env checklist

- real secrets are absent from tracked files
- `.env*` and service-local runtime env files are gitignored when they can contain sensitive values
- committed examples use fake placeholders only
- required variables are discoverable from examples or docs
- validation output is redacted or not shown when it could include secrets

## Validation examples

Adjust paths to the project:

```bash
docker compose --env-file .env --env-file .config.env --env-file <service>/.config.env -f <service>/docker-compose.yml config >/dev/null
```

If only non-secret examples are available, validate with those and state the limitation. If Docker is unavailable, report that rendered-config validation was not run and why.

## Final review

Before finalizing, inspect rendered or source configuration for accidental:

- host-port exposure
- anonymous or ambiguous volumes
- missing env examples
- secret-like literal values
- unexpected networks
- unrelated service changes
