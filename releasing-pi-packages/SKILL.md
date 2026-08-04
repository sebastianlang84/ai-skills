---
name: releasing-pi-packages
description: "Release a Pi extension or Pi package from a local Git repo. Use when preparing, versioning, tagging, packing, or pushing releases for Pi packages/extensions after code changes are verified. Extends generic git workflow with Pi/package-specific checks such as package.json pi manifest, changelog, npm pack dry-run, extension/tool tests, and post-release indexing notes. Do not use for ordinary code edits or non-Pi package releases."
---

# Releasing Pi Packages

Use this skill for release closeout of Pi extensions and Pi packages that live in local Git repos.

## Preconditions

- The implementation slice is complete and reviewed enough to release.
- The user has explicitly approved mutating Git operations before commit, tag, push, or release publication.
- Repository-local instructions override this skill.
- If the worktree has unrelated dirty changes, stop before staging or committing.

## Workflow

### 1. Identify release scope

Inspect:

- current branch and worktree;
- package name and version source, usually `package.json`;
- `package.json` `pi` manifest and bin/extension entrypoints;
- changelog/release-note file;
- previous tags and tag convention;
- whether release is npm-published, Git-tag-only, or local package update.

Classify SemVer impact using `git-workflow` and state the concrete next version before release changes.

### 2. Verify package readiness

Run the smallest relevant gates from repo scripts. Common Pi package checks:

```bash
npm run typecheck
npm test
npm pack --dry-run
git diff --check
```

Add repo-specific gates when present, for example:

- extension prompt/tool injection checks;
- search/context/eval quality gates;
- token-injection or fixture leak checks;
- package manifest/path validation.

Do not lower thresholds or rewrite eval cases as a substitute for a real fix.

### 3. Update release metadata

For release-relevant changes:

- bump `package.json` and lockfile if present;
- move changelog entries from `Unreleased` to `vX.Y.Z - YYYY-MM-DD` or repo convention;
- keep release notes factual and operator-facing;
- avoid secrets, local-only paths unless operationally relevant, and raw auth output.

### 4. Commit and tag

After explicit approval and successful verification:

1. Stage only intended files.
2. Commit using repo convention.
3. Create an annotated tag only when approved.
4. Re-run quick checks if version/changelog edits could affect package output.
5. Push branch and tag only when target remote/branch/tag are explicit.

### 5. Post-release checks

After push/tag:

- confirm branch is synced and worktree clean except pre-existing unrelated changes;
- if CodeMap is approved for the repo and Git state changed, refresh the index before relying on CodeMap state;
- record durable release memory only when the release matters for future sessions;
- report version, commit, tag, pushed state, verification, and any deferred publication step.

## Output shape

Keep closeout concise:

```text
Released <package> vX.Y.Z
Commit/tag: <sha> / <tag>
Pushed: <remote>/<branch>, tag <tag>
Verification: <checks>
Notes: <deferred npm publish or follow-up>
```

## Boundaries

- Use `pi-extension-packaging` for structural design before release readiness.
- Use `git-workflow` for generic branch, commit, push, and SemVer safety.
- Use `tool-update-checker` to discover whether installed local tools have upstream updates.
- Do not publish to npm, GitHub Releases, or push tags without explicit user approval.
