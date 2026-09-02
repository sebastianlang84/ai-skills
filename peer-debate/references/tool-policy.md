# Tool policy

Both debaters run through their cli — `agy` or `codex` — with its full configured tool surface. A
codex side gets `--dangerously-bypass-approvals-and-sandbox` and `features.hooks=false` (see
SKILL.md, Tool policy). The driver passes
`--dangerously-skip-permissions` because headless mode otherwise soft-denies any command, web or MCP
tool that would require an interactive answer. It does not pass `--sandbox`.

This is deliberate for the private experiment host: the debaters should be able to calculate,
write scripts, inspect local sources, browse, and call configured MCP servers without an approval
interrupt changing the debate. The role prompts remain the behavioral boundary: artifacts belong
under the side's named `A/` or `B/` directory, and neither side should mutate unrelated state.

`agy` does not expose a per-invocation tool allowlist. The effective surface therefore changes when
Agys global tools, agents, browser access or MCP configuration changes. `debate.py check` verifies
the executable and model, not every remote tool or its credentials.

Each turn adds the side's directory with `--add-dir` and names all paths absolutely. This is
required: without it Agys file tools write relative paths into its own scratch/brain directory
rather than the debate record.
