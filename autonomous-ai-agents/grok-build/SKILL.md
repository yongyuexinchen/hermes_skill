---
name: grok-build
description: "Use when delegating coding/execution tasks (build features, create files, refactor, run tests, repo understanding) to the Grok Build CLI (xAI `grok`) as Hermes' execution agent. Hermes plans and remembers; Grok executes. Grok supports custom OpenAI-compatible models — default uses DeepSeek official API (`deepseek-chat`) for ¼ the cost of SiliconFlow, no VPN needed for inference. Do NOT use for planning, knowledge management, or when grok binary/auth is unavailable — fall back to codex or claude-code."
version: 0.3.1
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Grok-Build, xAI, Execution, Delegation, Custom-Models]
    related_skills: [codex, claude-code, opencode, knowledge-system-architecture]
---

# Grok Build 执行代理

把叶子级编码任务委派给 xAI 的 `grok` CLI（headless 模式）。分工红线：**Hermes 负责规划、记忆、验收；Grok 只负责执行**。

## When to Use

- 建/改工程文件、实现功能、重构、批量修 bug
- 在 repo 内跑测试并根据结果迭代
- 需要独立进程隔离的长编码任务

**不要用于**：任务规划（Hermes Planner 的事）、知识/记忆管理、只读快问快答（Hermes 原生工具更快）。

## Installation & Setup

两行搞定（国内无需 VPN）：

```bash
npm i -g @xai-official/grok        # npm 版免 OAuth，headless 直接调自定义模型
grok --version                       # 验证: 应 ≥ 0.2.103
```

`~/.grok/config.toml` 配置自定义模型后即可使用。详见 `references/install.md`。
配置模板副本 → `templates/config.toml`。

> 直装版（`irm https://x.ai/cli/install.ps1 | iex`）需 VPN + 首次 OAuth，npm 版推荐国内用户。

**首次使用**需复制 adapter 配置到 skill 根目录（adapter 读取 `<skill_dir>/config.yaml`，不从 assets 读取）：

```bash
cp <skill_dir>/assets/config.yaml <skill_dir>/config.yaml
```

调用前先跑体检，失败则降级 codex/claude-code：
```
terminal(command="python <skill_dir>/scripts/grok_adapter.py doctor")
```

## Position in Hermes Architecture

```
User
  ↓
Hermes Core
  ↓
Phase -1: Architecture (Hermes, no Grok)
  ├── ADR: 记录为什么这样设计
  ├── Provider Interfaces: 定义契约 (Protocol)
  └── architecture.md: 单源真理
  ↓
Planner ── 任务分类 ──┐
  ↓                   │
Skill Router          │ 非编码类 → 原生工具 / 其他 Skills
  ↓                   │
grok-build Skill ─────┘
  ↓  subprocess (进程边界 = 架构边界)
grok -p "<任务书>" -m deepseek-v4 --output-format json GROK_MEMORY=0
  ↓  Grok 内部自治: goal_planner → 工具循环 (建文件/改代码/跑测试)
Execution Result (envelope JSON)
  ↓  Adapter 后处理: git diff 核验 + session_id + usage
Hermes Memory ← 耐久结论
```

> **Phase -1 是关键**: 在委派 Grok 之前，Hermes 先完成架构决策记录(ADR) + Provider 接口定义。接口就是契约 — Grok 只能在契约内实现，不能越界。详见 `references/architecture-phase.md`。
> 三层架构（Application → Core ← Storage）的强制模式和测试注入见 `references/layered-architecture-pattern.md`。
> Knowledge OS 特定模式（Tool Server、Relation Resolver、Self-Bootstrap）见 `references/knowledge-os-patterns.md`。

## Input Format

Hermes 侧以结构化参数下发任务（adapter 翻译为 headless CLI 旗标）：

```json
{
  "task": "实现最小RAG测试程序：内存向量库+关键词检索+3条断言，pytest全绿",
  "context": "Python 3.11, faiss-cpu + sentence-transformers, E:/scratch/rag-demo",
  "constraints": "禁用外部API; 断言用assert不用unittest; 完成≤500字总结",
  "workspace": "E:/scratch/rag-demo"
}
```

| 字段 | 必需 | 说明 |
|---|---|---|
| `task` | ✓ | 目标 + 可核验的验收标准（Hermes 事后按此核验） |
| `context` | | 技术栈、已有代码约定、项目约束（注入 `--rules`） |
| `constraints` | | 硬性限制：禁外部API、特定测试框架等 |
| `workspace` | ✓ | 绝对路径：Windows 用 `E:/x` 或 `E:\\x`，MSYS `/e/x` 传给原生 exe 会解析失败 |

## 调用范式

### 一次性任务

```
terminal(command="python <skill_dir>/scripts/grok_adapter.py run --task '<任务书>' --workdir 'E:/path/to/repo' --policy guarded", timeout=920)
```

任务书必须包含：① 目标 ② 可核验的验收标准（如"pytest 全绿"）③ 技术栈约束 ④ "完成后用≤500字总结改动与关键决策"。

### 长任务（>5 分钟）

```
terminal(command="python <skill_dir>/scripts/grok_adapter.py run --task '...' --workdir '...'", background=true, notify_on_complete=true)
```

### 直接调用（绕过 adapter — 备用路径）

当 adapter 环境异常时（如 PATH 问题、Python 依赖缺失），可直接 terminal 调 grok：

```
terminal(command="grok -p '<任务书>' -m deepseek-v4 --output-format json --cwd 'E:/path' --max-turns 30 --no-auto-update", background=true, notify_on_complete=true)
```

跳过 adapter 时注意：
- 无 git 核验包裹层 —— 需自行 `git diff` 验收
- 无 `GROK_MEMORY=0` 环境变量注入 —— 确认 `~/.grok/config.toml` 中 `[memory] enabled = false`
- background + notify_on_complete 是关键组合，避免长时间阻塞


envelope 里的 `session_id` 可续接：

```
terminal(command="python <skill_dir>/scripts/grok_adapter.py resume --session <sid> --task '测试第3条失败了，修复它' --workdir '...'")
```

## 策略档位（--policy）

| 档位 | 效果 | 场景 |
|---|---|---|
| `readonly` | 只读工具白名单 | 代码讲解、review |
| `guarded`（默认） | 可写代码；rm -rf/sudo/网络抓取被 deny | 日常开发 |
| `auto` | `--yolo` 全自动 | 一次性 scratch 目录 |

## 自定义模型（关键 — 零 xAI 成本）

Grok 开源的是执行框架；模型推理可替换为任何 OpenAI 兼容端点。
**优先使用 DeepSeek 官方 API**（国内直连、最便宜 ≈ 硅基 1/4 价格）。
硅基流动作为备用（注意欠费风险 — 与博客 Kanban 共用额度池）。
配置指南 → `references/install.md`，DeepSeek 配置模板 → `references/deepseek-config.md`。

headless 调用必须加 `-m deepseek-v4`，否则默认走 xAI 内置模型产生费用。

## 批量任务模式（DRBCV 知识库建卡等）

当需要对大量源文件执行同类操作（如"从 45 篇转录稿建知识卡"）：

1. **验证批**：选 3-5 个源文件先跑，确认卡格式、类型判定正确后 → 全量
2. **拆批**：**5-7 篇/批是最优窗口**（>10 篇易 Cancelled，<4 篇固定开销占比过高），`--max-turns 30-35`
3. **并行提交**：多批用 `background=true + notify_on_complete=true` 并行跑
4. **Cancelled 处理**：`stopReason=Cancelled` 且卡数 << 源文件数 → 批次太大，拆为 5-6 篇小批重跑
5. **max_turns_reached**：仍有产出（部分卡片已写入），按未覆盖源文件补批
6. **DeepSeek 缓存红利**：源文件重复读取时 `cache_read_input_tokens` 可达数百万（几乎零成本），批量越大越省。实测 107 篇→81 卡总增量仅 ~440K tokens（≈ ¥0.44）

源文件为 `.docx` 时先 `python-docx` 转 `.md`（文本抽取）。注意：转录稿中"如图所示"的内容（协议时序图、状态机、拓扑图）会丢失——这些属于图片，LLM 看不到。高图片引用文件（如 CSMA/CA 有 6 处图）需用视觉模型补扫或人工对照原稿。

详见 `references/batch-construction.md`。

## Common Pitfalls

1. **workdir 用 Windows 绝对路径**（`E:/x` 或 `E:\\x`），MSYS 风格 `/e/x` 传给原生 exe 会解析失败
2. Grok 记忆必须保持关闭 —— adapter 强制 `GROK_MEMORY=0`；不要在 `~/.grok/config.toml` 里打开
3. **npm 版无需 OAuth**：headless + 自定义模型直接可用；仅 xAI 内置模型或直装版需 OAuth
4. `--max-turns` 打满时 `stop_reason=max_turns_reached` → 用 resume 续做，不要重开
5. cost 字段缺失≠免费（OAuth 路径常不标价）；用 DeepSeek API 时以 usage tokens 记账
6. **每次 headless 调用必须 `-m deepseek-v4`**，否则默认走 xAI 内置模型产生费用
7. Hermes 技能名用**连字符** `grok-build`，不要用下划线 `grok_build`（skill_manage 会拒绝）
8. **Windows subprocess `.CMD` 陷阱**：```
subprocess.run(['grok', ...])``` 在 Windows 上会因为 `CreateProcess` 不识别 `.CMD` 文件扩展名而抛 `FileNotFoundError`，即使 `shutil.which('grok')` 能找到它。Adapter (v0.2.1+) 已修复——用 `shutil.which()` 解析完整路径后再传 subprocess。旧版本如需绕过：直接 terminal 调用 `grok -p "..."`（bash shell 原生处理 `.CMD` 解析）。详见 `references/windows-subprocess.md`。
8.5 **Grok ≠ delegate_task 模型名格式**：`delegate_task`（Hermes 内建委派）和 Grok CLI 独立运行时，DeepSeek 官方 API 要求的模型名格式不同：
| 调用方式 | 模型名格式 | 配置位置 |
|---------|-----------|---------|
| Grok CLI (`grok -m`) | `deepseek-v4-pro` | `~/.grok/config.toml` → `[model.xxx].model` |
| `delegate_task` | `deepseek-v4-pro` | `~/.hermes/config.yaml` → `delegation.model` |
| Hermes 主模型 | `deepseek-ai/DeepSeek-V4-Pro`（完整路径） | `~/.hermes/config.yaml` → `model.default` |

**最容易踩的坑**: 把 Hermes 主模型格式（`deepseek-ai/DeepSeek-V4-Pro`）复制到 delegation.model 或 Grok config，DeepSeek API 会返回 400 "supported model names are deepseek-v4-pro or deepseek-v4-flash"。修复：delegation + Grok 都用短名。
8.6 **DeepSeek 官方 API 余额不足**：`HTTP 403: account balance insufficient` 表示 DeepSeek 官方 key 欠费。切换到 SiliconFlow（`api.siliconflow.cn/v1`）作为替代。注意 SiliconFlow 模型名也是短格式。Hermes 主模型切 provider 用 `hermes config set model.provider siliconflow` + 改 `model.default`。`subprocess.run(['grok', ...])` 在 Windows 上会因为 `CreateProcess` 不识别 `.CMD` 文件扩展名而抛 `FileNotFoundError`，即使 `shutil.which('grok')` 能找到它。Adapter (v0.2.1+) 已修复——用 `shutil.which()` 解析完整路径后再传 subprocess。旧版本如需绕过：直接 terminal 调用 `grok -p "..."`（bash shell 原生处理 `.CMD` 解析）。详见 `references/windows-subprocess.md`。
9. **批量任务拆分过小无效**：3-5 篇源文件时启动 Grok 的固定 token 开销可能超过收益 → 先验证再批量
10. **跳过 Phase -1 直接派活**：不先定义 ADR + Provider 接口就派 Grok 写代码 → Grok 自行做架构决策 → 紧耦合、不可测、无边界。正确的顺序：Hermes 先做 ADR + 接口定义（Phase -1），再把接口作为 task context 交给 Grok 实现。详见 `references/architecture-phase.md`。
11. **脚手架不委派 Grok**：`mkdir` + `touch` + 空文件创建是 shell 级操作，Hermes 用 `terminal` 2 秒完成。Grok 为此启动完整 LLM session（≥60 秒 + 消耗 token）是纯浪费。Grok 的推理能力应留给代码实现、测试、修复——而不是创建目录。
12. **Grok 可能忽略你指定的类名/字段名**：任务书明确写 `Card(type=discriminant)`，Grok 可能输出 `Entry(type=concept)`。决策矩阵：

| Grok 偏离 | 判定 | 动作 |
|-----------|------|------|
| 类名不同但 Protocol 合规 | 接受 | 命名是风格问题，不值得修改所有引用 |
| 缺少必需字段 | 拒绝 | resume 修复，这是功能缺陷 |
| type 枚举值不同 | 视情况 | 如果用户明确指定了新枚举值 → 修正。如果是 Grok 自创 → 接受（只要逻辑正确） |
| 多出额外字段（如 pinned） | 修正 | 多余字段会进入序列化，造成格式污染 |

验收标准始终是：**Protocol 合规 + 测试全绿 > 命名匹配**。

13. **Grok 自报"全绿"不一定真实**：Grok envelope 声称 `142 passed`，但 Hermes 独立复跑后才能确认。Grok 可能：
14. **重复函数定义静默覆盖**：Python 中同名函数定义在同一作用域，后定义者静默覆盖前者，无警告。症状：`set_adapter()` 设置全局变量，但 `_get_adapter()` 永远返回新实例——因为第一个 `_get_adapter()`（含注入检查）被第二个 `_get_adapter()`（直接 `build_adapter()`）覆盖。排查：`grep -n "def funcname" file.py` 检查是否重复定义。
15. **Click 自动转换下划线为连字符**：`def list_cards` → CLI 命令变成 `list-cards`。测试中调用 `CliRunner.invoke(cli, ["list_cards"])` 会报 "No such command"。正确：`["list-cards"]`。
16. **Card 构造函数 __post_init__ 会拒绝无效数据**：当 Tool/Adapter 需要传递未验证的 Card 给 `engine.validate_card()` 时，`Card(type="bad")` 在构造阶段就抛 ValueError。绕过：`card = Card.__new__(Card); card.type = "bad"; ...`，在 `__post_init__` 执行前手动赋值字段。

    - 修改了不在 scope 内的文件（如 `core/models/card.py`、`pyproject.toml`）
    - 写了测试验证自己的实现，但这些测试与 Hermes 的预期不同
    - 缺少关键方法（如 `find_related_cards`、`validate_card`、异常类）
    - Hermes 后续修改（如 `get()` 返回 None → raise CardNotFoundError）会打破 Grok 写的测试
    **必须执行**: `pytest` 独立复跑 → `execute_code` 检查方法完整性 → 修复被 Hermes 修改打破的测试 → 架构合规检查。

## Post-Grok Inspection 工作流

每次 Grok 完成后，Hermes 必须执行这个 checklist（不是信任 envelope）：

```
1. pytest 全量复跑（独立 Python，不通过 adapter）
2. execute_code 扫描关键方法/类是否存在
3. 检查 scope 外文件是否被意外修改 (git diff --stat)
4. 架构合规: core 层是否引入了 Web/CLI/DB import
5. 对照任务书检查: 每个要求的文件/方法/测试是否到位
6. Hermes 自行修补缺失 → 测试可能因修补而失败 → 修复测试
```

详见 `references/post-grok-inspection.md`。

## Grok 偏离后的 Hermes 修复模式

Grok 完成任务后常有三种偏离需 Hermes 手动修复：

### 模式 A: 缺少方法/类
症状: 测试全绿但检查发现缺少 `find_related_cards`、`validate_card`、异常类等。
修复: Hermes 直接创建缺失文件/方法，不重新委派 Grok。缺失的代码量通常 < 50 行。

### 模式 B: 返回值语义不同
症状: `get()` 返回 `None` 而非 raise `CardNotFoundError`。
影响: 下游测试断言 `is None` 会失败。
修复: 改方法签名 → `raise CardNotFoundError` → 更新所有受影响的测试。

### 模式 C: API 注入架构修复
症状: CLI 直接 `import storage.markdown/storage.index` 绕过适配器。
修复: 在 adapter 层加 `build_adapter()` 工厂函数 → CLI 改为 `from adapters.agent import build_adapter` → 加 `set_adapter()` 注入函数供测试使用。
原则: Application 层永远不直接 import Storage 具体实现。

### 模式 D: sed 破坏 Python 缩进
**绝对禁止**用 `sed -i` 批量替换 Python 文件。缩进被破坏后语法错误难以批量修复。
正确做法: 用 `execute_code` 运行 Python 脚本做精确的字符串替换。
```python
content = open(path).read()
content = content.replace("old", "new")
open(path, "w").write(content)
```

### 模式 E: CLI 测试注入
症状: CLI 层需要 mock Engine，但不能 import Storage 实现（架构红线）。
修复: adapter 层提供 `set_adapter()` + `_get_adapter()` 全局注入模式，测试通过 fixture 注入 mock adapter。详见 `references/cli-testing-injection.md`。

## Verification Checklist

- [ ] doctor 全绿后才 run
- [ ] envelope.ok == true 且 stop_reason == EndTurn
- [ ] files_changed 与任务书预期一致；测试类验收由 Hermes 复跑确认
- [ ] 耐久结论已写 memory，session_id 已留存
- [ ] 架构合规检查（`references/arch-compliance-check.md`），确认 Core 层未越界 import
- [ ] 方法完整性检查：用 `grep "def "` 对照任务书逐一核实
- [ ] Hermes 修改后复跑全量 pytest（修补可能打破 Grok 写的测试）
