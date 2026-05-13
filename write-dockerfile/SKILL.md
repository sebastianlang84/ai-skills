---
name: write-dockerfile
description: Use this skill when the user wants to create or substantially rewrite a Dockerfile. Covers base image selection, multi-stage builds, cache-friendly layers, non-root runtime, secrets handling, .dockerignore, and post-write validation.
---

# Write Dockerfile

Use this skill for authoring production-ready Dockerfiles, not for auditing an existing Dockerfile only.

## Workflow

1. Gather context before writing: language, runtime version, build tool, output artifact, system dependencies, port, existing Docker/Compose files, and whether `.dockerignore` exists.
2. Apply the authoring rules in `references/dockerfile-authoring.md`.
3. Keep changes local to the Docker build context unless the user explicitly expands scope.
4. If a required fact is unclear and a wrong guess could affect security, runtime behavior, or persistence, stop and ask.
5. After writing, validate structurally and, when Docker is available and in scope, run a build or explain why it was not run.

## Output expectations

- Dockerfile with pinned base image tags, explicit `WORKDIR`, cache-aware dependency installation, non-root final runtime, and exec-form `CMD`/`ENTRYPOINT`.
- `.dockerignore` when absent or inadequate for the build context.
- No secrets copied into images or stored with `ENV`.
- Brief final report listing changed files, validation, and residual risks.
