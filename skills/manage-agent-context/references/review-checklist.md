# Review Checklist

Use this checklist before considering an aligned repo complete.

## Baseline files

- `README.md` exists and stays concise: project description, install, usage, and license by default.
- `AGENTS.md` exists and is short, normative, and operational.
- Agent/harness memory (Pi: pi-memory tools) contains stable context when needed, not rules or backlog; any legacy `MEMORY.md` is intentionally kept and gitignored unless explicitly versioned.
- `TODO.md` exists and contains active open work only.
- `TODO.md` uses either a SemVer roadmap or priority buckets, not both unless explicitly justified.
- `CHANGELOG.md` exists when user/operator-visible changes or versioning matter.

## Frontmatter

- Maintained Markdown files have `role`, `contains`, `not-contains`, `write-when`.
- Frontmatter matches actual content.
- Frontmatter is compact and not used for volatile details.

## Routing

- No active backlog in `README.md` or durable memory.
- No completed task diary in `TODO.md` or durable memory.
- No agent rules in `README.md` or durable memory.
- No setup instructions hidden only in `AGENTS.md`.
- No durable decisions outside the repo's chosen ADR location.

## Context engineering surface

- Repo `AGENTS.md` captures repo-specific normative context and points to global/default workflows where appropriate.
- Relevant global/repo skills are referenced by role instead of duplicating their full procedures.
- `git-workflow` remains the authority for branch/commit/merge/push/tag/release mechanics; this repo only adds local overrides/gates.
- Optional Pi extensions, scripts, hooks, or CI checks are identified when they would make context gates more reliable.

## Agent usability

- Bootstrap/read order is explicit.
- Stop-and-ask conditions are explicit.
- Verification expectations are explicit.
- Secrets handling is explicit.
- Dirty-worktree/user-change protection is explicit.
- Closeout order is explicit where repo policy matters: status, TODO cleanup, changelog/SemVer, verification, commit, release suggestion, push approval.
- Push gate expectations are explicit: TODO cleanup, CHANGELOG/SemVer decision, verification, and target branch/remote.
- Rules that must survive chat forgetfulness are routed to AGENTS.md, skills, extensions/tools, hooks, or CI rather than only memory.

## Maintenance cost

- Extra docs are justified by reuse and clear update triggers.
- Templates/placeholders are filled where facts are known.
- References point to files that exist.
- The repo does not require reading a large policy corpus for normal tasks.
