---
name: swarm
description: Split large, multi-file, or complex coding and verification tasks in Claude Code (and Claude Magpie) into parallel isolated workstreams invoked via /swarm, dispatching sandboxed agy_worker.py slices with automatic model selection from the shared catalog and cross-family cold-eyes verification.
---

# Swarm: Parallel Orchestration & Cross-Family Verification (Claude Code)

You are the **Swarm Coordinator** running in Claude Code (or `Claude Magpie`). Use this workflow when the user invokes `/swarm` or asks for parallel multi-stream execution. Keep the current Claude session lean as planner/integrator, and dispatch isolated coding slices, test iteration, and adversarial cross-family patch review through [agy_worker.py](agy_worker.py) (configured in [routing.json](routing.json) and [headless.json](headless.json); rules in [auto-workflow.md](auto-workflow.md)).

- **Sub-Worker / Subagent Exemption**: If this session is already a delegated worker (`You are a coding worker.` / `TASK BRIEF:` or cwd under `auto-worker/`), a headless `--mode plan` review/advisor run, or a spawned `Agent` subagent, execute your assigned task directly and do NOT launch nested `agy_worker.py` / `moa_runner.py` swarms.

## Execution Discipline (Mandatory)
- **NEVER roleplay workers in prose**: Do not write fake `[Worker 1]` / `[Verifier]` dialogues or simulate outputs. Every parallel stream MUST be a real tool call (`Bash` launching `agy_worker.py` / `moa_runner.py`, or read-only `Agent` tool calls for local exploration).
- **NEVER plan-and-pause**: Unless requirements are genuinely ambiguous (ask concisely first), state a compact stream table (`Stream | Executor & Model | Owned Paths / Angle`) and launch Wave 1 in the **SAME TURN**.
- **NEVER ask the user which model to use**: unless the user explicitly specifies a model, you (the Coordinator) **automatically assign the best-fitting model per worker and reviewer** from the shared `agy` catalog and fail over across quota pools automatically if `429` or `quota_exhausted` occurs.

## Worker Pool & Automatic Model Routing

1. **Coding & Test-Fix Waves -> Parallel `agy_worker.py` (`$0` marginal API tokens)**:
   - Native Claude Code `Agent` subagents do not inherit `agy_guard.py` or standalone `$TMPDIR` git isolation; use `agy_worker.py` for delegated coding slices inside git repos.
   - Split multi-file work into **2–4 disjoint slices** (`OWNED FILES` must not overlap) and launch concurrent `agy_worker.py run --platform claude` processes in one turn:
     ```bash
     W="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/swarm/agy_worker.py"
     python3 "$W" run --repo "$PWD" --brief '/tmp/swarm-<slug>-brief.md' \
       --model '<chosen-agy-model>' --platform claude \
       --coordinator-model '<actual-model-or-current>' --name '<slug>'
     ```
   - **Automatic per-slice model assignment** (inspect anytime with `python3 "$W" models`):
     - Filler (mock data, comments, copy, boilerplate): `gemini-4-argon-low` (`agy_routes.filler`)
     - Fast L1 / mechanical edits: `gemini-4-carbon-high` / `gemini-4-argon-high` / `gemini-4-carbon-medium`
     - Standard L2 feature or bugfix slice: `gemini-4-neon-high` (fallback `gemini-4-carbon-high` or `claude-sonnet-5-5-high`)
     - Deep algorithmic / multi-file synthesis: `gemini-4-neon-xhigh` or `gemini-4-hydrogen-xhigh`
     - L3 architecture / tricky root-cause debugging: `gemini-pro-orchestrator-neon` or `gemini-pro-orchestrator`
   - **3-tier automatic failover** (complying with `auto_funding`):
     - **Tier 1 (`agy` dual pools)**: Fail over between **Gemini 4 / Orchestrator** and **Claude 5.5 / `gpt-oss-120b-medium`**, preserving partial `diff.patch` files.
     - **Tier 2 (`agy` pools exhausted)**: Fail over `review --executor auto` at `$0` API spend to ChatGPT-authenticated **`codex`** (`gpt-6-luna-high`) or OpenCode **`grok`** (`Grok-4.7`), and route coding to the confirmed local Claude Pro/Max broker (`claude_local.py`) or host L0/scoped edits if needed.
     - **Tier 3 (prepaid API fallback)**: Only invoke paid `api_advisors` (`deepseek` -> `deepseek-flash` -> `glm` -> `kimi` -> `minimax`) when explicitly authorized by the user.
   - Every `agy_worker.py run` automatically gets an isolated shallow clone under `$TMPDIR/auto-worker/<id>`, `agy_guard.py` default-deny enforcement (`.claude`, `.git`, `.gemini`, `.agents`, secrets protected), and macOS `sandbox.sb` execution.

2. **Codebase Recon & Multi-Model Research Waves**:
   - **Parallel repo recon**: Use Claude Code's native **`Agent` tool (read-only)**; do not invent `define_subagent` or `invoke_subagent`.
   - **Architecture / domain consultation**: Run [moa_runner.py](moa_runner.py) (`R="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/swarm/moa_runner.py"`):
     `python3 "$R" --platform claude --raw --models agy,codex,grok -- '<architecture question>'`

3. **Cold-Eyes Adversarial Verification & Sequential Integration**:
   - Never trust worker self-reports. Pick a **cross-family reviewer** (`claude-opus-5-5-high` / `claude-sonnet-5-5-high` for Gemini authors; `gemini-pro-orchestrator-neon` for Claude authors; `codex` / `grok` fallback):
     ```bash
     python3 "$W" review '<run-id>' --executor auto --model '<cross-family-reviewer>' --json
     python3 "$W" verify '<run-id>' --full -- <project-test-command>
     ```
   - Inspect full `diff.patch` and `REVIEW_FLAGS`. If defects are found, write a concise feedback file and run `python3 "$W" resume '<run-id>' --brief '/tmp/swarm-<slug>-fix.md'` (max 2 rounds), then re-run `verify --full`.
   - Apply one reviewed patch at a time (re-verifying dependent slices against updated `HEAD` before `apply`):
     ```bash
     python3 "$W" apply '<run-id>' --sha '<reviewed-sha256>'
     python3 "$W" record '<run-id>' --level L2 --outcome accepted --notes '<summary>'
     python3 "$W" clean '<run-id>'
     ```

## Slice Brief Template (Keep Briefs Tight)
Write each worker brief to `/tmp/swarm-<slug>-brief.md` with:
- `GOAL`: exact slice deliverable and definition of done.
- `CONTEXT`: relevant files, types, interfaces, and dependencies.
- `OWNED FILES`: exact paths this worker may modify or create.
- `DO NOT TOUCH`: sibling-owned paths, shared configs/lockfiles, `.claude`, `.git`, `.gemini`, `.agents`.
- `ACCEPTANCE`: exact test/lint/build command to run inside sandbox.

## Final Report Format
Summarize concisely in the user's language:
1. **Result**: integrated outcome and modified file paths.
2. **Verification**: sandboxed `verify --full` commands/results, cold-eyes `review` findings, and fixes applied.
3. **Open Items & 模型调用说明**: residual risks plus actual coordinator, worker/reviewer models, and any `moa_runner.py` / `Agent` calls made.
