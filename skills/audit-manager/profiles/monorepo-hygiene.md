# Monorepo Hygiene Audit Profile

Purpose: audit large or mixed-purpose repositories for hygiene, structure, maintainability, security baseline, and operational readiness. Use for platform, infrastructure, multi-service app, deployment, tooling, or documentation-heavy repositories.

Scoring: ✅ fulfilled / ⚠️ partial / ❌ missing / N/A, with evidence and severity where useful.

## Audit metadata

Capture repository, date, auditor, scope, default branch, primary technologies, deployment model, ownership model, and last release tag when known.

## 1. Purpose, scope, and boundaries

- repo purpose is clear
- product code, infrastructure, documentation, tooling, and reference content are distinguishable
- active, experimental, archived, sandbox, and legacy areas are marked
- repo boundaries say what belongs and what does not

## 2. Top-level structure and information architecture

- top-level directories follow a recognizable pattern
- similar units are organized consistently
- names are self-explanatory and consistent
- variants such as dev/test/prod/legacy are not confusing
- entry points via README, docs, or index are clear

## 3. Ownership and governance

- repo or area ownership is defined
- governance documents have clear roles
- normative policies and reference docs are distinguishable
- update triggers for important docs are clear
- critical operational or security decisions are documented

## 4. Documentation architecture

- documentation has an obvious entry point
- docs are routed by role: policy, runbook, ADR, inventory, backlog, reference
- cross-links work
- drift-prone facts are not duplicated unnecessarily
- stale docs are removed or marked deprecated

## 5. Repeated structure patterns

- similar services/apps/modules share core artifacts
- differences are intentional and documented
- names, paths, compose files, env files, docs, and scripts follow a coherent pattern

## 6. Configuration and secrets model

- secrets and non-secrets are separated
- examples/templates exist where needed
- runtime sensitive data is not tracked
- source of truth for runtime config is clear
- missing config validation exists or its absence is documented
- secret scanning exists or risk is acknowledged

## 7. Version-control hygiene

- branch, release, tag, merge, hotfix, and rollback conventions are documented where needed
- large binaries and dumps are controlled
- `.gitignore` is realistic
- vendored code, forks, or history rewrites are consciously managed

## 8. Build, deploy, and operations

- deploy units are clear
- services can be built and started from documented steps
- network, port, domain, and routing models are documented
- environment differences are clear
- migrations, bootstrap, rollback, and patches are described when relevant

## 9. CI/CD and automation

- important quality checks are automated or documented as manual checks
- blocking versus advisory checks are clear
- link/config/lint/hygiene checks exist where useful
- policy-enforcing scripts are actually used

## 10. Script and tooling hygiene

- scripts have clear purpose and documented side effects
- critical scripts describe inputs, outputs, prerequisites, and failure behavior
- dry-run/no-op modes exist where valuable
- exit codes and logging are predictable
- obsolete scripts are removed or marked

## 11. Security baseline

- trust boundaries and exposed surfaces are documented
- administrative interfaces are protected
- defaults are conservative
- secrets, dumps, backups, tokens, and keys are handled safely
- dependency/container/secret scanning exists or gaps are visible

## 12. Dependencies and reproducibility

- important versions are pinned or controlled
- upstream images/components are known
- local forks or patches are documented
- update paths for critical dependencies are defined
- generated, vendored, foreign, and patched content is distinguishable

## 13. Inventory and drift control

- operational facts have clear sources of truth
- hosts, ports, domains, jobs, schedules, and service relations are inventoried where relevant
- update triggers exist for inventories
- duplicate maintenance is minimized

## 14. Environment separation

- dev/test/stage/prod are clearly separated
- naming and layout reduce confusion
- shared artifacts are intentional and safe
- environment-specific docs do not create excessive copy-paste drift

## 15. Binary, data, and artifact policy

- binaries, dumps, PDFs, models, media, and generated artifacts have clear handling rules
- large files are justified
- temporary data, caches, and local DBs are excluded
- test data is recognizable and safe

## 16. Change management

- important changes are documented through changelog, release notes, ADRs, or equivalent
- breaking changes are visible
- operational impact of repo changes is traceable
- temporary workarounds are not silently permanent

## 17. Maintainability realism

- structure fits actual team size and operating model
- critical maintenance does not depend on implicit personal knowledge
- documentation and automation focus on high-leverage tasks
- process is neither overformalized nor purely ad hoc

## 18. Legacy and experimental areas

- legacy, retired, and experimental areas are marked
- removed components are consistently reflected in docs and inventories
- archive/retirement patterns are consistent

## Optional: forks, vendor code, patch stacks

Use when relevant: upstream source, target version, local changes, patch order, update process, and guardrails are documented.

## Optional: automation/agent governance

Use when relevant: automation rules, secret/git/destructive-operation gates, memory/session boundaries, and governance-file overlap are clear.

## Output template

```markdown
## Monorepo Hygiene Audit — Summary
- Overall: ✅ / ⚠️ / ❌
- Scope:
- Top strengths:
  1.
  2.
  3.
- Top risks/gaps:
  1.
  2.
  3.

## Findings
| ID | Area | Status | Finding | Severity | Recommendation |
|---|---|---|---|---|---|

## Quick wins
-

## Larger measures
-
```
