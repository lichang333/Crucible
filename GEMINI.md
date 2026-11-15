# Antigravity / Gemini entry

Read [the shared project conventions](shared/project-conventions.md) when working in this repository.

Antigravity / Gemini entrypoints live in `platforms/gemini/skills/` (`moa`, `auto`, `swarm`)
and `platforms/gemini/rules/swarm-coordinator.md` (aliased via `platforms/agy/`); OpenCode entrypoints live in `platforms/opencode/skills/` and
`platforms/opencode/agents/swarm.md`; Cursor entrypoints live in `platforms/cursor/skills/`,
`platforms/cursor/agents/swarm-coordinator.md`, and `platforms/cursor/rules/swarm-coordinator.mdc`;
Claude entrypoints live in `platforms/claude/skills/`; Codex entrypoints live in
`platforms/codex/skills/`. Shared Python and sandbox code stays in `skills/`.
Edit the shared source rather than copying implementations into platform folders.

For multi-agent work, the current Antigravity session owns dispatch, subagents and integration.
Consult `config/gemini.json` and `config/headless.json` (`agy_catalog`: 8 active families / 19 variants,
excluding retired `gemini-3.8`) for role choices. For `/swarm` and `/auto`, unless the user explicitly
pins a model, the Coordinator automatically selects task-fit models per worker and cross-family reviewers
(pairing Gemini 4 / Orchestrator with Claude Opus/Sonnet 5.5 or GPT-OSS 120B) and switches quota/RPM
buckets automatically on `429` or quota exhaustion without asking the user to pick models. Antigravity
`/swarm`, `/moa`, and `/auto` sessions can also invoke external/bridged advisors and cross-family reviewers
— **`grok` (`Grok-4.7` via signed-in OpenCode xAI OAuth subscription at `$0` API spend, or `XAI_API_KEY`)**,
**`glm` (`GLM-5.3`)**, **`deepseek` (`DeepSeek-V4-Pro`)**, and **`minimax` (`MiniMax-M3`)** — via
`skills/moa/moa_runner.py` (`--platform gemini`) and `agy_worker.py review --executor auto|api`
(especially when the Claude/GPT-OSS quota pool runs low). Read-only
investigations can run in parallel using native Antigravity subagents. Delegated `/auto` code execution uses an isolated agy worker
via `agy_worker.py`, the native Claude broker in `shared/claude-local-workflow.md`, or the Claude
cloud bridge. Cloud results return through local sandbox verification and reviewed-patch apply;
cloud execution does not inherit agy's guard. See `shared/cloud-workflow.md` for cloud
funding and transport limits.
