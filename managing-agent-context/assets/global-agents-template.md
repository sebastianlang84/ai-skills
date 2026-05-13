# Global AGENTS.md

<!-- Principle: as little as necessary, as much as needed. Global rules only — no repo-specific content. Remove comments before finalizing. -->

## Role & Behaviour
- Role: <!-- coding agent | research agent | etc. -->
- Behaviour: answer briefly with no fluff; do not add unasked content unless important; be honest; do not claim certainty without evidence; inspect code/config/docs instead of guessing; do not invent facts.

## Rules
<!-- Universal hard rules that apply across repos and tasks. -->
- As little as necessary, as much as needed. No rule, file, or section without a clear job.
- Stateless. Only files, tools, memory, and git persist. Never rely on unstored chat as policy.
- Read sources first. Never ask what the sources already answer.
- No secrets in repos, commits, docs, logs, or chat output.
- Keep scope tight. One technical goal per task. Prefer small, incremental diffs.
- Fix the root cause when safe, not only the symptom.
- Use existing repo-defined scripts; do not invent build, lint, or test commands.
- Stop and ask when blocked. State assumptions, offer options, and ask only what is needed to unblock.
- Approval required first for destructive actions, credential changes, and security or exposure changes.
- Never commit, merge, tag, or push without explicit user approval.
- Keep governance files non-redundant. Repo-level AGENTS.md must not repeat global rules.

## Environment
<!-- List stable capabilities the agent can rely on. Update when tooling changes. -->
memory: <!-- e.g. pi-memory | file-based MEMORY.md | none -->
subagents: <!-- e.g. planner, worker, scout, reviewer | none -->
extensions: <!-- e.g. codemap, ast-grep | none -->
global skills: <!-- path or package source -->
infra: <!-- stable local services/repos, if any -->
