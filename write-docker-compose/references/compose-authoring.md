# Docker Compose Authoring Reference

## Core guardrails

1. Apply `handling-secrets` for secret classification, env-file boundaries, ignore rules, committed examples, and leak checks; this reference keeps only the Compose-specific rules.
2. Pass every env layer as an explicit `--env-file` argument in run instructions instead of relying on unstated shell state. For `${VAR}` interpolation, shell variables override `--env-file` values and a later `--env-file` overrides an earlier one; `environment:` overrides `env_file:` inside the container.
3. Do not add host port exposure without rationale and matching documentation.
4. Prefer internal Docker networking over host exposure when only containers need access.
5. Name volumes and bind mounts clearly. Document backup-relevant persistent data.
6. Keep Compose changes isolated to the affected service or stack.
7. Validate with `docker compose ... config` before considering the work complete. Its output contains interpolated secrets: send it to `/dev/null` or redact it.

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
