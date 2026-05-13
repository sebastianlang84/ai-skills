---
name: pi-extension-packaging
description: Use this skill when designing, reviewing, restructuring, packaging, or auditing Pi extensions and Pi Packages, especially to choose clean repo structure (`src/index.ts` vs `extensions/`), package.json `pi` manifests, discovery paths, dependencies, and bundles with skills, prompts, or themes. Do not use for unrelated TypeScript work or non-Pi package management.
---

# Pi Extension Packaging

Use this skill to help choose and review clean, documented structures for Pi extensions and Pi Packages.

## Core distinctions

- **Extension**: TypeScript module extending Pi with tools, commands, shortcuts, flags, events, or UI elements.
- **Skill**: on-demand capability description for agents; it is not extension code.
- **Pi Package**: npm, git, or local-path bundle that can include extensions, skills, prompt templates, and themes.
- Do not call a bundle a "multi-extension package" as official terminology; use **Pi Package**.

## Default recommendations

- For one extension, prefer `src/index.ts` plus explicit `package.json` `pi.extensions` pointing at `./src/index.ts`.
- Use `extensions/`, `skills/`, `prompts/`, and `themes/` when the package intentionally bundles multiple Pi resources.
- Use explicit `package.json` `pi` mappings for non-conventional paths.
- Put runtime dependencies in `dependencies`, not only `devDependencies`.
- Keep README concise and avoid secrets in `package.json`, README, AGENTS files, or `.env`.

## Workflow

1. Decide first: single extension or Pi Package with multiple resources.
2. Inspect `package.json`, resource folders, and configured settings before restructuring.
3. Recommend the smallest structure that matches the artifact.
4. Verify runtime dependencies and `pi` manifest paths.
5. Use the audit commands from the reference when reviewing an existing repo.

## Detailed reference

For the full mini best practice, structures, discovery paths, manifests, examples, decision table, and audit commands, read `references/pi-extension-packaging.md`.
