---
name: orchestrator
description: Pure Orchestrator Mode in Codex invoked via /orchestrator or $orchestrator. The Codex session strictly acts as planner, DAG dispatcher, cold-eyes reviewer, and integrator across guarded agy_worker.py waves without editing business code directly.
---

# Orchestrator Mode (Codex)

Use this workflow when the user invokes `/orchestrator`, selects `$orchestrator`, or requests pure Orchestrator Mode. Follow [the shared orchestrator workflow](workflow.md) and [the shared coding workflow](auto-workflow.md); honor [routing](routing.json) (`swarm` preferences and `native_roles`) plus the shared catalog in [headless.json](headless.json).

## Strict Host Boundaries
- **Zero business-code edits in Codex**: Preserve existing WIP and delegate implementation and test slices (even bounded `filler`/`L1` edits) through guarded `agy_worker.py run --platform codex` sandboxes rather than editing application files directly, unless handling `agy_guard.py`-protected control files (`.git`, `.agents`, `.codex`, `AGENTS.md`, guard/sandbox files), live SSH/ops, non-git tasks, or an explicit user override.
- **Wave 0 Recon & Routing**: Use read-only Codex subagents or direct inspection for Wave 0 recon. Read `swarm` in [routing](routing.json) (`implementer.model` = `gemini-pro-orchestrator-neon`, `secondary_implementer` = `claude-sonnet-5-5-high`, `filler` = `gpt-oss-120b-medium`) alongside `agy_routes` in [headless.json](headless.json), confirming live availability via `agy models` when needed. Native Codex subagents do not inherit `agy_guard.py` or macOS sandboxing.
- **Authorization & Evidence**: Keep code review, full patch inspection, `verify --full`, and integration in the current Codex session (`swarm.reviewer: current` or explicit cross-family `review`). Any external prepaid API calls (`api_advisors` or `--executor api`) require prior explicit spending authorization.
- **Temporary Path Discipline**: Use run-specific temporary paths in `/tmp/orch-*`, verify paths before writing/deleting, and remove only the paths created for the run after the final ledger is complete.

## Commands
- **Optional Read-Only Multi-Model Consult**:
  ```bash
  R="$HOME/.agents/skills/orchestrator/moa_runner.py"
  python3 "$R" --platform codex --raw --models agy,grok -- '<architecture question>'
  ```
- **Concurrent Wave Dispatch, Verification & Apply**:
  ```bash
  W="$HOME/.agents/skills/orchestrator/agy_worker.py"
  python3 "$W" run --repo '<git-root>' --brief '/tmp/orch-<wave>-<slug>-brief.md' \
    --model '<chosen-model>' --platform codex \
    --coordinator-model '<actual-model-or-current>' --name '<slug>'
  python3 "$W" verify '<run-id>' --full -- <project checks>
  python3 "$W" apply '<run-id>' --sha '<reviewed-patch-sha256>'
  python3 "$W" record '<run-id>' --level <filler|L1|L2|L3> --outcome accepted --notes '<summary>'
  python3 "$W" clean '<run-id>'
  ```
  - Because `agy_worker.py run --base HEAD` clones committed `HEAD`, integrate upstream Wave `k` work onto the base commit before dispatching dependent Wave `k+1` slices.

End with the Wave Execution Ledger, checks completed, residual risks, and **模型调用说明** (naming actual models/channels without inferring from defaults).
