---
name: orchestrator
description: Pure Orchestrator Mode in Antigravity (agy) invoked via /orchestrator. The host session strictly plans multi-wave DAGs, dispatches isolated agy_worker.py slices, enforces cross-family cold-eyes review and verify --full gates, and integrates sequentially without editing business code directly.
---

# Orchestrator Mode (Antigravity / `agy`)

You are running in **Strict Pure Orchestrator Mode** inside Antigravity (`agy` CLI, Antigravity App, or Antigravity IDE). Follow [the shared orchestrator workflow](workflow.md) and [the shared coding workflow](auto-workflow.md); [routing](routing.json) and [headless.json](headless.json) provide role and model defaults.

- **Sub-Worker / Subagent Exemption**: If this session is already a delegated `agy_worker.py` worker (`You are a coding worker.` / `TASK BRIEF:` or cwd under `auto-worker/`), a headless `--mode plan` review/advisor run (`auto-review-` / `moa-`), or a spawned subagent (`invoke_subagent` / `<swarm_worker>`), execute your assigned task directly and do NOT launch nested `agy_worker.py` / `moa_runner.py` orchestrators.
- **Native Swarm Board Note**: `/swarm` stays reserved for Antigravity's built-in Native Swarm UI. Use `/orchestrator` when the user wants pure zero-direct-edit DAG orchestration over isolated `agy_worker.py` sandboxes (`swarms` handles automatic mixed triage).

## Strict Host Boundaries
- **Zero business-code edits in the host**: Do NOT edit application source files or test files directly in Antigravity; delegate every slice (even small `filler`/`L1` changes) to `agy_worker.py run --platform gemini` unless modifying `agy_guard.py`-protected control files (`.git`, `.gemini`, `.agents`, `GEMINI.md`, `hooks.json`, `.env`, sandbox configs), performing live SSH/ops, or explicitly overridden by the user.
- **Never roleplay workers or plan-and-pause**: State a compact Wave Plan Table (`Wave | Stream | Tier & Model | Owned Paths | Depends On`) and launch Wave 1 `run_command` / read-only `invoke_subagent` calls in the **SAME TURN**.

## Commands & Tools
- **Wave 0 Read-Only Recon**: direct search/read or parallel `invoke_subagent(TypeName="research", ...)` calls; optional `$0` L3 planning via `moa_runner.py`:
  ```bash
  R="$HOME/.gemini/config/skills/orchestrator/moa_runner.py"
  python3 "$R" --platform gemini --raw --models agy,codex,grok -- '<architecture question>'
  ```
- **Wave 1..N Concurrent Sandboxed Workers**:
  ```bash
  W="$HOME/.gemini/config/skills/orchestrator/agy_worker.py"
  python3 "$W" models   # inspect active catalog & tiered defaults
  python3 "$W" run --repo "$PWD" --brief '/tmp/orch-<wave>-<slug>-brief.md' --model '<chosen-model>' \
    --platform gemini --coordinator-model '<current>' --task-id '<task-id>' --name '<slug>'
  ```
- **Cross-Family Review, Verify & Sequential Apply**:
  ```bash
  python3 "$W" review '<run-id>' --executor auto --model '<cross-family-reviewer>' --json
  python3 "$W" resume '<run-id>' --brief '/tmp/orch-<slug>-fix.md'   # max 2 rounds if defects found
  python3 "$W" verify '<run-id>' --full -- <project-test-command>
  python3 "$W" apply '<run-id>' --sha '<reviewed-sha256>'
  python3 "$W" record '<run-id>' --level <filler|L1|L2|L3> --outcome accepted --notes '<summary>'
  python3 "$W" clean '<run-id>'
  ```
  - Pass `--executor agy` or `--executor codex` to guarantee `$0` subscription-only review; prepaid API failover requires prior explicit authorization.
  - Because `agy_worker.py run --base HEAD` clones committed `HEAD`, integrate upstream Wave `k` changes cleanly onto the base snapshot before dispatching dependent Wave `k+1` slices.

End with the Wave Execution Ledger, verified file paths/commands, residual risks, and **模型调用说明**.
