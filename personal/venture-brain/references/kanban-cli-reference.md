# Kanban CLI 速查 — Venture Brain 工作流

> 2026-07-20 实战踩坑记录。Hermes 的 kanban 子命令与直觉有微妙差异。

## 核心命令

### 创建任务
```bash
hermes kanban --board venture create "<任务描述>" --assignee <profile>
```
- `--assignee` 可选值：`vb-orchestrator | vb-researcher | vb-gh-explorer | vb-architect | vb-analyst | vb-librarian`
- 创建后状态：`ready`，等待 dispatcher 分配

### 查看看板
```bash
hermes kanban --board venture list
```

### 查看所有看板
```bash
hermes kanban boards list
```

### 查看任务详情
```bash
hermes kanban --board venture show <task_id>
```

---

## 任务管理（踩坑区）

### 阻止任务 ⚠️
```bash
# ✅ 正确：reason 是位置参数，不是 --reason
hermes kanban --board venture block <task_id> "阻止原因" --kind needs_input

# ❌ 错误：不存在 --reason 参数
hermes kanban --board venture block <task_id> --reason "原因"  # 报错
```

`--kind` 可选：
- `needs_input` — 需要人工介入，任务进入 blocked 状态
- `dependency` — 等待依赖完成，保持 todo
- `capability` — 能力不足
- `transient` — 临时失败

### 添加注释 ✅
```bash
hermes kanban --board venture comment <task_id> "注释内容"
```
- 注释会追加到任务上，Agent 理论上会读到
- ⚠️ 但如果 Agent 已在执行中且速度快，可能不会读取 mid-execution 的注释
- 对 `running` 状态的任务加注释：不一定生效，但值得尝试

### 编辑任务 ⚠️
```bash
# edit 只用于编辑结果，不是编辑描述
hermes kanban --board venture edit <task_id> --result "结果内容" --summary "摘要"
```
- **不能用来修改任务描述** — 创建时确定描述，后续只能通过 comment 追加
- 没有 `--description` 参数

### 指定任务（从 triage → ready）
```bash
hermes kanban --board venture specify <task_id>
```
- 只对 `triage` 状态的任务有效
- 对 `running`/`todo`/`ready` 状态执行会报错：`task is not in triage`

### 归档任务
```bash
hermes kanban --board venture archive <task_id>
```

---

## ❌ 不存在的命令
- `hermes kanban update` — 不存在，用 `edit --result`
- `hermes kanban context` — 不存在，用 `comment`
- `hermes kanban --board venture update <task_id> --description "..."` — 不存在

---

## Kanban Worker profiles 缺少 provider 配置 → 秒崩（🔴 2026-07-28 实战）

**现象**：`hermes kanban swarm --worker "researcher:..."` 创建的任务，Worker 在 < 1 分钟内全部 blocked（crashed: `pid not alive`），dispatch 无法 spawn 有效进程。

**根因**：Kanban profiles（researcher/vb-researcher/vb-gh-explorer 等）只是任务分配槽位，需要在 profile 配置中绑定 provider/model 才能执行。当前环境这些 profile 缺少 provider 配置。

**诊断**：
```bash
hermes profile show researcher          # 看 provider 字段
hermes kanban diagnostics               # 看所有 profile 状态
hermes kanban show <task_id>            # 看具体任务的 runs 日志
```

**替代方案**：用 `delegate_task` 代替 Kanban Swarm——子 Agent 继承当前会话的 provider/model，无需额外 profile 配置。适合 ≤3 路并行研究。

---

## 状态流转（完整）

```
created → ready → (dispatch) → running → (complete) → done
                                    ↓
                                 blocked → (unblock) → triage → (specify) → ready
                                    
triage → (specify) → ready

todo 状态的特殊性：
- 无法直接 block（报错：cannot block）
- 无法 specify（报错：task is not in triage）
- 只能 archive 或等它被 dispatch → running 后再 block
```

---

## Git Clone 后台僵死（新增）

vb-gh-explorer 用 `background=true` 开 git clone 时的典型故障：

**症状：** `.git/` 创建成功，文件未 checkout，`tmp_pack_*` + `shallow.lock` 锁住目录，`rm -rf` 报 `Device or resource busy`。

**修复：**
```bash
# 1. Windows taskkill 杀 git
/c/Windows/System32/taskkill.exe /F /IM git.exe

# 2. 等锁释放
sleep 3

# 3. 用新目录名重克（避免旧锁残留）
git clone --depth 1 <url> "<path>_new"

# 4. 完成后重命名
mv "<path>_new" "<path>"
```

**预防：** 大仓库用 `notify_on_complete=true` + `timeout=300`，不要无超时裸跑。

**代理优化（国内 Clash，🆕 2026-07-20）：**
```bash
# 克隆前必须设置（否则大仓库如 SillyTavern 会 RPC 断流）
git config --global http.postBuffer 524288000   # 500MB
git config --global http.version HTTP/1.1        # Clash 对 HTTP/2 差

# 超大仓库加 --single-branch
git clone --depth 1 --single-branch <url> <path>
```
**大仓库不要并行克隆** — 逐一排队，避免代理被打满全部超时。

**克隆后验证（🆕 2026-07-20）：**
```bash
# 确认不是空骨架
find "<path>" -type f -not -path '*/.git/*' | wc -l   # 必须 > 0
```

## vb-architect「假解剖」验收（🆕 2026-07-20）

vb-architect 可能声称读了源码，实际用 GitHub API / raw 文件糊弄。验收硬性标准：

- [ ] 输出路径 = D:/Contents/research/（不是 E:/research/）
- [ ] 包含 ≥3 个项目的目录树
- [ ] 包含 ≥10 处具体代码引用（文件路径 + 行号）
- [ ] 不包含 `raw.githubusercontent.com` URL
- [ ] 没有类似 `hermes kanban show` 的摘要式描述

不合格时：废弃该任务产出 → 创建新 architect 任务 → comment 中明确 `read_file` 本地路径。

---

## 典型干预流程

当 orchestrator 走了默认全流程模板，但实际只需要部分 Phase：

```bash
# 1. 阻止不需要的任务
hermes kanban --board venture block t_xxx "本轮不需要市场扫描，上轮已完成。" --kind needs_input

# 2. 给正在跑的任务加注释重定向
hermes kanban --board venture comment t_yyy "【重定向】只解剖 3 个项目：A/B/C。不要做宽泛扫描。"

# 3. 手动创建遗漏的任务
hermes kanban --board venture create "Phase 3: 架构解构" --assignee vb-architect
```

---

## 状态流转

```
created → ready → running → done
                    ↓
                  blocked (需人工介入)
```
