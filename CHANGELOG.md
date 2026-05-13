# Changelog

Operator-facing changes to this global skill collection are documented here.

This repo does not version individual skills with SemVer. Use this changelog to record skill additions, removals, renames, source-of-truth changes, and enforcement changes.

## [Unreleased]

### Changed

- Added a root `.ignore` so top-level repository docs (`README.md`, `CHANGELOG.md`) are not discovered as Pi skills, and corrected README layout docs for skill-local `scripts/` versus repo-level `_scripts/`.
- Flattened the repository so Pi discovers skill folders directly from the repo root at `~/.pi/agent/skills`.
- Renamed `manage-agent-context` to `managing-agent-context` to match the preferred gerund naming convention.
- Updated `skill-creator` naming guidance to prefer gerund skill names while allowing established noun/action names.
- Added README/CHANGELOG enforcement via a shared metadata checker, GitHub Actions workflow, and local Git hooks.

### Removed

- Removed unused or archived runtime skills from the active collection: `audit-manager`, `claude-api`, `doc-coauthoring`, `mcp-builder`, `pdf`, and `to-prd`.
- Dropped stale repo-only skills that were not present in the active runtime skill set during the flattening migration.
