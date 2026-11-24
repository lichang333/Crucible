---
name: orchestrator
description: Pure Orchestrator Mode in Claude Code invoked via /orchestrator. The Claude session strictly plans multi-wave DAGs, dispatches isolated coding workers (agy_worker.py, authorized claude_local.py, or claude_cloud.py), enforces cross-family review and verify --full gates, and integrates sequentially without editing business code directly.
---

# Orchestrator Mode (Claude Code)

Claude in the current session strictly operates as **Pure Orchestrator**: owning recon, DAG wave decomposition, worker dispatch, independent cross-family review, sandbox verification, sequential `apply --sha`, and final integration without directly writing application code. Follow [the shared orchestrator workflow](workflow.md), [the shared coding workflow](auto-workflow.md), [routing](routing.json), and [headless.json](headless.json).

## Strict Host Boundaries
- **Zero business-code edits in Claude Code**: Delegate every application source/test slice (even `filler`/`L1`) to guarded workers unless editing `agy_guard.py`-protected control files (`.git`, `.claude`, `CLAUDE.md`, guard/sandbox files), performing live SSH/ops, working outside a git repo, or explicitly overridden by the user.
- **Wave 0 Recon & Executor Selection**: Use Claude Code's `Agent` tool (read-only) for parallel Wave 0 exploration; do not invent `define_subagent` or `invoke_subagent`. Follow `auto_funding`: use included `agy` subscription slices (`agy_worker.py`), confirmed local Claude Pro/Max broker (`~/.claude/skills/auto/claude_local.py`), or confirmed unexpired Claude cloud credits (`~/.claude/skills/auto/claude_cloud.py`) as appropriate; never call prepaid `api_advisors` without explicit spending authorization.
- **Cross-Family Review & Hard Gates**: Never let the same model family review itself without disclosure; inspect full `diff.patch`, `REVIEW_FLAGS`, run `verify --full` in local sandbox, and apply only `--sha`-verified patches.

## Commands
- **Optional Multi-Perspective Design Consult**:
  ```bash
  R="$HOME/.claude/skills/orchestrator/moa_runner.py"
  python3 "$R" --platform claude --raw --models agy,codex,grok -- '<architecture question>'
  ```
- **Concurrent Wave Dispatch, Verification & Apply (`agy`)**:
  ```bash
  W="$HOME/.claude/skills/orchestrator/agy_worker.py"
  python3 "$W" run --repo "$PWD" --brief '/tmp/orch-<wave>-<slug>-brief.md' --model '<chosen-agy-model>' \
    --platform claude --coordinator-model '<actual-model-or-current>' \
    --task-id '<task-id>' --name '<slug>'
  python3 "$W" review '<run-id>' --executor auto --model '<cross-family-reviewer>' --json
  python3 "$W" resume '<run-id>' --brief '/tmp/orch-<slug>-fix.md'   # max 2 rounds if defects found
  python3 "$W" verify '<run-id>' --full -- <project-test-command>
  python3 "$W" apply '<run-id>' --sha '<reviewed-sha256>'
  python3 "$W" record '<run-id>' --level <filler|L1|L2|L3> --outcome accepted --notes '<summary>'
  python3 "$W" clean '<run-id>'
  ```
  - Pass `--executor agy` or `--executor codex` to guarantee `$0` API spend; prepaid API fallback requires prior explicit authorization.
  - Because `agy_worker.py run --base HEAD` clones committed `HEAD`, integrate upstream Wave `k` changes cleanly before launching dependent Wave `k+1` slices.

End with the Wave Execution Ledger, verified files/commands, residual risks, and **模型调用说明**.
