# Dockerfile Authoring Reference

## Hard constraints

1. Pin base image versions with concrete tags; do not use `latest`.
2. Use multi-stage builds when build tools, compilers, generated assets, or development dependencies are needed. Name stages, for example `AS build` and `AS runtime`.
3. The final stage must run as a non-root user. Prefer an official image's existing user when suitable.
4. Do not bake secrets into the image. Do not use `ENV` for tokens, passwords, API keys, or private material. Do not copy secret files.
5. Require a `.dockerignore` in the build context. At minimum exclude VCS metadata, dependency folders, build outputs, env files, logs, and editor files.
6. Use exec-form `CMD` or `ENTRYPOINT` for correct signal handling.
7. Set `WORKDIR` early; do not rely on `/`.
8. Copy dependency manifests before application source so dependency layers can be cached.
9. Keep runtime images lean. Do not install editors, debug tools, or unnecessary network tools in production images.
10. Prefer `COPY` over `ADD` unless tar extraction or remote URL behavior is specifically needed.
11. Do not run `apt-get upgrade` in Dockerfiles; update by rebuilding from a newer base image.
12. Clean package-manager caches in the same layer where packages are installed.
13. Add short comments only for non-obvious choices and trade-offs.

## Context checklist

Before writing, identify:

- language/framework and runtime version constraints
- package/build tool and lockfile
- build artifact location
- required native/system libraries
- service port
- runtime environment variables and which are secrets
- existing `.dockerignore`, Compose files, README, or deployment docs

## Base image guidance

- Node.js: `node:<major-or-major.minor>-alpine` when native dependencies allow; otherwise a slim Debian variant.
- Python: `python:<version>-slim` unless the app requires a different distro.
- Go: build with `golang:<version>-alpine` or slim; run with distroless/static or Alpine when compatible.
- Rust: build with `rust:<version>` variant suited to dependencies; run with distroless, slim, or Alpine as appropriate.
- Java: build with a JDK image and run with a JRE image such as an Eclipse Temurin runtime variant.
- Static sites: build with the framework runtime; serve with a pinned web-server image.

Match the project's declared runtime version where possible.

## Canonical structure

```dockerfile
FROM <build-base> AS build
WORKDIR /app

# Copy manifests first for dependency-layer cache reuse.
COPY <manifest-files> ./
RUN <install-build-dependencies>

COPY . .
RUN <build-command>

FROM <runtime-base> AS runtime
WORKDIR /app

COPY --from=build /app/<artifact> ./<artifact>

USER <non-root-user>
EXPOSE <port>
CMD ["<executable>", "<arg>"]
```

Adapt this structure to the stack. Compiled binaries often need only the binary and minimal runtime files in the final stage.

## `.dockerignore` baseline

```gitignore
.git
node_modules
dist
build
*.env
*.env.*
.env.example
*.log
.DS_Store
.vscode
.idea
Dockerfile
docker-compose*.yml
README.md
docs/
tests/
```

Adjust for the stack, such as `__pycache__/`, `*.pyc`, `target/`, `bin/`, or `obj/`.

## Verification checklist

- `.dockerignore` exists and is non-empty.
- Dockerfile has no unreviewed `COPY . .` pattern without an effective ignore file.
- final stage contains `USER`.
- no secret-like `ENV` names or copied secret files.
- base images are pinned to concrete tags.
- multi-stage build is used when build-time dependencies exist.
- `CMD`/`ENTRYPOINT` uses exec form.
- build succeeds when Docker is available and running the build is in scope.
