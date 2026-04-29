# AGENTS.md Audit Profile

Purpose: assess whether an agent policy file is clear, binding, secure, conflict-light, and usable by coding agents.

Scoring: ✅ fulfilled / ⚠️ partial / ❌ missing, with concise evidence.

## 0. Meta, scope, and role

- scoped to coding agents or defined automation classes
- repository/project scope is clear
- in-scope and out-of-scope work are clear
- relationship to system rules, repo policy, runbooks, skills, and task instructions is clear
- positioned as policy/governance, not a runbook, log, or broad manual

## 1. Binding rules

- most important rules appear early
- rules are concrete and operational: read before edit, no secrets, no silent assumptions, minimal safe changes, one technical goal per task
- modal strength is clear through MUST/MUST NOT/SHOULD/MAY or equivalent wording
- no vague filler such as "be careful" without action guidance

## 2. Deny list and safety boundaries

- destructive actions are explicitly controlled, such as reset, delete, prune, drop, or destructive migrations
- security-boundary changes are gated, such as ports, proxy exposure, auth weakening, or firewall relaxation
- credential invalidation or rotation is gated
- production, database, auth, network, persistence, backup, and migration changes have explicit safeguards

## 3. Stop-and-ask behavior

- unclear scope, target, component, or environment causes a stop
- conflicting or missing facts are handled explicitly
- breaking-change risk is covered
- stop format is useful: blocker, refused assumption, and smallest decision needed
- gates are not so broad that trivial work becomes impossible

## 4. Change policy

- freely editable versus approval-required areas are distinguishable
- dev/test expectations are clear
- sensitive domains have explicit approval requirements
- policy does not contradict git or verification workflow

## 5. Secrets and config

- secret policy is explicit
- no real secrets are present in tracked policy examples
- no secret output in chat/logs/docs
- runtime secrets are separated from tracked examples or non-secret config
- placeholder strategy is clear

## 6. Git workflow

- git governance is defined directly or delegated to a canonical workflow source
- minimal-diff philosophy is clear
- release/changelog expectations are named when functional changes occur
- destructive git operations require explicit authorization

## 7. Verification and completion

- verification is mandatory before done
- typical checks are named or profile-specific checks are required
- final report names changed files, validation, and residual risks
- there is a clear gate between "edited" and "complete"

## 8. Document routing

- policy separates roles for state/memory, active work, runbooks, ADRs, changelog, and operational docs when those files exist
- no open task backlog lives inside the policy
- no incident diary or complete runbook is embedded in policy
- routing is compact enough to prevent policy bloat

## 9. Conflict clarity

- no contradictory or competing rules
- precedence is clear enough where multiple authorities are referenced
- safe behavior is obvious when conflict occurs

## 10. Execution gates

- preflight exists
- read-only diagnosis exists
- implementation/approval boundary exists where needed
- post-change verification exists
- order is clear and consistent

## 11. Formulation quality

- rules are testable and concise
- terminology is consistent
- duplicates and near-duplicates are absent
- procedure-heavy content is linked instead of inlined
- runtime-specific boilerplate is avoided unless it changes behavior

## 12. Length and scanability

- target length is compact enough for one-pass reading
- important rules remain visible during skimming
- long files justify their length through actionable governance

## Output template

```markdown
## AGENTS.md Audit — Summary
- Overall: ✅ / ⚠️ / ❌
- Distinction-ready: yes / almost / no
- Top strengths:
  1.
  2.
  3.
- Top risks/gaps:
  1.
  2.
  3.
- Line count: N

## Findings
| Section | Status | Evidence | Recommended fix |
|---|---|---|---|

## Quick wins
-

## Larger measures
-
```
