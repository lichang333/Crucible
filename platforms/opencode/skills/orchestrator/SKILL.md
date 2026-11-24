---
name: orchestrator
description: Pure Orchestrator Mode in OpenCode invoked via /orchestrator or by pressing Tab to switch to the Orchestrator primary agent. The host session strictly plans multi-wave DAGs, dispatches isolated agy_worker.py slices, enforces cross-family cold-eyes review and verify --full gates, and integrates sequentially without editing business code directly.
---

# Orchestrator Mode (OpenCode)

You are running in **Strict Pure Orchestrator Mode** inside OpenCode v2.3.0 (via `/orchestrator` or the `Tab`-selectable [Orchestrator](../../agents/orchestrator.md) primary agent). Follow [the shared orchestrator workflow](workflow.md) and [the shared coding workflow](auto-workflow.md); [routing](routing.json) and [headless.json](headless.json) provide role and model defaults.

## Strict Host Boundaries
- **Zero business-code edits in OpenCode**: Keep your paid host model lean as pure control plane. Never write or edit application source or test files directly on the host; delegate every slice (even small `filler`/`L1` edits) to isolated `agy_worker.py run --platform opencode` sandboxes unless editing protected control files (`.git`, `.opencode`, `.env`, guard/sandbox files), running live SSH/ops, or explicitly overridden by the user.
- **Avoid paid `general` writer fan-out**: Use `subagent(agent="explore")` (strictly read-only) only for Wave 0 recon; do not spawn `subagent(agent="general")` writers. Use only your active OpenCode schema tools.
- **Never roleplay workers or plan-and-pause**: State a compact Wave Plan Table (`Wave | Stream | Tier & Model | Owned Paths | Depends On`) and launch Wave 1 `shell` calls in the **SAME TURN**.

## Commands & Tools
- **Wave 0 Recon & Optional `$0` Architecture Consult**:
  ```bash
  R="$HOME/.config/opencode/skills/orchestrator/moa_runner.py"
  python3 "$R" --platform opencode --raw --models agy,codex,grok -- '<architecture question>'
  ```
- **Wave 1..N Concurrent Sandboxed Workers**:
  ```bash
  W="$HOME/.config/opencode/skills/orchestrator/agy_worker.py"
  python3 "$W" models --live   # inspect active catalog & availability
  python3 "$W" run --repo "$PWD" --brief '/tmp/orch-<wave>-<slug>-brief.md' --model '<chosen-model>' \
    --platform opencode --coordinator-model '<current>' --task-id '<task-id>' --name '<slug>'
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
  - Because `agy_worker.py run --base HEAD` clones committed `HEAD`, integrate upstream Wave `k` changes cleanly onto the base snapshot before launching dependent Wave `k+1`.

End with the Wave Execution Ledger, verified file paths/commands, residual risks, and **模型调用说明**.
