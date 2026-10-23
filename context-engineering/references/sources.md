# Sources behind the mental model

Read 2026-10-24. Paraphrased; check the source before quoting a number. Vendor docs change often.

## What the sources support

| Claim in `SKILL.md` | Evidence | Limits |
| --- | --- | --- |
| Quality drops with length, even at equal task difficulty | Chroma, Context Rot: 18 models; a focused ~300-token prompt beat the full ~113k-token one | Degradation is gradual, not a cliff (Anthropic) |
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
| Few, distinct, compact tools | Anthropic (no overlap; if a human cannot pick, neither can the agent); Breunig (selection failures beyond roughly 30 tools, tool RAG up to 3x better); Claude Code (CLIs are the most context-efficient) | Breunig's thresholds come from older, smaller models: indicative only. Deferred tool loading keeps unused definitions out of context (Anthropic, advanced tool use). Manus masks tools rather than removing them mid-task, to keep the cache |
| Verify before writing memory | Breunig, "context poisoning": a recorded hallucination keeps being referenced; LangChain: memory retrieval can surface unrelated facts | |
| Add corrective rules for observed failures; test the effect | Anthropic (start minimal, add for observed failure modes); Claude Code (treat CLAUDE.md like code, test whether behavior changes) | Does not apply to explicit user requirements and stop conditions, which belong in from the start |
| Full rewrites collapse context | ACE (arXiv 2510.04618): one rewrite shrank 18,282 tokens to 122 and dropped accuracy below the no-adaptation baseline; prefers itemized entries with small delta merges | ACE favors growing, detailed playbooks; this fits retrievable stores, not the always-loaded layer |
| Enforce in hooks, not prose | Claude Code: CLAUDE.md is advisory, hooks are deterministic; use PreToolUse hooks or permission deny rules to block actions | |

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
