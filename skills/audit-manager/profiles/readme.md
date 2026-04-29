# README Audit Profile

Purpose: assess whether a README is useful, current, safe, consistent, and easy for its target readers to consume.

Scoring: ✅ fulfilled / ⚠️ partial / ❌ missing, with concise evidence.

## 0. Audience and scope

- target audience is clear: users, contributors, operators, security reviewers, or maintainers
- README scope is clear and deeper docs are linked
- project status is visible when relevant
- language and terminology are consistent

## 1. First 30 seconds

- project name and one-line purpose are present
- short description explains problem, solution, audience, and boundaries
- quickstart or minimal example exists when appropriate
- badges are useful and not excessive
- screenshot or diagram exists when helpful

## 2. Structure and readability

- order supports the reader journey: concept, install, usage, development, operations
- heading hierarchy is consistent
- table of contents exists for longer READMEs
- paragraphs are short and examples are copy/paste-friendly
- technical terms are explained or linked

## 3. Installation and setup

- prerequisites include runtime versions, OS/platform notes, and required tools
- install paths distinguish end-user, developer, and container usage when relevant
- commands are deterministic and version-aware
- cleanup or uninstall is documented when useful

## 4. Usage

- minimal working example shows input and expected output
- CLI/API/library examples cover common paths
- configuration examples explain important keys
- common error cases and fixes are documented

## 5. Architecture and concepts

- non-trivial systems include a high-level architecture view
- components and responsibilities are clear
- data flow, persistence, external dependencies, ports, and credentials are named where relevant
- limits and non-goals are explicit

## 6. Configuration, secrets, and security

- no real secrets, private URLs, private IPs, or credentials appear
- secret handling is explained through examples, secret manager, or runtime env guidance
- minimal permissions or API scopes are documented when applicable
- security policy or responsible disclosure path is linked when relevant

## 7. Development onboarding

- clone/install/run/test path is clear
- test, lint, format, build, and release commands are documented when they exist
- project structure overview helps contributors navigate
- contribution standards are linked when present

## 8. Operations and deployment

- deployment options are documented when relevant
- dev/test/prod differences are clear
- logs, metrics, healthchecks, migrations, backups, rollback, and resource requirements are covered when operationally important

## 9. Documentation ecosystem

- README links deeper docs, ADRs, runbooks, API docs, or examples as applicable
- changelog or releases are discoverable
- roadmap, FAQ, or issue tracker is linked when useful

## 10. Accuracy and freshness

- commands appear current and runnable
- versions match code/config
- relative links resolve
- screenshots or diagrams are not stale
- README does not contradict code, config, CI, or docs

## 11. Legal and ownership

- license is clear
- support or ownership path is visible when needed
- third-party notices are handled if relevant

## 12. Markdown rendering

- Markdown renders correctly
- tables/images are usable
- images have useful alt text
- anchors and TOC links work
- lines are readable and not dominated by huge unwrapped content

## Output template

```markdown
## README Audit — Summary
- Overall: ✅ / ⚠️ / ❌
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
