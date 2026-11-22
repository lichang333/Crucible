---
name: auto
description: Delegate bounded coding tasks from OpenCode to isolated Google AI Ultra (agy) workers under macOS sandbox and guard enforcement (automatically in Build/Swarm or when invoking /auto). OpenCode plans, auto-selects models from the shared agy catalog, reviews cross-family, verifies in sandbox, and applies reviewed patches. Excludes Q&A synthesis and production/SSH/deployment tasks.
---

# Delegated coding in OpenCode (`/auto`)

Read [the shared coding workflow](workflow.md) for every coding task, including L0. OpenCode owns triage, briefing, automatic model selection, cross-family cold-eyes review, sandbox verification, and integration; [routing](routing.json) and [headless.json](headless.json) supply the shared Google AI Ultra (`agy`) catalog.

## Automatic Coordinator Model Selection & Cost-Saving Routing
Follow `auto_funding` (`included_subscription` first) and **select models automatically without asking the user** (honor explicit user overrides when given). Inspect the active catalog anytime with `python3 "$HOME/.config/opencode/skills/auto/agy_worker.py" models`:
- **L0** (1–2 small edits, live operations, SSH/deploy, guard/sandbox changes): handle directly in OpenCode.
- **Filler** (mock data, comments, copy, boilerplate): `gemini-4-argon-low` (`agy_routes.filler`; or bridged `grok` / `deepseek-v4.1` for text) to reserve `Neon`, `Carbon`, `Hydrogen`, and `GPT-6-Luna` quota for core logic & review.
- **Fast L1 / mechanical edits**: `gemini-4-carbon-high` / `gemini-4-argon-high` or `gemini-4-carbon-medium`.
- **Standard L2 implementation/bugfix**: `gemini-4-neon-high` (fallback `gemini-4-carbon-high` or `claude-sonnet-5-5-high`).
- **Deep algorithmic / cross-file synthesis**: `gemini-4-neon-xhigh` or `gemini-4-hydrogen-xhigh`.
- **L3 architecture / tricky diagnosis**: `gemini-pro-orchestrator-neon` (`Orchestrator (Neon)`), `gemini-pro-orchestrator` (`Orchestrator (Carbon)`), or `claude-opus-5-5-high` (or split into bounded L1/L2 slices).
- **Cold-eyes review (`review --executor auto`)**: always choose a **different family** from the slice author (`claude-opus-5-5-high` / `claude-sonnet-5-5-high` to review Gemini 4; `gemini-pro-orchestrator-neon` to review Claude; `--executor auto` fails over across `$0` subscription pools first — `agy` pools -> ChatGPT `codex` `gpt-6-luna-high` -> signed-in OpenCode xAI OAuth `grok` — and only proceeds to prepaid API fallback (`deepseek` / `deepseek-flash` / `glm` / `kimi` / `minimax`) when prepaid APIs are explicitly authorized; pass `--executor agy` or `--executor codex` to stay strictly `$0` subscription-only and prevent reaching prepaid APIs).
- **Cross-pool failover (`429` / quota)**: automatically switch between the **Gemini 4 / Orchestrator** pool and the **Claude 5.5 / GPT-OSS 120B** (`gpt-oss-120b-medium`) pool while preserving partial patches. Never silently fall back to prepaid APIs without explicit authorization.

See the [shared model catalog](headless.json) for exact IDs. Run `agy models` to check current availability.

UI display names and shorthands (e.g. `"Claude Opus 5.5"`, `"Gemini 4 Hydrogen (XHigh)"`, `"Orchestrator (Argon)"`) are automatically resolved by `agy_worker.py`.

## Run, review, verify, and apply
Write a self-contained brief (`GOAL`, `CONTEXT`, `REQUIREMENTS`, `CONSTRAINTS`, `ACCEPTANCE`, `OUT OF SCOPE`) to an ignored file or temp path and launch `agy_worker.py`:

```bash
W="$HOME/.config/opencode/skills/auto/agy_worker.py"
python3 "$W" run --repo "$PWD" --brief '<brief.md>' --model '<chosen-agy-model>' \
  --platform opencode --coordinator-model '<actual-model-or-current>' \
  --task-id '<task-id>' --name '<slug>'
```

1. **Inspect patch & flags**: read `diff.patch` completely and check `REVIEW_FLAGS` (`protected_paths` including `.opencode`, `sensitive_paths`, `execution_surface`, `INCOMPLETE_RUN`).
2. **Cold-eyes review (subscription channels first; requires `--executor agy` or `--executor codex` to guarantee `$0` API spend)**: run cross-family review using `--executor auto` (`--model claude-opus-5-5-high` for Gemini authors, or `gemini-pro-orchestrator-neon` for Claude authors; fails over across `$0` subscription pools first — `agy` pools -> ChatGPT `codex` `gpt-6-luna-high` -> signed-in OpenCode xAI OAuth `grok` — before prepaid API `deepseek` / `deepseek-flash` / `glm` / `kimi` / `minimax`, which require prior spending authorization; pass `--executor agy` or `--executor codex` to stay strictly `$0` subscription-only):
   ```bash
   python3 "$W" review '<run-id>' --executor auto --model '<cross-family-reviewer>' --json
   ```
3. **Revise if needed** (max 2 rounds):
   ```bash
   python3 "$W" resume '<run-id>' --brief '<feedback.md>'
   ```
4. **Verify in fresh macOS sandbox & apply reviewed SHA**:
   ```bash
   python3 "$W" verify '<run-id>' --full -- <project-test-command>
   python3 "$W" apply '<run-id>' --sha '<reviewed-sha256>'
   python3 "$W" record '<run-id>' --level L2 --outcome accepted --notes '<summary>'  # --level accepts filler|L1|L2|L3
   python3 "$W" clean '<run-id>'
   ```

For explicit Claude local/cloud routing, see [claude-local-workflow.md](claude-local-workflow.md) and [cloud-workflow.md](cloud-workflow.md). End every `/auto` reply with the shared workflow's **模型调用说明**.
