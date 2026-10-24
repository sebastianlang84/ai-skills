# Sources behind the mental model

Read 2026-10-24; checked again by Fable 5.1 and gpt-6-astra reviews the same day. Paraphrased; check the source before quoting a number. Vendor docs change often.

## What the sources support

| Claim in `SKILL.md` | Evidence | Limits |
| --- | --- | --- |
| Quality drops as irrelevant content grows | Chroma, Context Rot: 18 models degrade with input length in controlled tasks; on LongMemEval a focused ~300-token prompt beat the full ~113k-token one | The LongMemEval comparison also removes the retrieval step, so it is not a pure length test; Degradation is gradual, not a cliff (Anthropic) |
| Smallest high-signal set, not shortest text | Anthropic, Effective context engineering | Minimal does not mean short; vague rules fail |
| Near-miss distractors hurt more than noise | Chroma (one related distractor already lowers accuracy); Breunig, "context confusion" | |
| Unresolved contradictions fail unpredictably | Claude Code memory docs: conflicting instruction files may be resolved arbitrarily | Deliberate repo overrides and harness-defined precedence (Codex: closer files later) are not contradictions |
| Early wrong assumptions persist | Breunig, "context clash", citing Laban et al. (arXiv 2505.06120): 39 % average loss when an underspecified task is spread over turns | Measures multi-turn anchoring, not conflicting instruction layers |
| Position does not establish authority | Claude Code docs: load order is not priority; CLAUDE.md arrives as a user message after the system prompt | Claude-specific |
| Position effects depend on model and task | Lost in the Middle (Liu et al., 2023): U-shaped curve on older models; Chroma: no notable variation across 11 needle positions on its needle task, but an early-position advantage in its repeated-words task; Anthropic prompting guidance: long documents before the query | Test placement for large inputs instead of assuming either way |
| Restate goals instead of relying on placement | Manus rewrites `todo.md` so goals sit at the end of context | One vendor's practice, no controlled study |
| Always-loaded files: short, non-derivable, under 200 lines, imports cost the same | Claude Code best practices and memory docs | Claude-specific numbers; Codex caps at 32 KiB instead (see `harness-loading.md`) |
| Persist must-survive constraints through the harness's mechanism | Claude Code memory docs and glossary: the project-root CLAUDE.md is reloaded after compaction; conversation-only instructions may be lost | Claude-specific; Codex not verified. You can also tell `/compact` what to keep |
| No volatile values in stable prefixes | Manus: cache hit rate as the key cost metric, append-only context, no timestamp at the start | Applying it to instruction files is an inference |
| Emphasis is scarce | Claude Code best practices | Single source |
| Progressive disclosure for skills | Anthropic, Agent Skills (metadata, then SKILL.md, then linked files) | Runtime exploration is slower than preloading |
| Few, distinct, compact tools | Anthropic (no overlap; if a human cannot pick, neither can the agent); Breunig (selection failures beyond roughly 30 tools, tool RAG up to 3x better); Claude Code (CLIs are the most context-efficient) | The 30-tool and 3x figures come from the RAG-MCP paper on DeepSeek-v3 (cited in Breunig's second post), the 46 vs. 19 tool figure from a quantized Llama 3.1 8B: indicative, not universal. Filter or paginate tool output; Claude Code's default limit for MCP output is 25,000 tokens (configurable), and larger text results are saved to a file the agent can read back. Deferred tool loading keeps unused definitions out of context (Anthropic, advanced tool use). Manus masks tools rather than removing them mid-task, to keep the cache |
| Verify before writing memory | Breunig, "context poisoning": a recorded hallucination keeps being referenced; LangChain: memory retrieval can surface unrelated facts | |
| Add corrective rules for observed failures; test the effect | Anthropic (start minimal, add for observed failure modes); Claude Code (treat CLAUDE.md like code, test whether behavior changes) | Does not apply to explicit user requirements and stop conditions, which belong in from the start |
| Full rewrites collapse context | ACE (arXiv 2510.04618): one rewrite shrank 18,282 tokens to 122 and dropped accuracy below the no-adaptation baseline; prefers itemized entries with small delta merges | ACE favors growing, detailed playbooks and also tests them in system prompts; keeping them out of the always-loaded layer is this skill's inference |
| Enforce in hooks, not prose | Claude Code: CLAUDE.md is advisory, hooks are deterministic; use PreToolUse hooks or permission deny rules to block actions. Codex hooks: `PreToolUse` deny | Only for mechanically decidable rules; Codex `PreToolUse` misses hosted tools and `write_stdin` |
| Scoped rules, compaction, subagent loading | Claude Code context-window and sub-agents docs (see `harness-loading.md`) | Claude-specific; Codex `SessionStart(compact)` hook documented, `AGENTS.md` reload after compaction not documented |
| Test context changes on representative tasks | OpenAI, skill evals; Claude Code best practices | |

## Not covered in `SKILL.md`

- Few-shot drift: agents copy repetitive patterns in their own history; vary examples (Manus). Prefer a few diverse canonical examples over long rule lists (Anthropic).
- Keeping errors in context helps recovery (Manus), but after repeated failed corrections a fresh session with a better prompt beats accumulating wrong turns (Claude Code).
- Skills with scripts or network access are a security surface; audit them (Anthropic, Agent Skills).

## Links

- Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, Claude prompting best practices (long-context placement): https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic, Advanced tool use (deferred tool loading): https://www.anthropic.com/engineering/advanced-tool-use
- Claude Code glossary, compaction: https://code.claude.com/docs/en/glossary#compaction
- Laban et al., LLMs Get Lost in Multi-Turn Conversation: https://arxiv.org/abs/2505.06120
- Anthropic, Writing tools for agents: https://www.anthropic.com/engineering/writing-tools-for-agents
- Claude Code context window (what survives compaction): https://code.claude.com/docs/en/context-window
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Codex hooks: https://learn.chatgpt.com/docs/hooks
- Codex AGENTS.md discovery: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- OpenAI, Testing agent skills systematically with evals: https://developers.openai.com/blog/eval-skills
- RAG-MCP (tool selection at scale): cited via Breunig, How to Fix Your Context; not read directly
- Anthropic, Equipping agents with Agent Skills: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- Claude Code memory: https://code.claude.com/docs/en/memory
- Manus, Context Engineering for AI Agents: https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- Chroma, Context Rot: https://www.trychroma.com/research/context-rot
- LangChain, Context Engineering for Agents: https://www.langchain.com/blog/context-engineering-for-agents
- Breunig, How Long Contexts Fail: https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html
- Breunig, How to Fix Your Context: https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html
- Zhang et al., Agentic Context Engineering: https://arxiv.org/abs/2510.04618
- Liu et al., Lost in the Middle (abstract only): https://arxiv.org/abs/2307.03172
- Mei et al., A Survey of Context Engineering (abstract only): https://arxiv.org/abs/2507.13334
