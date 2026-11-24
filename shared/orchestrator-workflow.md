# Shared Orchestrator Mode Workflow

**Orchestrator Mode** (`/orchestrator`) turns the coordinating host session into a strict, pure-control-plane **Orchestrator**: it frames goals, runs read-only reconnaissance, designs a multi-wave DAG of disjoint slices, dispatches isolated workers, enforces cross-family cold-eyes review and sandboxed verification, integrates sequentially, and reports results.

Read [the shared coding workflow](auto-workflow.md) alongside this specification. All sandbox, guard, funding, quota-handoff, and SHA/HEAD apply rules in [auto-workflow.md](auto-workflow.md) remain binding.

## 1. Core Contract (Zero Direct Business-Code Edits)

- **Host never edits application code or tests directly**: Even a small 1-file application or test change MUST be delegated as a bounded worker slice (`filler` or `L1`) under guarded sandbox isolation.
- **Explicit exceptions (Control-Plane & Ops Only)**:
  - **Protected security/execution-boundary control files**: `.git`, `.cursor`, `.gemini`, `.claude`, `.codex`, `.opencode`, `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `hooks.json`, `.env`, `agy_guard.py`, `run_sandboxed.sh`, `sandbox.sb`, or other files guarded by `agy_guard.py` stay with the host coordinator.
  - **Live operations / SSH / deployment**: handled directly by the host coordinator, never delegated to workers.
  - **Explicit user override**: if the user explicitly asks the host to edit a file directly (or work outside a git repo where guarded cloning cannot apply), honor the override and disclose it.
- **Sub-Worker / Subagent Exemption**: If this session is already a delegated worker (`AUTO_WORKER=1`, `auto-worker/` working directory, `TASK BRIEF:` / `FEEDBACK ON YOUR PREVIOUS ATTEMPT`), a headless `--mode plan` review/advisor run (`auto-review-` / `moa-`), or a spawned subagent (`invoke_subagent` / `subagent` / `<swarm_worker>`), execute the assigned slice directly and NEVER launch nested orchestrators or `agy_worker.py` / `moa_runner.py` swarms.

## 2. Four-Wave Execution Lifecycle

### Wave 0: Recon & Multi-Wave DAG Plan
1. Inspect the repository read-only (host search/read tools or parallel read-only subagents).
2. For `L3` ambiguity, invariant design, or architecture trade-offs, optionally run read-only `moa_runner.py --raw --models agy,codex,grok` (`$0` subscription channels; prepaid APIs require explicit spending authorization).
3. Partition the task into **Wave 1..N** streams where every stream inside the same wave has strictly non-overlapping `OWNED FILES`. Keep shared interfaces/types in an upstream wave or a dedicated contract slice.
4. State a compact **Wave Plan Table**:
   `Wave | Stream | Tier & Model | Owned Paths | Depends On`
5. **Never plan-and-pause**: Unless requirements are genuinely ambiguous (ask concisely first), launch Wave 1 immediately in the **SAME TURN**. Never roleplay workers or simulate outputs in prose.

### Wave 1..N: Concurrent Sandboxed Execution
- Launch all independent streams in the current wave concurrently in ONE turn via `agy_worker.py run --platform <platform>` (or explicitly authorized `claude_local.py` / `claude_cloud.py`).
- **Automatic Tiered Model Selection** (read [headless.json](headless.json) and platform [routing.json](routing.json); run `agy_worker.py models` to check active catalog):
  - `filler` (mock data, comments, copy, boilerplate): `gemini-4-argon-low` (fallback `gemini-4-argon-medium`, or `gpt-oss-120b-medium` on Codex `swarm.filler`)
  - `L1` (bounded mechanical / single-module edits): `gemini-4-carbon-high` (fallback `gemini-4-argon-high`)
  - `L2` (standard feature / multi-file slice): `gemini-4-neon-high` (fallback `gemini-4-carbon-high` or `claude-sonnet-5-5-high`)
  - `L3` / deep synthesis: `gemini-pro-orchestrator-neon` / `gemini-4-neon-xhigh` (fallback `gemini-pro-orchestrator`, or `routing.json` `swarm.implementer` / `secondary_implementer` where defined)
- **Git Snapshot Rule for Multi-Wave DAGs**: `agy_worker.py run --base HEAD` clones committed `HEAD` (not unstaged workspace edits). Before dispatching dependent Wave `k+1`, integrate Wave `k` cleanly onto the base snapshot (`HEAD` / commit or explicitly planned independent target) so downstream workers read real integrated code rather than missing interfaces. Split independent work into Wave 1 whenever possible to minimize cross-wave waits.
- **3-Tier Failover**: Follow [auto-workflow.md](auto-workflow.md) quota-handoff rules; preserve partial `diff.patch` files on `429` / `quota_exhausted` and switch across Gemini 4 / Orchestrator vs. Claude 5.5 / `gpt-oss-120b-medium` (`--live` / `quota_handoff` aware).

### Wave Gate: Cold-Eyes Review, Targeted Fix Loop & Sandbox Verification
For each finished slice before integration:
1. Read the full `diff.patch` and inspect `REVIEW_FLAGS` (`protected_paths`, `sensitive_paths`, `execution_surface`, `INCOMPLETE_RUN`).
2. Run **cross-family cold-eyes review** (never same family reviewing itself: Gemini 4 / Orchestrator author -> `claude-opus-5-5-high`, `claude-sonnet-5-5-high`, `gpt-6-luna-high`, or `grok`; Claude author -> `gemini-pro-orchestrator-neon`):
   - Use `python3 "$W" review '<run-id>' --executor auto --model '<cross-family-reviewer>' --json` (`--executor auto` prioritizes `$0` subscription pools: `agy` pools -> ChatGPT `codex` `gpt-6-luna-high` -> signed-in OpenCode xAI `grok`; pass `--executor agy` or `--executor codex` to guarantee `$0` API spend, as reaching keyed prepaid APIs requires prior explicit authorization).
3. If review or verification finds defects, write a concise feedback file citing exact file/line and expected behavior, then run `python3 "$W" resume '<run-id>' --brief '<feedback.md>'` (max 2 fix rounds).
4. Run full sandboxed tests against the target base: `python3 "$W" verify '<run-id>' --full -- <project-test-command>`.

### Final Integration & Cleanup
1. Apply reviewed patches sequentially one slice at a time (`python3 "$W" apply '<run-id>' --sha '<reviewed-sha256>'`), re-verifying subsequent slices against updated `HEAD` when earlier slices change shared code or tests.
2. Record each slice (`python3 "$W" record '<run-id>' --level <filler|L1|L2|L3> --outcome accepted|fixed|rejected --notes '<summary>'`), clean worker trees (`python3 "$W" clean '<run-id>'`), and remove only the run-specific temporary briefs created for the run.
3. Run final integrated verification on the combined result without making host business-code edits.

## 3. Slice Brief Template
Write each brief to a unique run-specific temp file (e.g., `/tmp/orch-<wave>-<slug>-brief.md`) with:
- `GOAL`: exact slice deliverable and definition of done.
- `CONTEXT`: exact files, interfaces, and upstream wave outputs this slice reads.
- `OWNED FILES`: exact paths this worker may modify or create.
- `DO NOT TOUCH`: sibling/other-wave paths, shared lockfiles/configs unless owned, `.git`, host dot-dirs.
- `ACCEPTANCE`: exact test/lint/build command to run inside the sandbox.

## 4. Final Report Format
Present a concise structured ledger in the user's language:
1. **Wave Execution Ledger**: Markdown table with columns `Wave | Stream | Tier | Worker Model | Reviewer Model | Run ID | Verify | Outcome`.
2. **Modified Paths & Verification**: Integrated file list and exact sandboxed/final check results.
3. **Residual Risks & 模型调用说明**: Open items plus actual coordinator model, every `agy` / `codex` / `grok` / API worker and reviewer invoked (including failed/fallback runs), and whether zero direct host edits were maintained.
