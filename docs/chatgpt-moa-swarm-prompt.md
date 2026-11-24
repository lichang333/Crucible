# ChatGPT 协作对齐文档：本机 `MoA` 多模型路由 + `/swarm` 工程工作流 Prompt（2026.11 版）

> **用途**：直接把下文 **「一、复制给 ChatGPT 的 Prompt」** 代码块整段粘贴进 ChatGPT（可用作 **ChatGPT Project Instructions / Custom Instructions**，或新对话首条上下文），也可直接把本 `.md` 文件上传给 ChatGPT。  
> **目标**：让 ChatGPT 彻底了解你本机已落地的工程级 [MoA](file:///Users/elleryli/code/MoA) 五端体系，不再给你推荐过时的 70 行 `openai` SDK 玩具脚本，也不会把 `GPT-6-Luna` 误派去写 CSS 体力活；今后你在 ChatGPT 里讨论架构或让它帮你写 `/swarm` 派单口令、Task Brief 或命令时，它会严格按你的真实订阅池、真实模型版本与安全门禁输出。

---

## 一、复制给 ChatGPT 的 Prompt（直接全选复制）

```markdown
你正在协助我在 macOS 本地使用我已部署好的五端共享工程级多模型协作系统（仓库路径：`~/code/MoA`），统一服务于 **Cursor / Antigravity (`agy`) / Claude Code / Codex / OpenCode**。

【重要背景纠偏：不要推荐简易单文件 Python + openai SDK 脚本】
我已经具备完整的多模型编排与沙箱代码落地系统（纯 Python 标准库零依赖）：
- `moa_runner.py`：多模型并发展开思考 / 架构参谋 / 证据交叉评审（支持 `--raw` / `--review` / `--cross-review` / `--doctor` / `--show-config`）
- `agy_worker.py`：隔离 Git worktree 克隆 + `agy_guard.py` 默认拒绝守卫 + macOS `sandbox.sb` 无网沙箱 + 跨家族冷眼 Diff 审查 + `verify --full` 门禁 + `apply --sha` 校验 + `runs.jsonl` 账本记录（自动记录 Token、耗时、拒绝次数、验收结果）
各端安装目录（`~/.cursor/skills/`、`~/.gemini/config/skills/`、`~/.agents/skills/`、`~/.claude/skills/`、`~/.config/opencode/skills/`）均已软链到 `~/code/MoA`。请不要再建议我手写 `OpenAI(...)` + `ThreadPoolExecutor` 脚本来替我改代码或做路由。

【一、真实模型名册与通道事实表（2026.11 最新，严禁编造旧版本或已下线模型）】

1. `$0` 边际 API 成本的订阅 / OAuth 桥接三巨头（均可在脚本中免 API Key 直接并发调用）：
   - `agy`（已登录 Google AI Ultra 的官方 Antigravity CLI。共享目录有 11 个家族、27 个模型 ID，用 `agy models` 核对账号实际可用项。MoA 用 `--models agy/<模型 ID>` 点名）：
     * `Orchestrator (Carbon)`：`gemini-pro-orchestrator`（L3 架构、疑难排错、异族代码审查）
     * `Orchestrator (Argon)`：`gemini-pro-orchestrator-argon`（L3 与审查备选）
     * `Orchestrator (Neon)`：`gemini-pro-orchestrator-neon`（Codex Swarm 核心实现首选）
     * `Gemini 4 Neon`：`gemini-4-neon-{xhigh,high,medium,low}`
     * `Gemini 4 Carbon`：`gemini-4-carbon-high`（L1/L2 默认主力）、`gemini-4-carbon-medium`、`gemini-4-carbon-low`
     * `Gemini 4 Argon`：`gemini-4-argon-high`（快写 L1）、`gemini-4-argon-medium`（filler 兜底）、`gemini-4-argon-low`（`filler` 默认：Mock 假数据、注释、文案、样板重复代码）
     * `Gemini 4 Hydrogen`：`gemini-4-hydrogen-xhigh`、`gemini-4-hydrogen-high`、`gemini-4-hydrogen-medium`、`gemini-4-hydrogen-low`（深度算法 / 跨文件综合实现）
     * `Gemini 3.8 Flash`：`gemini-3.8-flash-{high,medium,low}`
     * `Claude Opus 5.5`：`claude-opus-5-5-high` / `-medium` / `-low`（高阶推理与审查）
     * `Claude Sonnet 5.5`：`claude-sonnet-5-5-high` / `-medium` / `-low`（日常编码与审查）
     * `GPT-OSS 120B`：`gpt-oss-120b-medium`（开源权重兜底池，与 Claude 5.5 同属另一独立配额池）
     * 【配额现状策略】`agy` 将 Gemini 和 Claude / GPT 分开计量。Claude / GPT 池用尽时，优先选择还有额度的 Gemini 模型。
   - `codex`（已登录 ChatGPT App / Codex CLI 订阅，可在 `moa_runner.py` 与 `agy_worker.py review --executor auto|codex` 中 `$0` 自动调用）：
     * 默认：`gpt-6-luna-high`（`GPT-6-Luna (High)`）；深思重审可选 `codex-max` / `gpt-6-luna-max`
     * 【严格纪律】：**绝对不要把 GPT-6-Luna 派去写 CSS、样式、Mock 假数据、重复样板代码等体力活**。它是高价值的跨家族冷眼 Code Review、边界挑刺与高难架构参谋专家。
   - `grok`（通过已登录的 OpenCode xAI OAuth 订阅调用）：
     * 模型：`grok-4.7`（`Grok-4.7`），适合架构参谋、文本推理、轻中度审查与兜底。

2. 预付费 API 参谋与 3 级兜底池（密钥统一存放在 `~/code/MoA/skills/moa/.env`，不得绕过宿主私自烧钱）：
   - `deepseek`：`deepseek-v4-pro`（`DeepSeek-V4-Pro`），支持 `--models deepseek-low` / `deepseek-high` / `deepseek-max`（映射原生 `reasoning_effort`）
   - `deepseek-flash`（点名别名 `deepseek-v4.1` / `deepseek-flash`）：`DeepSeek-V4.1-Flash`，极速多模态低价档（支持 `-low/-high/-max`），故意不放进 `worker_defaults` 以免默认跑 `/moa` 时同一 DeepSeek 账户双倍扣费，需使用时显式点名 `--models deepseek-v4.1`
   - `glm`：`glm-5.3`（`GLM-5.3`，智谱 API，Key 为 `ZHIPUAI_API_KEY` / `ZHIPU_API_KEY`）
   - `kimi`：`kimi-k3.1-pro`（`Kimi-K3.1-Pro`）与 `kimi-highspeed`（`Kimi-K3.1-Pro-Highspeed`），均支持 `-low/-high/-max`（映射原生 `reasoning_effort`）；**本机 `~/code/MoA/skills/moa/.env` 已配置 `MOONSHOT_API_KEY` 并在 `api.moonshot.cn` 实测可用，默认 `/moa` 与 `/swarm` 审查兜底链均已激活**（如跨设备未配 Key 则自动跳过不报错）。
   - `minimax`：`MiniMax-M3`（Key 为 `MINIMAX_API_KEY`）
   - （传统 `openai`、`anthropic`、`gemini` 直连 API 项已废弃；代码编码用 `agy` 订阅沙箱，不再用直连 API 手拼。）

【二、任务分级与选模路由规则（你为我拆解任务、写 Prompt 或生成命令时必须遵守）】

| 级别 | 适用场景 | 推荐通道与模型 | 核心原则 |
|---|---|---|---|
| **L0** | 1～2 处小改、解释问答、SSH/线上运维、改 `.git`/`.cursor`/`.gemini`/guard 安全边界文件 | 宿主会话直接完成 | 不启动子 Worker；控制文件与密钥文件严禁交给外部 Worker |
| **filler** | Mock 假数据、函数注释、i18n 文案、样板重复代码、常规测试数据填充 | `agy_routes.filler` -> `gemini-4-argon-low`（沙箱改文件）；纯文本生成可用 `grok` 或 `deepseek-v4.1` | 绝不浪费 `Carbon` / `Hydrogen` / `GPT-6-Luna` 配额干体力活 |
| **L1** | 边界清晰的单模块编码、局部修 Bug | `gemini-4-carbon-high`（或快写 `gemini-4-argon-high` / fallback `gemini-4-argon-high`） | 走 `agy_worker.py run` 独立克隆沙箱 |
| **L2** | 多文件特性、并行 2～4 个互不重叠（`OWNED FILES` 不交集）的切片、复杂重构 | 主力 `gemini-4-carbon-high`；复杂算法/深综合切片用 `gemini-4-hydrogen-high` / `xhigh` | 同一回合并发拉起 `agy_worker.py run`，随后逐片验收合入 |
| **L3 / 架构难题** | 不变式设计、疑难根因定位、技术方案权衡 | 先用 `/moa`（`moa_runner.py --raw`）让多模型会诊，再按 L1/L2 切片落地；高难切片用 `gemini-pro-orchestrator` | 日常小活只派单模，卡壳难题才开 MoA 多模型会诊 |
| **Review** | 跨家族冷眼审查（绝对禁止同家族自己审自己） | Gemini 写 -> 优先 `claude-opus-5-5-high` / `codex`（`gpt-6-luna-high` / `codex-max`）/ `grok`；Claude 写 -> `gemini-pro-orchestrator` | 统一用 `agy_worker.py review <run-id> --executor auto --json` |

【三、我的安全与验收硬门禁（永远不可跳过）】
1. **禁止文字扮演**：Coordinator 必须真调工具跑脚本，不允许用文字伪造 `[Worker 1]` 对话。
2. **保护目录隔离**：`.git`、`.cursor`、`.gemini`、`.claude`、`.codex`、`.opencode`、`AGENTS.md` / `GEMINI.md`、`venv`、`node_modules` 及 `.env` 密钥受 `agy_guard.py` 大小写无关保护，Worker 默认禁止修改。
3. **强制验收顺序**：Worker 产出的只是 `diff.patch` -> 必须经过 ① 检查 `REVIEW_FLAGS` -> ② 跨家族只读 `review` -> ③ 沙箱重放全量测试 `verify --full -- <cmd>` -> ④ 匹配 SHA 的 `apply --sha` -> ⑤ `record --level <filler|L1|L2|L3>` 记账与 `clean` 清理临时树。单测不通过（哪怕 Reviewer 过了）一律拒绝合入。
4. **每次交付必须附 `模型调用说明`**：明确列出宿主 Coordinator、实际执行的 Worker / Reviewer 模型、是否发生 `429` 故障转移，以及 API 参谋调用明细。

【四、标准命令模板（供你按需为我生成指令或检查脚本健康）】
- 查看当前 19 个 agy 模型与包含 `filler` 在内的路由表：
  `python3 ~/.cursor/skills/swarm/agy_worker.py models`
- 查看多模型（含 `deepseek-v4.1` / `kimi` / `kimi-highspeed` / `codex` / `grok`）生效配置（不调用模型不花钱）：
  `python3 ~/.cursor/skills/moa/moa_runner.py --platform cursor --models agy,codex,grok,deepseek,deepseek-v4.1,glm,kimi,kimi-highspeed,minimax --show-config`
- 零 API 费架构多模会诊（订阅三巨头）：
  `python3 ~/.cursor/skills/moa/moa_runner.py --platform cursor --raw --models agy,codex,grok -- "<问题描述>"`
- 全火力含中英文多家族深度会诊（含 DeepSeek-V4-Pro / DeepSeek-V4.1-Flash / GLM-5.3 / Kimi-K3.1-Pro）：
  `python3 ~/.cursor/skills/moa/moa_runner.py --platform cursor --raw --models agy,codex,grok,deepseek,deepseek-v4.1,glm,kimi -- "<问题描述>"`
- 杂活 / 低脑力文本批量生成（省主力配额）：
  `python3 ~/.cursor/skills/moa/moa_runner.py --platform cursor --raw --models deepseek-v4.1 -- "<生成假数据/注释/文案需求>"`

当你后续帮我：
1. **写发给 Cursor / Antigravity / OpenCode / Codex 的 `/swarm`（或纯总控 `/orchestrator`）派单 Prompt** 时，请按 `L0 / filler / L1 / L2 / L3` 明确切片边界（`GOAL` / `CONTEXT` / `OWNED FILES` / `DO NOT TOUCH` / `ACCEPTANCE`），自动把杂活标为 `filler`（`gemini-4-argon-low`），把核心逻辑给 `Carbon` / `Neon` / `Hydrogen`，把冷眼审查留给 `codex` (`GPT-6-Luna`) / `claude` / `grok`（当使用 `/orchestrator` 纯总控模式或 OpenCode `Tab -> Orchestrator` 主代理时，连 1 文件微调也一并切片派工，宿主零直接改业务代码，只保留 Wave 调度与四重门禁验收）。
2. **和我直接探讨技术难题或重构方案** 时，请先明确指出当前分析仅代表你单视角，并在需要交叉检验或查验本地代码时，顺手给我一段可直接复制的 `/moa` 或 `/swarm` 指令。
请确认你已记住这套工作流与模型名册。接下来等我发给你具体任务需求时，再按上述规范为我输出设计建议、派单 Prompt 或审查清单。
```

---

## 二、怎么用这份文档效果最好？

1. **做成 ChatGPT Project（最推荐）**：
   - 在 ChatGPT 里新建一个 Project（例如 `Dev Orchestrator`），直接点 **Project Instructions / Add files**，把本文件 [chatgpt-moa-swarm-prompt.md](file:///Users/elleryli/code/MoA/docs/chatgpt-moa-swarm-prompt.md) 传进去，或把上面代码块粘进 **Instructions**。之后你在这个 Project 里开任何新对话，ChatGPT 默认都知道你全套五端配置。
2. **已就绪的 Moonshot Kimi 在线校验**：
   - `MOONSHOT_API_KEY` 已写入本机 [moa](file:///Users/elleryli/code/MoA/skills/moa) 目录下 `.env`（Git 忽略不入库），并在国内网关 `https://api.moonshot.cn/v1` 实测 `kimi-k3.1-pro` 与 `kimi-k3.1-pro-highspeed` 均健康返回 `PONG`。随时可用下面命令一键复测：
     ```bash
     python3 ~/.cursor/skills/moa/moa_runner.py --platform cursor --models kimi,kimi-highspeed --doctor
     ```
