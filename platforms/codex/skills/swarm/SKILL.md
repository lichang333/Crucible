---
name: swarm
description: Coordinate parallel Codex subagents for substantial multi-file or research tasks when the user invokes /swarm or requests a swarm.
---

# Swarm in Codex

Use this workflow when the user invokes `/swarm`, selects `$swarm`, or explicitly asks for parallel agents. The current Codex session remains responsible for task framing, integration, and the final result.

## Dispatch

- Read the repository instructions and inspect the working tree before assigning work. Preserve existing user changes.
- Use parallel agents only when the work has independent streams that justify the coordination overhead. Keep small, tightly coupled, or same-file edits in the coordinator.
- Use the native Codex subagent tools available in the current session. Do not invent tools or report a worker as launched until the tool call succeeds.
- For a multi-stream implementation, assign non-overlapping file ownership. Give each agent a clear goal, relevant context, owned paths, constraints, and acceptance criteria. Start independent streams in the same turn when their briefs are ready.
- For read-only investigation, keep agents read-only. For implementation, prefer an isolated worktree if the active tool supports one; otherwise enforce distinct file ownership because agents may share the working tree.
- Use the configured native role preferences in [routing.json](routing.json) only when the current subagent interface supports model selection. A configured role does not prove that model is available or was invoked; use a supported fallback and report it.

## Temporary paths and cleanup

- Use a run-specific temporary path. Before using a supplied path, inspect it; if it already exists, is a symlink, or appears to belong to another app or workflow, leave it untouched and choose a fresh path.
- Track the exact paths created for the run, such as fixture repositories, briefs, and worker or verification trees. After review, required verification, and any requested apply, remove only those paths. Confirm a cleanup target resolves to the expected run-specific path before recursive deletion; never sweep a generic parent directory or another run's artifacts.
- Keep MoA and worker run records until the final role/model/Run ID summary is complete. Report any records intentionally retained for audit.

## Boundaries and integration

- This Codex workflow uses native subagents. Do not silently switch to external API calls, `agy_worker.py`, or the `/auto` workflow. Use those routes only when the user explicitly requests them or their applicable workflow has already been authorized.
- Native subagents do not inherit the `agy` guard or sandbox. Keep production operations, credentials, live systems, and execution-boundary or security-control changes with the coordinator, following repository instructions.
- After agents finish, inspect the actual working-tree diff and each report. Resolve overlap or missing work yourself; do not treat a worker's self-report as verification.
- Run the acceptance checks required by the user and repository instructions. Report checks that were not run and any remaining disagreement or limitation.
- If no native subagent tool is available, continue with the current session and state that parallel dispatch was unavailable.

## Final response

Summarize the integrated result, the checks and review actually completed, any unresolved findings, and the actual coordinator and subagent models/channels when known. Identify failed or unavailable agent calls; do not infer model identity from configured role names.
