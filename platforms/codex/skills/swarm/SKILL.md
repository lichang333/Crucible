---
name: swarm
description: Coordinate parallel implementation or research for substantial tasks when the user invokes /swarm or requests a swarm. Codex reviews and integrates the results.
---

# Swarm in Codex

Use this workflow when the user invokes `/swarm`, selects `$swarm`, or explicitly asks for parallel agents. The current Codex session remains responsible for task framing, integration, and the final result.

## Dispatch

- Read the repository instructions and inspect the working tree before assigning work. Preserve existing user changes.
- Use parallel agents only when the work has independent streams that justify the coordination overhead. Keep small, tightly coupled, or same-file edits in the coordinator.
- On explicit `/swarm` or `$swarm` coding tasks, prefer the guarded implementation route below for independent slices. Honor model and executor choices the user makes for the task.
- Use native Codex subagents for parallel research or when native agents are requested. Do not report a worker as launched until the tool call succeeds.
- For a multi-stream implementation, assign non-overlapping file ownership. Give each agent a clear goal, relevant context, owned paths, constraints, and acceptance criteria. Start independent streams in the same turn when their briefs are ready.
- Keep investigation agents read-only. For native implementation, prefer isolated worktrees when available and enforce distinct file ownership.
- Use the configured native role preferences in [routing.json](routing.json) only when the current subagent interface supports model selection. A configured role does not prove that model is available or was invoked; use a supported fallback and report it.

## Implementation via agy

- Read `swarm` in [routing.json](routing.json) and the [shared model catalog](headless.json). Use `implementer.model` for the main slice, `secondary_implementer` for a separate substantive slice or when the main model is unavailable, and `filler` for independent mock data, docs, or boilerplate. Dispatch slices only when the task calls for them. Keep planning, code review, and integration in the current Codex session.
- Use the signed-in Google Antigravity CLI through [agy_worker.py](agy_worker.py). Confirm the configured filler is still offered with `agy models`; use the shared `agy_routes.filler` or handle it in Codex if unavailable. Claude and GPT-OSS share an `agy` quota pool, so one is unlikely to help when that pool is exhausted.
- Confirm the worker guard is registered and the sandbox is available before dispatch. Use `agy models` if model availability is unclear. Base each slice on a committed Git snapshot and give it only the context, owned paths, and acceptance criteria it needs. Handle slices that require uncommitted changes in the current session.
- Run the shared worker from the installed skill. `--model` takes the exact model ID from the route or the user's override.

  ```bash
  W="$HOME/.agents/skills/swarm/agy_worker.py"
  python3 "$W" run --repo '<git-root>' --brief '<brief-file>' \
    --model '<implementation-model>' --platform codex \
    --coordinator-model '<actual-model-or-current>' --name '<slice-name>'
  ```

- Inspect the entire returned patch and its review flags in the current session. Run `verify <run-id> --full -- <project checks>` with the worker before `apply <run-id> --sha <reviewed-patch-sha256>`. Verify against the target `HEAD` and preserve the guard and apply checks. Integrate sequentially and check the combined result.
- If a run fails, inspect any partial patch before assigning the remaining work to an available configured worker or continuing in Codex. Keep tasks in Codex if the guard or sandbox is unavailable. Use `clean <run-id>` for the worker trees once review and verification are finished.

## Temporary paths and cleanup

- Use a run-specific temporary path. Before using a supplied path, inspect it; if it already exists, is a symlink, or appears to belong to another app or workflow, leave it untouched and choose a fresh path.
- Track the exact paths created for the run, such as fixture repositories, briefs, and worker or verification trees. After review, required verification, and any requested apply, remove only those paths. Confirm a cleanup target resolves to the expected run-specific path before recursive deletion; never sweep a generic parent directory or another run's artifacts.
- Keep MoA and worker run records until the final role/model/Run ID summary is complete. Report any records intentionally retained for audit.

## Boundaries and integration

- The guarded agy route applies to the explicitly invoked coding task. Extra model reviews, external API calls, and `/auto` require a separate request.
- Native subagents do not inherit the `agy` guard or sandbox. Keep production operations, credentials, live systems, and execution-boundary or security-control changes with the coordinator, following repository instructions.
- After agents finish, inspect the actual working-tree diff and each report. Resolve overlap or missing work yourself; do not treat a worker's self-report as verification.
- Run the acceptance checks required by the user and repository instructions. Report checks that were not run and any remaining disagreement or limitation.
- If no native subagent tool is available, continue with the current session and state that parallel dispatch was unavailable.

## Final response

Summarize the integrated result, the checks and review actually completed, any unresolved findings, and the actual coordinator and subagent models/channels when known. Identify failed or unavailable agent calls; do not infer model identity from configured role names.
