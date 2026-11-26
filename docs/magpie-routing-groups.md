# Magpie Routing Groups & Claude Magpie Runbook

Sanitized, reproducible configuration for running **Claude Desktop (`Claude Magpie`)** on top of local **Magpie** (`127.0.0.1:3425`) with `$0` subscription pools (`grok`, `agy-cli`, `codex`), automatic 3-tier difficulty routing, and Apple Silicon (`arm64`) stability safeguards.

---

## 1. Two-Group Strategy (Daily vs. Heavy)

| Group | Target Usage | Gemini Pool Usage | Effort Safety (`max`-safe) |
|---|---|---|---|
| **`group/daily-light`** | 80% daily coding (`effort: high`, `ultracode: off`) | **0 Gemini in normal operation** (Grok + Sonnet 5.5 + Codex only) | Easy/Subagent/Compact locked to `:low`; Medium locked to `:high`; Hard/Plan/`120k+` unlocked |
| **`group/orchestrator`** | Heavy architecture, multi-module refactors, deep debugging (`effort: max`, `ultracode: on`) | Uses `agy-cli` Gemini 4 flagship (`Hydrogen:high`, `Neon:xhigh`) | Same 3-tier protection; removed blanket `effort >= xhigh` rule so `max` does not waste flagship quota on trivial turns |

### Escalation & Failover from `Daily Light` to `Orchestrator`
- **On-demand one-message escalation** (rule #3): include `!heavy`, `#heavy`, `换强模型`, `升级模型`, `切强模型`, `用强模型`, or `上旗舰` anywhere in a prompt to route that turn directly to `group/orchestrator` without switching dropdowns. Leading `/` (e.g. `/heavy`) and bare `升级` are intentionally avoided to prevent Claude Code slash-command interception and false triggers on prompts like “升级依赖” or “升级建筑”.
- **Automatic tail failover** (member #8): if every non-Gemini model in `group/daily-light` is rate-limited, exhausted, or past context capacity, Magpie falls back seamlessly to `group/orchestrator`.

---

## 2. Reproducible CLI Setup

> Note: Always use `@500k` variants for SuperGrok (`grok/grok-4.7@500k`, `grok/grok-4.7-build-fast@500k`) when serving Claude Code / long-context clients, otherwise Magpie skips 256K Grok models once conversation length passes 256K.

### A. `group/orchestrator` (Flagship 3-Tier, `max`-Safe)

```bash
MAGPIE="/Applications/magpie.app/Contents/MacOS/magpie"

"$MAGPIE" group add "Orchestrator" \
  models=agy-cli/gemini-4-hydrogen:high,codex/gpt-6.2-sol:high,grok/grok-4.7@500k:high,agy-cli/gemini-4-neon:xhigh,codex/gpt-6.2-astra,agy-cli/claude-opus-5-5,grok/grok-4.7-build-fast@500k:low,agy-cli/gemini-4-carbon:low,agy-cli/gemini-3.8-flash:low \
  routing=order stays=turn

"$MAGPIE" group set orchestrator \
  note="Plan-Execute Orchestrator (\$0, max-safe 3-tier): Easy/Subagent/Compact->Grok Fast:low/Carbon:low/Flash:low; Execute->Hydrogen:high/Sol:high/Grok 4.7:high; Plan/Hard/120k+->Neon XHigh/Astra/Opus 5.5"

"$MAGPIE" group rule add orchestrator use=agy-cli/gemini-3.8-flash:low,grok/grok-4.7-build-fast@500k:low,agy-cli/gemini-4-carbon:low compact
"$MAGPIE" group rule add orchestrator use=grok/grok-4.7-build-fast@500k:low,agy-cli/gemini-4-carbon:low,agy-cli/gemini-3.8-flash:low when=subagent
"$MAGPIE" group rule add orchestrator use=agy-cli/gemini-4-neon:xhigh,codex/gpt-6.2-astra,agy-cli/claude-opus-5-5 when="system contains plan mode"
"$MAGPIE" group rule add orchestrator \
  use=agy-cli/gemini-4-neon:xhigh,codex/gpt-6.2-astra,agy-cli/claude-opus-5-5 \
  intent="architecture design, multi-step planning, deep root-cause debugging, security review, or code review" \
  classifier=grok/grok-4.7-build-fast@500k,agy-cli/gemini-3.8-flash
"$MAGPIE" group rule add orchestrator \
  use=grok/grok-4.7-build-fast@500k:low,agy-cli/gemini-3.8-flash:low,agy-cli/gemini-4-carbon:low \
  intent="quick question, simple explanation, copy or comment edit, typo fix, or trivial single-file tweak"
"$MAGPIE" group rule add orchestrator \
  use=agy-cli/gemini-4-neon:xhigh,codex/gpt-6.2-astra,agy-cli/claude-opus-5-5 \
  when="tokens >= 120k"
"$MAGPIE" group rule classifier orchestrator grok/grok-4.7-build-fast@500k,agy-cli/gemini-3.8-flash
```

### B. `group/daily-light` (0 Gemini Normal Operation + `Orchestrator` Escalation & Failover)

```bash
MAGPIE="/Applications/magpie.app/Contents/MacOS/magpie"

"$MAGPIE" group add "Daily Light" \
  models=grok/grok-4.7-build-fast@500k:high,agy-cli/claude-sonnet-5-5,codex/gpt-6-luna:high,grok/grok-4.7@500k,codex/gpt-6.2-astra,grok/grok-4.7-build-fast@500k:low,codex/gpt-6-luna:low,group/orchestrator \
  routing=order stays=turn

"$MAGPIE" group set daily-light \
  note="Daily Light (\$0, max-safe 3-tier, 0 Gemini normal): Easy/Subagent/Compact->:low; Medium->:high; Hard/Plan/120k+->Sonnet 5.5/Grok 4.7/Astra; !heavy/换强模型 or failover->Orchestrator"

"$MAGPIE" group rule add daily-light use=grok/grok-4.7-build-fast@500k:low,codex/gpt-6-luna:low compact
"$MAGPIE" group rule add daily-light use=grok/grok-4.7-build-fast@500k:low,codex/gpt-6-luna:low when=subagent
"$MAGPIE" group rule add daily-light \
  use=group/orchestrator \
  when='message matches (!heavy|#heavy|升级模型|换强模型|切强模型|用强模型|上旗舰)'
"$MAGPIE" group rule add daily-light use=agy-cli/claude-sonnet-5-5,grok/grok-4.7@500k,codex/gpt-6.2-astra when="system contains plan mode"
"$MAGPIE" group rule add daily-light \
  use=agy-cli/claude-sonnet-5-5,grok/grok-4.7@500k,codex/gpt-6.2-astra \
  intent="architecture design, multi-step planning, deep root-cause debugging, security review, or complex cross-file refactoring" \
  classifier=grok/grok-4.7-build-fast@500k
"$MAGPIE" group rule add daily-light \
  use=grok/grok-4.7-build-fast@500k:low,codex/gpt-6-luna:low \
  intent="quick question, simple explanation, copy or comment edit, typo fix, or trivial single-file tweak"
"$MAGPIE" group rule add daily-light \
  use=agy-cli/claude-sonnet-5-5,grok/grok-4.7@500k,codex/gpt-6.2-astra \
  when="tokens >= 120k"
"$MAGPIE" group rule classifier daily-light grok/grok-4.7-build-fast@500k
```

### C. Bind to Claude Magpie & Verify

```bash
MAGPIE="/Applications/magpie.app/Contents/MacOS/magpie"
"$MAGPIE" claude-desktop group/daily-light
"$MAGPIE" group orchestrator
"$MAGPIE" group daily-light
```

---

## 3. Operational Safeguards & macOS Apple Silicon Notes

- **Avoid recursive `Antigravity` → `Magpie` → `agy-cli` loops**: Keep native Antigravity Desktop and `agy` CLI connected directly to Google (`"$MAGPIE" antigravity default`). Otherwise `agy` enters `Enterprise Gateway` mode (`~/.gemini/config/config.json`) and breaks standalone `agy_worker.py` / `moa_runner.py` model lists.
- **Account isolation & concurrency hygiene**:
  - Do not bind a primary Google account into third-party OAuth bridge plugins or rotate multiple Google accounts on the same machine. When signing a secondary account into `@magpie-community/opencode-agy-cli-auth`, explicitly choose **"Add another Google account"** (isolated directory under `~/.local/state/magpie-agy-bridge/accounts/`) instead of the default method (which re-imports the system Keychain `agy` account).
  - Lower `agy-cli` **Concurrency** in Magpie UI (**Providers → `agy-cli` → Concurrency**) from default `16` to **`3`–`4`** (note: idle warm `agy acp` processes up to `AGY_BRIDGE_MAX_PROCS=16` stay asleep at `0%` CPU for prompt-cache reuse and do not issue concurrent network requests).
  - Keep Magpie bound strictly to loopback (`127.0.0.1:3425`); never expose it via LAN/tunnel without strong auth.
- **Apple Silicon (`arm64`) Rosetta freeze fix for `Claude Magpie.app`**:
  - When `Claude.app` updates to a universal (`x86_64` + `arm64`) binary, macOS may launch the shell-script wrapper `~/Applications/Claude Magpie.app/Contents/MacOS/claude-magpie` under Rosetta `x86_64`, causing ~200% CPU stalls, downloading `darwin-x64` Claude Code, and breaking `/usr/bin/git` (`libxcrun.dylib` missing `x86_64`).
  - Patch the launcher's `exec` line to force native `arm64`:
    ```sh
    exec /usr/bin/arch -arm64 "$app/Contents/MacOS/$exe" --user-data-dir="$dir" "$@"
    ```
    Then remove any partial `darwin-x64` download under `~/Library/Application Support/Claude-Magpie-3p/claude-code/` and relaunch `Claude Magpie.app`.
