---
name: write-docker-compose
description: Use this skill when the user wants to create or substantially update a Docker Compose file. Covers env layering, secrets-safe configuration, ports, persistence, service dependencies, documentation impact, and rendered-config validation.
---

# Write Docker Compose

Use this skill for creating or materially changing `docker-compose.yml`, `compose.yaml`, or equivalent Compose files.

## Workflow

1. Identify the affected service or stack, existing Compose style, Dockerfiles, env files, ports, volumes, networks, dependencies, and service-local docs.
2. Apply `references/compose-authoring.md` for guardrails and authoring checks.
3. Keep scope local to the requested Compose file or stack. Do not rewrite unrelated services.
4. Stop and ask before widening exposure, weakening security, changing persistence, or guessing secret values.
5. Validate the rendered Compose config after edits and report the command/result.

## Output expectations

- Compose file with explicit, reviewable services, images/builds, ports, volumes, networks, and env sources.
- Secrets are not committed in YAML.
- Non-secret defaults are separated from secret runtime values.
- Operational docs or examples are updated only when startup, exposure, config, or backups change and the user has included that scope.
