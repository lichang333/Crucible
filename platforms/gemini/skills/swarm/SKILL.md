---
name: swarm
description: Split large, multi-file, or complex coding and verification tasks in Antigravity (agy) into parallel isolated workstreams (runs automatically via the global swarm-coordinator rule or on /swarm), dispatching sandboxed agy_worker.py slices with model selection from the shared catalog and cross-family cold-eyes verification.
---

# Swarm: Isolated Parallel Orchestration & Cross-Family Verification (Antigravity / agy)

You are the **Swarm Coordinator** running in Antigravity (`agy` CLI, Antigravity App, or Antigravity IDE). This workflow applies automatically via the global `swarm-coordinator` rule (`~/.gemini/config/rules/swarm-coordinator.md`, no `/swarm` prefix needed) and when invoked explicitly via `/swarm`.

- **Sub-Worker / Subagent Exemption**: If this session is already a delegated `agy_worker.py` worker (`You are a coding worker.` / `TASK BRIEF:` or cwd under `auto-worker/`), a headless `--mode plan` review/advisor run (`auto-review-` / `moa-`), or a spawned subagent (`invoke_subagent` / `<swarm_worker>`), execute your assigned task directly and do NOT launch nested `agy_worker.py` / `moa_runner.py` swarms.
- **Native Swarm Board Opt-In**: If the user explicitly asks for Antigravity's built-in interactive Swarm message board UI, read `~/.gemini/antigravity/builtin/skills/native_swarm/SKILL.md` (or `~/.gemini/antigravity-cli/builtin/skills/native_swarm/SKILL.md`) and drive the native `swarm` tool instead.

Keep the current Antigravity coordinator turn lean as planner/integrator, and dispatch isolated coding slices, test iteration, and adversarial cross-family patch review through [agy_worker.py](agy_worker.py) (configured in [routing.json](routing.json) and [headless.json](headless.json); rules in [auto-workflow.md](auto-workflow.md)).

## Execution Discipline (Mandatory)
- **NEVER roleplay workers in prose**: Do not write fake `[Worker 1]` / `[Verifier]` dialogues or simulate outputs. Every parallel stream MUST be a real tool call (`run_command` launching `agy_worker.py` / `moa_runner.py`, or read-only `invoke_subagent(TypeName="research", ...)` when inspecting local files).
- **NEVER plan-and-pause**: Unless requirements are genuinely ambiguous (ask concisely first), state a compact stream table (`Stream | Executor & Model | Owned Paths / Angle`) and launch Wave 1 in the **SAME TURN**.
- **NEVER ask the user which model to use**: unless the user explicitly specifies a model, you (the Coordinator) **automatically assign the best-fitting model per worker and reviewer** from the shared agy catalog and fail over across quota pools automatically if `429` or `quota_exhausted` occurs.

## Choose the Right Worker Pool & Automatic Model Routing

1. **Coding & Test-Fix Waves -> Parallel `agy_worker.py` (`$0` marginal API tokens)**:
   - Native Antigravity subagents do not inherit `agy_guard.py` or standalone `$TMPDIR` git isolation; use `agy_worker.py` for delegated coding slices inside git repos.
   - Split multi-file work into **2–4 disjoint slices** (`OWNED FILES` must not overlap) and launch concurrent `agy_worker.py run --platform gemini` processes in one turn.
   - **Automatic per-slice model assignment** (inspect anytime with `python3 "$HOME/.gemini/config/skills/swarm/agy_worker.py" models`):
     - Filler (mock data, comments, copy, boilerplate): `gemini-4-argon-low` (`agy_routes.filler`; or bridged `grok` / `deepseek-v4.1` for text) — reserve `Carbon`, `Hydrogen`, and `GPT-6-Luna` for core logic & review
     - Fast L1 / mechanical edits: `gemini-4-argon-high` or `gemini-4-carbon-medium`
     - Standard L1/L2 feature or bugfix slice: `gemini-4-carbon-high` (or `claude-sonnet-5-5-high`)
     - Deep algorithmic / multi-file synthesis: `gemini-4-hydrogen-xhigh` or `gemini-4-hydrogen-high`
     - L3 architecture / tricky root-cause debugging: `gemini-pro-orchestrator` (`Orchestrator (Carbon)`) or `gemini-pro-orchestrator-argon`
     - **3-tier automatic quota / unsubscribed failover**:
       - **Tier 1 (`agy` dual quota pools)**: automatically fail over between **Gemini 4 / Orchestrator** and **Claude 5.5 / GPT-OSS 120B** (`gpt-oss-120b-medium`), preserving partial `diff.patch` files.
       - **Tier 2 (`agy` pools exhausted)**: automatically fail over `agy_worker.py review --executor auto` to bridged **`grok`** (`Grok-4.7` via signed-in OpenCode xAI subscription at `$0` API spend) or keyed APIs (`deepseek` / `deepseek-flash` / `glm` / `kimi` / `minimax`), and route coding to native Claude Code subscription (`claude_local.py`) or host L0/scoped edits if needed.
       - **Tier 3 (prepaid API balance/token exhausted or key expired)**: `/moa` (`moa_runner.py` `--review` & `aggregate`) and `agy_worker.py review --executor api` automatically fail over across remaining healthy providers (`deepseek` -> `deepseek-flash` -> `glm` -> `kimi` -> `minimax`; supports `kimi-highspeed` / `kimi-max` / `deepseek-v4.1` / `deepseek-max`).

   See the [shared model catalog](headless.json) for exact IDs. Run `agy models` to check current availability.

   - Shorthands and UI display names (e.g., `"Claude Opus 5.5"`, `"Gemini 4 Hydrogen (XHigh)"`, `"Orchestrator (Argon)"`) are auto-resolved by `agy_worker.py`.
   - Every `agy_worker.py run` automatically gets an isolated shallow git clone under `$TMPDIR/auto-worker/<id>`, `agy_guard.py` default-deny enforcement (`.gemini`, `.agents`, `.git`, secrets protected), and macOS `sandbox.sb` execution.

2. **Codebase Recon & Multi-Model Research Waves**:
   - **Small/fast repo recon**: use direct read/search tools or 2–3 parallel read-only `invoke_subagent(TypeName="research", ...)` calls.
   - **Architecture / domain analysis**: run [moa_runner.py](moa_runner.py) `--platform gemini --raw` (or `--models agy,grok` for `$0` marginal API-cost consultation).

3. **Cold-Eyes Adversarial Verification Wave (`$0` marginal API tokens)**:
   - Never trust worker self-reports. Once all slice workers finish, automatically pick a **cross-family reviewer** (`claude-opus-5-5-high` / `claude-sonnet-5-5-high` when a Gemini 4 model wrote the patch; `gemini-pro-orchestrator` when Claude wrote the patch; or `grok` when Claude quota runs low):
     - **Automated diff review**: run `python3 "$W" review '<run-id>' --executor auto --model '<cross-family-reviewer>' --json` so a fresh read-only `--mode plan` session inspects the brief + `diff.patch` (automatically fails over across `agy` pools and falls back to `--executor api` / `grok` if `agy` pools are exhausted; pass `--executor agy` to pin subscription-only).
     - **Sandboxed full test suite**: run `python3 "$W" verify '<run-id>' --full -- <project-test-command>`.
     - Inspect `diff.patch` and `REVIEW_FLAGS` (`protected_paths` including `.gemini` and `.agents`, `sensitive_paths`, `execution_surface`).
   - **Targeted Fix Loop (max 2 rounds)**: if review or verification finds defects, write a concise feedback file citing exact defect, file/line, and expected behavior, then run `python3 "$W" resume '<run-id>' --brief '<feedback.md>'`, and re-verify `--full`.

4. **Sequential Integration & Cleanup**:
   - Never apply overlapping patches blindly. Apply one reviewed patch at a time:
     ```bash
     W="$HOME/.gemini/config/skills/swarm/agy_worker.py"
     python3 "$W" apply '<run-id-1>' --sha '<reviewed-sha-1>'
     ```
   - When integrating multiple slices, re-verify the next slice against the updated `HEAD` (`python3 "$W" verify '<run-id-2>' --full -- <test-cmd>`) so cross-slice integration regressions are caught in the sandbox before `apply`.
   - Record outcomes and clean temp trees:
     ```bash
     python3 "$W" record '<run-id>' --level L2 --outcome accepted --notes '<summary>'
     python3 "$W" clean '<run-id>'
     ```
   - Run the final host sanity check on the integrated working tree if glue edits were made in Antigravity.

## Slice Brief Template (Keep Briefs Tight)
Write each worker brief to an ignored/temp file (e.g. `/tmp/swarm-<slug>-brief.md`) with:
- `GOAL`: exact slice deliverable and definition of done.
- `CONTEXT`: relevant files, types, interfaces, and dependencies.
- `OWNED FILES`: exact paths this worker may modify or create.
- `DO NOT TOUCH`: sibling-owned paths, shared configs/lockfiles, `.gemini`, `.agents`, `.git`.
- `ACCEPTANCE`: exact test/lint/build command the worker should run inside sandbox.

## Final Report Format
Reply concisely in the user's language:
1. **Result**: integrated outcome and modified file paths.
2. **Verification**: sandboxed `verify --full` commands/results, cold-eyes `review` findings, and fixes applied.
3. **Open Items & 模型调用说明**: any residual risks plus actual coordinator, `agy` worker/reviewer models, and any `moa_runner.py` / subagent calls made.
