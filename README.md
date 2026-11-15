# MoA — Multi-agent Orchestration & Auto-sandbox

**MoA** here means *Multi-agent Orchestration & Auto-sandbox*: shared multi-agent
workflows for Antigravity, OpenCode, Cursor, Claude Code, and Codex. The `/moa`
skill remains Mixture-of-Agents Q&A synthesis; `/auto` and `/swarm` cover sandboxed
coding and parallel orchestration. Paths and command names stay `moa` for compatibility.

Separate platform instructions, one shared implementation. The current host session
triages tasks and integrates changes, while subscription-backed workers (**Google AI Ultra**
via `agy` CLI at zero marginal API cost across 8 active families / 19 variants, plus
bridged **`grok`** (`Grok-4.7` via signed-in OpenCode xAI OAuth subscription at zero API
cost or `XAI_API_KEY`), optional prepaid APIs `glm` (`GLM-5.3`), `deepseek`
(`DeepSeek-V4-Pro`), and `minimax` (`MiniMax-M3`), and optional Claude Code subscription
bridges) provide parallel Q&A analysis, isolated coding slices, and cross-family
cold-eyes verification.

| Workflow | Purpose | Execution |
|---|---|---|
| `/moa` | Multi-model Q&A and analysis | Read-only `agy` (`Orchestrator (Carbon)`) + `grok` (OpenCode xAI subscription or `XAI_API_KEY`) + configured API answers (`glm`/`deepseek`/`minimax`); current-session synthesis |
| `/auto` | Delegated single-module coding | Isolated `agy` sandbox worker (or native Claude Code CLI / Claude cloud bridge); cross-family review + local `verify --full` & `apply --sha` |
| `/swarm` | Parallel multi-file orchestration | Automatic prefix-free triage in Antigravity / `agy` (`always_on` rule), OpenCode (`default_agent: swarm`), & Cursor (`alwaysApply` rule + `swarm-coordinator`), splitting work into disjoint sandboxed `agy` slices with cross-family verification and cross-pool quota failover |

Provider models, active `agy` family tiers (`agy_catalog` / `agy_routes` / `agy_alternatives`),
and role defaults live in `config/`; application profiles (`codex.json`, `claude.json`,
`gemini.json`, `opencode.json`, `cursor.json`) inherit shared defaults from
[headless.json](config/headless.json).

The shared runners under `skills/` are platform-agnostic: any agent host can drive them
directly, including Muse. Use `--platform headless` with the shared scripts when no platform
entrypoint applies; platform folders are symlinks into the shared implementation.

## Layout

```text
AGENTS.md / CLAUDE.md / GEMINI.md   platform-specific project entrypoints
platforms/codex/skills/             Codex moa and auto skill entrypoints
platforms/claude/skills/            Claude moa and auto skill entrypoints
platforms/gemini/skills/            Antigravity / Gemini moa, auto and swarm skill entrypoints
platforms/gemini/rules/             Antigravity / agy always_on triage rule (`swarm-coordinator.md`)
platforms/opencode/skills/          OpenCode moa, auto and swarm skill entrypoints
platforms/opencode/agents/          OpenCode primary agents (`swarm.md`)
platforms/cursor/skills/            Cursor moa, auto and swarm skill entrypoints (ambient auto-invoke)
platforms/cursor/agents/            Cursor proactive subagent (`swarm-coordinator.md`)
platforms/cursor/rules/             Cursor always-apply triage rule (`swarm-coordinator.mdc`)
shared/                             common project and workflow rules
config/                             provider defaults (`headless.json`) and platform profiles
skills/moa/                         shared API/agy runner and offline tests
skills/auto/                        agy/native Claude executors, cloud bridge, guard, sandbox and tests
tests/                              installer and platform package tests
```

Platform folders link to shared scripts, workflow documents, and profiles. Edit the source
in `skills/`, `shared/`, or `config/`; there are no copied implementations. API keys remain
in the existing local `skills/moa/.env`, with no per-platform copy.

## Install or migrate

```bash
./install.sh --dry-run
./install.sh                         # all platforms (codex, claude, gemini, opencode, cursor)
./install.sh --platform codex        # only Codex
./install.sh --platform claude       # only Claude
./install.sh --platform gemini       # only Gemini / agy (moa, auto, swarm skills + always_on rule; alias: --platform agy)
./install.sh --platform opencode     # only OpenCode (moa, auto, swarm skills + swarm agent)
./install.sh --platform cursor       # only Cursor (moa, auto, swarm skills + agent + alwaysApply rule)
```

Install targets:
- **Codex**: `~/.agents/skills/{moa,auto}`
- **Claude**: `~/.claude/skills/{moa,auto}`
- **Gemini / Antigravity (`agy`)**: `~/.gemini/config/skills/{moa,auto,swarm}` plus
  `~/.gemini/config/rules/swarm-coordinator.md` (`trigger: always_on`, active across `agy` CLI,
  Antigravity App, and Antigravity IDE without typing `/swarm`, with an automatic exemption for
  delegated `agy_worker.py` sub-workers and subagents).
- **OpenCode**: `~/.config/opencode/skills/{moa,auto,swarm}` plus
  `~/.config/opencode/agents/swarm.md`. Set `"default_agent": "swarm"` in
  `~/.config/opencode/opencode.jsonc` to enter `Swarm` directly without `/swarm` (`Tab` switches
  between `Swarm`, `Build`, and `Plan`). Keep OpenCode's host model on `zhipu/glm-5.3`,
  `deepseek/deepseek-v4-pro`, `minimax/MiniMax-M3`, `xai/grok-4.5`, or `opencode/*-free`
  (e.g., `opencode/glm-5.3-flash-free`) rather than OpenCode's built-in `google/*` provider,
  which routes to Google AI Studio Free Tier (`limit: 0`) instead of your Google AI Ultra
  (`agy`) subscription.
- **Cursor**: `~/.cursor/skills/{moa,auto,swarm}`, `~/.cursor/agents/swarm-coordinator.md`, and
  `~/.cursor/rules/swarm-coordinator.mdc` (`alwaysApply: true`). Cursor auto-invokes these
  skills on matching prompts (without `disable-model-invocation: true`) or via `/swarm`,
  `/auto`, and `/moa` (`Option + Enter` pins a skill for the session). To force unconditional
  global triage before project rules load, you can also paste the short Coordinator rule into
  **Cursor Settings > Rules > User Rules**.

The installer replaces legacy shared Claude→Codex links with independent links, backs up
conflicts under `~/.local/share/moa-install-backups/`, and preserves unrelated Gemini hooks.
A Codex-only migration also detaches a recognized old managed Claude→Codex link so Claude
does not silently start reading Codex instructions. Unselected platforms are left alone.

The shared `agy` guard is registered in `~/.gemini/config/hooks.json` (inert unless
`AUTO_WORKER=1` is set). An existing `skills/moa/.env` is preserved; when moving from an
older installed checkout, its local key file is copied if the new checkout has none, otherwise
`skills/moa/.env.example` is used. Old run records stay in their original checkout.

## Inspect routes without calling models

```bash
python3 skills/moa/moa_runner.py --platform cursor --show-config
python3 skills/moa/moa_runner.py --platform opencode --dry-run
python3 skills/auto/agy_worker.py models --json
python3 skills/auto/agy_worker.py models --live
```

These commands (except `--live`, which queries `agy` subscription quota state) do not call
models or load paid API keys:
- **8 active `agy` families / 19 variants** (excluding retired `gemini-3.8`):
  - **Gemini 4 / Orchestrator pool**: `gemini-pro-orchestrator` (`Orchestrator (Carbon)`),
    `gemini-pro-orchestrator-argon`, `gemini-4-carbon-{high,medium,low}`,
    `gemini-4-argon-{high,medium,low}`, `gemini-4-hydrogen-{xhigh,high,medium,low}`
  - **Claude 5.5 / GPT-OSS pool**: `claude-opus-5-5-{high,medium,low}`,
    `claude-sonnet-5-5-{high,medium,low}`, `gpt-oss-120b-medium`
- **3-Tier Automatic Quota & Unsubscribed Failover**:
  - **Tier 1 (`agy` dual quota pools)**: unless you explicitly name a model, the Coordinator
    picks task-fit slice models and **cross-family reviewers** automatically (pairing Gemini 4 /
    Orchestrator with Claude Opus/Sonnet 5.5 or GPT-OSS 120B) and switches quota pools
    automatically on `429` or `quota_exhausted` while preserving partial `diff.patch` files.
    `agy_worker.py` accepts canonical IDs, shorthands, and UI display names (via
    `resolve_agy_model()`).
  - **Tier 2 (`agy` unsubscribed / uninstalled / all pools exhausted)**: automatically downgrade
    to OpenCode/Cursor native host or scoped native subagents using healthy `zhipu/glm-5.3`,
    `deepseek/deepseek-v4-pro`, `minimax/MiniMax-M3`, `xai/grok-4.5` (subscription), or
    `opencode/*-free`, and run `agy_worker.py review --executor auto` (cross-pool `agy`
    failover -> `--executor api`) or `agy_worker.py review --executor api`.
  - **Tier 3 (prepaid API balance/token exhausted or key expired)**: `/moa` (`moa_runner.py`
    `--review` and `aggregate`) plus `agy_worker.py review --executor api` automatically fail
    over across remaining active/keyed providers (`grok` via OpenCode xAI OAuth subscription
    or `XAI_API_KEY` -> `deepseek` -> `glm` -> `minimax`). In the OpenCode
    TUI, switching to another healthy provider or `opencode/glm-5.3-flash-free` continues
    seamlessly.
- **Active API & retired direct providers**: legacy `openai`, `anthropic`, `gemini`, and `codex`
  entries were removed from active `config/headless.json` defaults in favor of `agy`,
  subscription/keyed `grok` (`Grok-4.7` via OpenCode `xai` OAuth or `XAI_API_KEY`), and active
  prepaid API fallbacks (`deepseek` / `DeepSeek-V4-Pro`, `glm` / `GLM-5.3`, `minimax` / `MiniMax-M3`).

For API-backed Q&A, application profiles default to raw collection:

```bash
python3 skills/moa/moa_runner.py --platform cursor --models agy,deepseek,minimax --coordinator-model current --task-id example -- 'Question to compare'
```

Pass `--models agy` for zero-marginal-API-cost second opinions via `Orchestrator (Carbon)`.
Installed platform entrypoints infer their platform automatically even when `--platform` is
omitted. Use `--platform headless` when an explicit paid API aggregator step is wanted.

## Evidence-based analysis

The [shared MoA workflow](shared/moa-workflow.md#evidence-based-collaboration) applies common
evidence rules to independent workers, the optional single reviewer (`--review`), and host
synthesis. Synthesis preserves unresolved disagreements and does not count repeated claims as
independent evidence. No live tools or web access are assumed in offline worker prompts.

The [four-stage experiment proposal](shared/evidence-review-proposal.md) describes independent
answers → cross-review → revision → synthesis (`--cross-review`) using local evidence checks.

## Coding execution and records

`--platform <name>` identifies the coordinating host (`codex`, `claude`, `gemini`, `opencode`,
`cursor`, or `headless`); executors are **agy**, **claude-local**, and **claude-cloud**,
recorded separately. Delegated implementation follows the
[shared coding workflow](shared/auto-workflow.md).

The `agy` executor provides disposable shallow worktrees, a default-deny PreToolUse guard
(`agy_guard.py`), macOS `sandbox-exec` enforcement (`sandbox.sb`, network disabled), orphan
process cleanup, cross-family read-only diff review (`review --executor auto` for cross-pool
`agy` + `--executor api` failover, or `review --executor agy` in `--mode plan` / `--executor api`),
and whole-patch gates. Applying requires the reviewed SHA (`--sha`), full sandboxed
verification (`verify --full`) against the current `HEAD`, clean target files, and protected
path checks. Control directories including `.git`, `.claude`, `.codex`, `.opencode`,
`.cursor`, `.gemini`, `.agents`, `.github`, `.vscode`, `.idea`, `venv`/`.venv`, and
`node_modules` are protected case-insensitively at any depth.

Runs identify the platform, coordinator model (`current` when omitted), task ID, and
executor. API records live under `skills/moa/runs/`; coding records and the run ledger remain
under `skills/auto/runs/` and `runs.jsonl`. All run artifacts and `.env` files are ignored
by Git.

`agy` supports bounded same-session transport recovery (`--network-retries 0..2`, default `1`),
preserving partial patches while failing closed on quota, auth, or safety/review flags.

## Native Claude Code CLI & Claude Cloud Bridge

- **Native CLI (`claude_local.py`)**: uses first-party Claude Pro/Max allowance via a scoped
  MCP file/test broker ([native CLI workflow](shared/claude-local-workflow.md)), with local
  sandbox `verify --full` and `--sha` apply gates.
- **Cloud Bridge (`claude_cloud.py`)**: supports `prepare`, `observe-funding` (single-use
  non-stale panel observation), `launch` / `attach` / `send`, and sandbox-verified local
  patch import ([cloud workflow](shared/cloud-workflow.md)).

```bash
python3 skills/auto/claude_cloud.py prepare --repo "$PWD" --brief '<brief.md>' --platform cursor
python3 skills/auto/claude_cloud.py attach '<run-id>' --session '<Claude-cloud-session-URL>'
python3 skills/auto/claude_cloud.py status '<run-id>'
```

## Offline verification

```bash
python3 skills/moa/test_runner.py
python3 skills/moa/test_evidence_review.py
python3 skills/auto/test_guard.py
python3 skills/auto/test_worker.py
python3 skills/auto/test_cloud.py
python3 skills/auto/test_local.py
python3 skills/auto/test_recovery.py
python3 tests/test_install.py
python3 tests/test_platforms.py
```

Runner tests mock providers; worker tests use mock CLIs and temporary git repos; installer
tests use isolated temporary homes; sandbox tests require macOS `sandbox-exec`. None of these
suites make live paid model calls.
