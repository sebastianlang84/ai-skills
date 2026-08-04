---
name: evaluating-local-tools
description: "Evaluate an external repo, CLI, Pi extension, or local utility for possible use on this machine. Use when the user asks whether a tool has value, how heavy/risky it is, or to test it standalone before integrating. Emphasizes read-only research first, isolated installs/smoke tests, credential safety, and a clear adopt/skip verdict. Do not use for ordinary version update checks."
---

# Evaluating Local Tools

Use this skill to assess a third-party repo, CLI, Pi extension, or local utility before adding it to a project or workflow.

## Goal

Produce a grounded adopt/skip/defer recommendation from minimal safe evidence, then run only the smallest standalone smoke test the user has approved or clearly requested.

## Safety defaults

- Start read-only: inspect README, package metadata, install docs, license, release/status notes, and existing local install state.
- Do not enter credentials, OAuth flows, production tokens, browser-cookie sessions, paid API keys, or account-write modes unless the user explicitly approves that step.
- Prefer temp dirs, containers, disposable homes such as `/tmp/<tool>-home`, and localhost-only ports.
- Keep candidate tools out of production repos until a clear integration decision exists.
- Never run remote install scripts via pipe-to-shell. If a command fetches and executes remote code (`npx`, `curl | sh`, installer scripts), call it out and ask unless the user already approved a standalone install/test.
- Treat scraping, social-media, browser-session, email, and credential-capture tools as higher risk; use read-only/local-cache modes first.

## Workflow

### 1. Clarify the intended use

Identify:

- target job the tool might solve;
- whether this is research-only, standalone smoke test, or integration planning;
- data sensitivity and write risk;
- success condition for the evaluation.

If unclear, ask one concrete question before installing or running anything stateful.

### 2. Inspect evidence first

Gather compact evidence:

- current repo status/health: WIP vs stable, maintenance, license;
- runtime and system requirements;
- install modes and reversibility;
- local state paths and network/listen behavior;
- CLI/API output formats, especially JSON/scriptable modes;
- auth, rate-limit, privacy, and write capabilities;
- overlap with existing skills, tools, extensions, or repo code.

### 3. Choose the smallest smoke test

Prefer this order:

1. `--help`, `--version`, config/status commands.
2. Initialize with disposable state.
3. Run local/read-only commands on empty/demo data.
4. Import explicit local fixture/export data.
5. Only then consider live authenticated reads.
6. Avoid live writes unless that is the explicit purpose and the user approves.

For Node tools with incompatible host Node versions, prefer a disposable Docker run over changing the host runtime.

### 4. Report integration fit

Return:

- what was tested and where state was written;
- whether the tool works standalone;
- concrete useful capabilities for the target project;
- risks/costs/operational burden;
- smallest safe integration seam if worth pursuing;
- cleanup command for temp artifacts;
- verdict: `adopt`, `defer`, `skip`, or `needs more evidence`.

## Good outputs

- “Standalone works, but integration should be disabled-by-default and consume JSON from local cache only.”
- “Skip for now: install is heavy, no stable CLI, duplicates existing CodeMap capability.”
- “Needs more evidence: cannot evaluate live-read quality without an export or explicit OAuth approval.”

## Boundary with other skills

- Use `tool-update-checker` for update/version checks of known installed tools.
- Use `pi-extension-packaging` when the tool is a Pi package/extension and the task is repo structure or package manifest design.
- Use `secrets-env` when evaluation changes credential or environment handling.
- Use `git-workflow` before committing, tagging, or pushing any resulting local changes.
