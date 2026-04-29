# Review Checklist

Use this checklist before considering an aligned repo complete.

## Baseline files

- `README.md` exists and explains purpose, setup, usage, verification, and status.
- `AGENTS.md` exists and is short, normative, and operational.
- `MEMORY.md` exists and contains stable context, not rules or backlog.
- `TODO.md` exists and contains active open work only.
- `TODO.md` uses either a SemVer roadmap or priority buckets, not both unless explicitly justified.
- `CHANGELOG.md` exists when user/operator-visible changes or versioning matter.

## Frontmatter

- Maintained Markdown files have `role`, `contains`, `not-contains`, `write-when`.
- Frontmatter matches actual content.
- Frontmatter is compact and not used for volatile details.

## Routing

- No active backlog in `README.md` or `MEMORY.md`.
- No completed task diary in `TODO.md` or `MEMORY.md`.
- No agent rules in `README.md` or `MEMORY.md`.
- No setup instructions hidden only in `AGENTS.md`.
- No durable decisions outside the repo's chosen ADR location.

## Agent usability

- Bootstrap/read order is explicit.
- Stop-and-ask conditions are explicit.
- Verification expectations are explicit.
- Secrets handling is explicit.
- Dirty-worktree/user-change protection is explicit.

## Maintenance cost

- Extra docs are justified by reuse and clear update triggers.
- Templates/placeholders are filled where facts are known.
- References point to files that exist.
- The repo does not require reading a large policy corpus for normal tasks.
