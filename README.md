# MoA — Shared Multi-Agent Workflows for Antigravity, OpenCode, Cursor, Claude Code, and Codex

Separate platform instructions, one shared implementation. The current host session
triages tasks and integrates changes, while subscription-backed workers (**Google AI Ultra**
via the signed-in `agy` CLI,
ChatGPT-authenticated **`codex`** (`GPT-6-Luna (High)` / `gpt-6-luna-high` default plus
`codex-max` / `gpt-6-luna-max` at zero API cost, auto-preferring newer
`/Applications/ChatGPT.app` bundled `codex` over stale Homebrew binaries), bridged
**`grok`** (`Grok-4.7` via signed-in OpenCode xAI OAuth only), optional prepaid APIs
`glm` (`GLM-5.3`), `deepseek` (`DeepSeek-V4-Pro`,
plus `deepseek-v4.1` / `deepseek-flash` for `DeepSeek-V4.1-Flash` & `deepseek-max` effort),
`kimi` (`Kimi-K3.1-Pro` + `kimi-highspeed` & `kimi-max` effort when `MOONSHOT_API_KEY`/`KIMI_API_KEY` is set),
and `minimax` (`MiniMax-M3`), and optional Claude Code subscription bridges) provide
parallel Q&A analysis, isolated coding slices, and cross-family cold-eyes verification.

| Workflow | Purpose | Execution |
|---|---|---|
| `/moa` | Multi-model Q&A and analysis | Read-only `agy` (`Orchestrator (Neon)`) + `codex` (`GPT-6-Luna (High / Max)` via ChatGPT subscription) + `grok` (OpenCode xAI OAuth only) + configured API answers (`glm`/`deepseek`/`minimax`); current-session synthesis |
| `/auto` | Delegated single-module coding | Isolated `agy` sandbox worker (or native Claude Code CLI / Claude cloud bridge); cross-family review + local `verify --full` & `apply --sha` |
| `/swarm` / `/swarms` | Parallel multi-file orchestration | Codex prefers guarded `agy` implementation on explicit `/swarm` coding tasks and reviews in the current session. Antigravity / `agy` exposes `/swarms` (`always_on` rule, leaving `/swarm` for Antigravity's built-in Native Swarm UI), OpenCode (`default_agent: swarm`), and Cursor (`alwaysApply` rule + `swarm-coordinator`) use isolated `agy` slices with cross-family verification and quota failover |

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
platforms/codex/skills/             Codex moa, auto and swarm skill entrypoints
platforms/claude/skills/            Claude moa and auto skill entrypoints
platforms/gemini/skills/            Antigravity / Gemini moa, auto and swarms skill entrypoints
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
./install.sh --platform codex        # only Codex (moa, auto, swarm)
./install.sh --platform claude       # only Claude
./install.sh --platform gemini       # only Gemini / agy (moa, auto, swarms skills + always_on rule; alias: --platform agy)
./install.sh --platform opencode     # only OpenCode (moa, auto, swarm skills + swarm agent)
./install.sh --platform cursor       # only Cursor (moa, auto, swarm skills + agent + alwaysApply rule)
```

Install targets:
- **Codex**: `~/.agents/skills/{moa,auto,swarm}`. Explicit `/swarm` coding tasks
  prefer the guarded worker in [the Codex profile](config/codex.json), with
  review in the current session. Parallel research uses native subagents.
- **Claude**: `~/.claude/skills/{moa,auto}`
- **Gemini / Antigravity (`agy`)**: `~/.gemini/config/skills/{moa,auto,swarms}` plus
  `~/.gemini/config/rules/swarm-coordinator.md` (`trigger: always_on`, active across `agy` CLI,
  Antigravity App, and Antigravity IDE without typing `/swarms`, leaving `/swarm` free for
  Antigravity's built-in Native Swarm UI, with an automatic exemption for
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
python3 skills/moa/moa_runner.py --platform codex --models agy/gemini-4-neon-high --show-config
python3 skills/auto/agy_worker.py models --json
python3 skills/auto/agy_worker.py models --live
```

These commands inspect configuration without calling models. `--live` asks `agy`
which models are offered to the signed-in account.
- [The shared catalog](config/headless.json) lists Gemini, Orchestrator, Claude 5.5,
  and GPT-OSS variants. Use exact IDs with `agy_worker.py run --model` or `--models agy/<model-id>` in MoA.
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
    failover -> ChatGPT-authenticated `codex` `gpt-6-luna-high` at `$0` spend -> `grok` /
    `--executor api`, or explicit `--model codex-max` / `gpt-6-luna-max`).
  - **Tier 3 (prepaid API balance/token exhausted or key expired)**: `/moa` (`moa_runner.py`
    `--review` and `aggregate`) plus `agy_worker.py review --executor api` automatically fail
    over across configured providers. Grok uses OpenCode xAI OAuth. The prepaid
    choices include `deepseek`, `glm`, `kimi`, and `minimax`. In the OpenCode
    TUI, switching to another healthy provider or `opencode/glm-5.3-flash-free` continues
    seamlessly.
- **Active subscription & API providers**: `agy` (Google AI Ultra), `codex` (`GPT-6-Luna (High)`
  / `gpt-6-luna-high` default plus `codex-max` / `gpt-6-luna-max` via ChatGPT subscription,
  auto-preferring `/Applications/ChatGPT.app` bundled `codex` over stale `/opt/homebrew/bin/codex`),
  subscription `grok` (`Grok-4.7` via OpenCode `xai` OAuth only), and active
  prepaid API fallbacks (`deepseek` / `DeepSeek-V4-Pro`, `deepseek-v4.1` / `DeepSeek-V4.1-Flash`
  + `deepseek-max`, `glm` / `GLM-5.3`, `kimi` / `Kimi-K3.1-Pro` + `kimi-highspeed` / `kimi-max`, `minimax` / `MiniMax-M3`). Legacy direct `openai`, `anthropic`, and `gemini` API entries remain retired.

For API-backed Q&A, application profiles default to raw collection:

```bash
python3 skills/moa/moa_runner.py --platform cursor --models agy,deepseek,minimax --coordinator-model current --task-id example -- 'Question to compare'
```

Pass `--models agy` for zero-marginal-API-cost second opinions via `Orchestrator (Neon)`.
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
`agy` + ChatGPT `codex` `gpt-6-luna-high` + `--executor api` failover, or `review --executor agy`
in `--mode plan` / `--executor codex` with `gpt-6-luna-high` or `gpt-6-luna-max` / `--executor api`),
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
