# Repo Structure Audit Profile

Purpose: focused audit of repository layout, naming, navigation, ownership, and document-role boundaries. Use this when the user asks about repo organization but not a full monorepo hygiene audit.

Scoring: ✅ fulfilled / ⚠️ partial / ❌ missing / N/A.

## 1. Repository purpose and boundaries

- top-level purpose is documented in the README or equivalent entry point
- it is clear what content belongs in the repo and what does not
- active, reference, generated, archived, experimental, and legacy content are distinguishable
- product, infrastructure, tooling, documentation, and examples are not accidentally mixed

## 2. Top-level layout

- directory names are self-explanatory
- similar things live in similar places
- singular/plural, hyphen/underscore, and suffix conventions are consistent
- there are no unexplained one-off top-level folders
- generated or build outputs are excluded or clearly isolated

## 3. Navigation and entry points

- README explains the major folders
- deeper docs are discoverable from README or docs index
- important operational or policy files are easy to find
- links between root docs, docs folders, and service folders work
- newcomers can identify where to start within a few minutes

## 4. Repeated unit layout

- services/apps/packages/modules use a consistent internal skeleton where practical
- required files such as README, config examples, tests, Dockerfile, or package metadata are predictable
- differences between units are intentional, documented, or clearly justified
- naming of variants such as dev/test/prod is not ambiguous

## 5. Governance and document roles

- policy, runbook, ADR, changelog, backlog, memory/state, and reference material are not conflated
- normative rules are easy to distinguish from examples or history
- document update triggers are defined for important maintained files
- open tasks do not live in policy docs

## 6. Configuration and env layout

- secrets, non-secret config, examples, and local overrides have clear locations
- env files are named consistently
- committed examples are present where needed
- runtime-only files are ignored when they may contain sensitive or host-specific values

## 7. Ownership and lifecycle signals

- owners or responsible teams are clear where needed
- deprecated, retired, or experimental areas are marked
- forks or vendored content are labeled with upstream and local-change context
- cleanup or archive rules exist for obsolete areas

## 8. Operational structure

- build/deploy/run artifacts live near the service or in a clearly named central location
- ports, volumes, domains, jobs, and persistent data have discoverable documentation when relevant
- backup-relevant paths are not hidden in obscure files only

## 9. Friction and drift indicators

- same fact is not maintained in many places
- naming does not force agents or contributors to guess intent
- docs and code/config agree on paths and commands
- scripts do not encode layout assumptions that docs contradict

## Output template

```markdown
## Repo Structure Audit — Summary
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
| Area | Status | Evidence | Recommended fix |
|---|---|---|---|

## Quick wins
-

## Larger measures
-
```
