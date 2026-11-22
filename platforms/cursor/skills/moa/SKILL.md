---
name: moa
description: Run multi-model Q&A, architecture trade-offs, and evidence-based analysis when the user invokes /moa or asks architecture/design/trade-off questions in Cursor. Collects Orchestrator (Neon) via Google AI Ultra (agy CLI, $0 marginal API cost) plus configured API workers, adds Cursor's web-grounded vote, and synthesizes one verified answer. For delegated coding, use auto or swarm instead.
---

# Mixture of Agents (MoA) in Cursor

The current Cursor session is the coordinator and final synthesizer. Read [the shared workflow](workflow.md) for evidence rules and run records. [Routing](routing.json) contains the Cursor profile and inherits shared defaults from [headless.json](headless.json).

## Why this lineup saves Cursor credits and cost
- **Host (Cursor)**: Anchor vote with live codebase tools and web search, plus final synthesis (avoids extra host agent loops or a paid API aggregator call).
- **Default Workers (from `routing.json`)**:
  - `agy` (`Orchestrator (Neon)` / `gemini-pro-orchestrator-neon`), `codex` (`GPT-6-Luna (High)`), & `grok` (`Grok-4.7`): subscription-backed (**\$0 marginal API cost**).
  - `glm` (`GLM-5.3`), `deepseek` (`DeepSeek-V4-Pro`, plus `deepseek-v4.1` / `deepseek-flash` for `DeepSeek-V4.1-Flash` & `deepseek-max` effort), `kimi` (`Kimi-K3.1-Pro` + `kimi-highspeed` / `kimi-max` when `MOONSHOT_API_KEY` or `KIMI_API_KEY` is set), & `minimax` (`MiniMax-M3`): independent non-Google model families via prepaid APIs when multi-family API diversity is needed.
- **Zero-API-cost single consult**: pass `--models agy` (or `--models agy,codex,grok`) when you only want opinions without spending prepaid API tokens.
- **3-Tier Automatic Failover**:
  - **Tier 1 (`agy` dual pools)** & **Tier 2 (`agy` unsubscribed/uninstalled/exhausted)**: `agy_worker.py review --executor auto` fails over across Gemini 4 / Orchestrator and Claude 5.5 / `gpt-oss-120b-medium`, then ChatGPT `codex` (`gpt-6-luna-high`) / `grok`, then `--executor api`; coding downgrades to the Cursor native host or scoped subagents (`zhipu/glm-5.3`, `deepseek/deepseek-v4-pro`, `minimax/MiniMax-M3`, `xai/grok-4.5`, or `opencode/*-free`).
  - **Tier 3 (prepaid API balance/token exhausted or key expired)**: `moa_runner.py` (`--review` & `aggregate`) and `agy_worker.py review --executor api` automatically fail over across remaining keyed providers (`deepseek` -> `deepseek-flash` -> `glm` -> `kimi` -> `minimax`).

## Operating steps
1. Verify the user supplied a prompt (if not, ask directly or use Cursor's question tool). Strip workflow-only flags (`--deep`, `--fast`, `--no-deep`) before passing the prompt to the script.
2. Run the shared runner in raw mode:
   ```bash
   python3 "$HOME/.cursor/skills/moa/moa_runner.py" --platform cursor --raw \
     --coordinator-model '<actual-model-or-current>' --task-id '<task-id>' -- '<question>'
   ```
   Inspect `routing.json` or run `--show-config` without calling models. Parse worker answers between `===MOA_RAW_JSON_START===` and `===MOA_RAW_JSON_END===`.
3. **Web-ground current facts**: external workers have no live web access here. Use Cursor's web search when the prompt depends on recent releases, docs, prices, or current events.
4. **Add the host's grounded vote and synthesize**: compare worker answers against verified sources and local files, resolve disagreements using evidence rather than majority vote, and preserve material uncertainty or worker failures.
5. **Optional deep cross-review (`--deep`)**: for genuinely complex or high-stakes tasks (or when workers materially disagree), run `--review` to critique the host draft with `Orchestrator (Neon)` via Google AI Ultra (**\$0 API cost**):
   ```bash
   python3 "$HOME/.cursor/skills/moa/moa_runner.py" --platform cursor --review \
     -- 'Original prompt and draft to critique...'
   ```
   Incorporate or explicitly refute each point from `===MOA_REVIEW_START===` ... `===MOA_REVIEW_END===` in the final response.
