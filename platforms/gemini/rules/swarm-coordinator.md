---
trigger: always_on
description: "Default cost-first MoA Swarm coordinator triage across Antigravity (agy) sandbox workers, read-only subagents, and cross-family reviewers without typing /swarm"
---

# Default Swarm Coordinator Routing (Antigravity / agy)

**Sub-Worker / Subagent Exemption**: If this session is already a delegated `agy_worker.py` worker (`You are a coding worker.` / `TASK BRIEF:` / `FEEDBACK ON YOUR PREVIOUS ATTEMPT` or working directory under `auto-worker/`), a headless `--mode plan` review/advisor call (`auto-review-` / `moa-`), or a spawned subagent (`invoke_subagent` / `<swarm_worker>`), skip Coordinator delegation below and execute your assigned task directly.

Otherwise, triage every incoming user prompt automatically (no `/swarm` prefix needed unless requirements are genuinely ambiguous):

1. **Quick Q&A, explanations, 1–2 small L0 edits, live ops/SSH, or guard/sandbox/control-file edits (`GEMINI.md`, `AGENTS.md`, `.gemini/`, `.agents/`, `hooks.json`)**:
   - Handle directly in the current Antigravity session for immediate response.
2. **Architecture, trade-offs, or multi-perspective analysis**:
   - Consult `python3 "$HOME/.gemini/config/skills/moa/moa_runner.py" --platform gemini --raw -- '<question>'` (use `--models agy,grok` for `$0` marginal API spend via Google AI Ultra + signed-in OpenCode xAI subscription, or include keyed `glm`, `deepseek`, `deepseek-v4.1`, `kimi`, `kimi-highspeed`, `minimax`) and/or parallel read-only `research` subagents (`invoke_subagent`), then synthesize with codebase evidence.
3. **Bounded coding (`filler`/`L1`/`L2`) or multi-file features/refactors (inside a git repo)**:
   - Offload coding to isolated `agy` sandbox workers via `$HOME/.gemini/config/skills/swarm/agy_worker.py` (`--platform gemini`; full runbook in `$HOME/.gemini/config/skills/swarm/SKILL.md`).
   - For multi-file tasks, split into **2–4 disjoint slices** (`OWNED FILES` non-overlapping) and launch concurrent `agy_worker.py run --platform gemini` workers in one turn. (Only use Antigravity's built-in `swarm` board tool if the user explicitly asks for the native Swarm Board UI.)
4. **Automatic Coordinator Model Selection & Failover (never ask the user to pick models)**:
   - Filler (mock data, comments, copy, boilerplate): `gemini-4-argon-low` (`agy_routes.filler`; or bridged `grok` / `deepseek-v4.1` for pure text) — reserve `Carbon`, `Hydrogen`, and `GPT-6-Luna` for core logic & review
   - Fast L1: `gemini-4-argon-high` / `gemini-4-carbon-medium`
   - Standard L1/L2: `gemini-4-carbon-high` (or `claude-sonnet-5-5-high`)
   - Deep synthesis: `gemini-4-hydrogen-xhigh` / `gemini-4-hydrogen-high`
   - L3 / tricky diagnosis: `gemini-pro-orchestrator` (`Orchestrator (Carbon)`) or `gemini-pro-orchestrator-argon`
   - Cross-family `review --executor auto`: Gemini author -> `claude-opus-5-5-high` / `claude-sonnet-5-5-high`; Claude author -> `gemini-pro-orchestrator` (pass `--executor agy` for subscription-only or `--model grok` / `--executor api` when `agy` pools run low).
   - **3-tier automatic failover**:
     - Tier 1 (`agy` dual pools): on `429` or `quota_exhausted`, preserve partial `diff.patch` and fail over between **Gemini 4 / Orchestrator** and **Claude 5.5 / `gpt-oss-120b-medium`**.
     - Tier 2 (`agy` pools exhausted): fail over `review --executor auto` to bridged `grok` (`Grok-4.7` via signed-in OpenCode xAI subscription at `$0` API spend) or keyed APIs, and fall back to scoped host/Claude-local execution if needed.
     - Tier 3 (prepaid API balance exhausted or key expired): `moa_runner.py` (`--review` / `aggregate`) and `agy_worker.py review --executor api` fail over across remaining healthy providers (`grok` -> `deepseek` -> `deepseek-flash` -> `glm` -> `kimi` -> `minimax`).
5. **Mandatory Verification Before Apply**:
   - Inspect `diff.patch` & `REVIEW_FLAGS` (`.gemini`, `.agents`, `.git`, secrets protected), run `review --executor auto`, `verify --full -- <test-cmd>`, `apply --sha`, and include **模型调用说明**.
