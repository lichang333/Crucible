---
name: moa
description: Run multi-model Q&A or analysis when the user invokes /moa or requests Mixture of Agents synthesis in OpenCode. Collects Orchestrator (Neon) via Google AI Ultra (agy CLI, $0 API cost) plus DeepSeek-V4-Pro and MiniMax-M3, adds the host's web-grounded vote, and synthesizes one verified answer. For delegated coding, use auto or swarm instead.
---

# Mixture of Agents (MoA) in OpenCode

The current OpenCode session (`zhipu/glm-5.3`, `deepseek/deepseek-v4-pro`, `minimax/MiniMax-M3`, `xai/grok-4.5`, `opencode/*-free`, or active host) is the coordinator and final synthesizer. Read [the shared workflow](workflow.md) for evidence rules and run records. [Routing](routing.json) contains the OpenCode profile and inherits shared defaults from [headless.json](headless.json).

## Why this lineup saves tokens and cost
- **Host (OpenCode `glm-5.3` or active host)**: Anchor vote with live codebase tools and web search, plus final synthesis (avoids a paid API aggregator call).
- **Default Workers (`agy`, `deepseek`, `minimax`)**:
  - `agy` (`Orchestrator (Neon)` / `gemini-pro-orchestrator-neon`): runs read-only via local `agy --mode plan` on your **Google AI Ultra subscription (\$0 marginal API cost)**.
  - `deepseek` (`DeepSeek-V4-Pro`) & `minimax` (`MiniMax-M3`): independent non-GLM model families via prepaid APIs.
  - `glm` worker is intentionally omitted from `worker_defaults` in `routing.json` to avoid a redundant same-family GLM API call; additional bridged or keyed providers (`--models codex,grok,deepseek-v4.1,kimi,kimi-highspeed`, plus `-low`/`-high`/`-max` effort selectors on `codex`, `deepseek`, and `kimi`) remain available on demand.
- **Zero-API-cost single consult**: pass `--models agy` when you only want a second opinion from `Orchestrator (Neon)` without spending prepaid API tokens.
- **3-Tier Automatic Failover**:
  - **Tier 1 (`agy` dual pools)** & **Tier 2 (`agy` unsubscribed/uninstalled/exhausted)**: `agy_worker.py review --executor auto` tries the `agy` model pools, then signed-in Codex and OpenCode xAI OAuth before authorized prepaid APIs. Coding can continue with the OpenCode host or scoped subagents (`zhipu/glm-5.3`, `deepseek/deepseek-v4-pro`, `minimax/MiniMax-M3`, `xai/grok-4.5`, or `opencode/*-free`).
  - **Tier 3 (prepaid API balance/token exhausted or key expired)**: `moa_runner.py` (`--review` & `aggregate`) and `agy_worker.py review --executor api` can use the remaining authorized API providers (`deepseek`, `deepseek-flash`, `glm`, `kimi`, `minimax`). In the OpenCode TUI, switch to another healthy provider or `opencode/glm-5.3-flash-free`.

## Operating steps
1. Verify the user supplied a prompt (if not, ask via `question` or plain reply). Strip workflow-only flags (`--deep`, `--fast`, `--no-deep`) before passing the prompt to the script.
2. Run the shared runner in raw mode:
   ```bash
   python3 "$HOME/.config/opencode/skills/moa/moa_runner.py" --platform opencode --raw \
     --coordinator-model '<actual-model-or-current>' --task-id '<task-id>' -- '<question>'
   ```
   Inspect `routing.json` or run `--show-config` without calling models. Parse worker answers between `===MOA_RAW_JSON_START===` and `===MOA_RAW_JSON_END===`.
3. **Web-ground current facts**: external workers have no live web access here. Use OpenCode's `websearch` and `webfetch` when the prompt depends on recent releases, docs, prices, or current events.
4. **Add the host's grounded vote and synthesize**: compare worker answers against verified sources and local files, resolve disagreements using evidence rather than majority vote, and preserve material uncertainty or worker failures.
5. **Optional deep cross-review (`--deep`)**: for genuinely complex or high-stakes tasks (or when workers materially disagree), run `--review` to critique the host draft with `Orchestrator (Neon)` via Google AI Ultra (**\$0 API cost**):
   ```bash
   python3 "$HOME/.config/opencode/skills/moa/moa_runner.py" --platform opencode --review \
     -- 'Original prompt and draft to critique...'
   ```
   Incorporate or explicitly refute each point from `===MOA_REVIEW_START===` ... `===MOA_REVIEW_END===` in the final response. Never pass `--glm52` when the host is GLM.
