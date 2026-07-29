# Venture Brain Profile 配置配方

> 本文件记录 vb-* profile 从零创建到可用的完整步骤和已知坑。
> 最后更新：2026-07-20，首次部署后

## 一步创建脚本

```bash
# 1. 创建 6 个 profiles（克隆自 default）
for p in vb-orchestrator vb-researcher vb-gh-explorer vb-architect vb-analyst vb-librarian; do
  hermes profile create "$p" --clone-from default --description "Venture Brain - $p"
done

# 2. 切换到 DeepSeek 官方 API（关键：default 用硅基流动，克隆后需替换）
DEEPSEEK_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
DEEPSEEK_URL="https://api.deepseek.com/v1"
DEEPSEEK_MODEL="deepseek-v4-pro"

for p in vb-orchestrator vb-researcher vb-gh-explorer vb-architect vb-analyst vb-librarian; do
  hermes config set --profile "$p" model.provider deepseek
  hermes config set --profile "$p" model.base_url "$DEEPSEEK_URL"
  hermes config set --profile "$p" model.api_key "$DEEPSEEK_KEY"
  hermes config set --profile "$p" model.default "$DEEPSEEK_MODEL"
done

# 3. 创建 Kanban Board
hermes kanban boards create venture

# 4. 创建工作区
mkdir -p E:\\research
mkdir -p "D:/DRBCV-Knowledge/Venture/"{Industry,OpenSource,Architecture,Product,Opportunity,FailureCase}

# 5. 重启 gateway（让 dispatcher 加载新配置）
hermes gateway restart
```

## 已知坑

### 坑 1：克隆 profile 继承硅基流动配置

**症状：** 新创建的 vb-* profile 报 HTTP 403 `balance insufficient`

**原因：** `hermes profile create --clone-from default` 完整复制了 default 的 provider (custom/siliconflow)、base_url、api_key。硅基流动余额不足。

**修复：** 步骤 2 的三项配置必须全部覆盖。

### 坑 2：模型名格式不兼容

**症状：** HTTP 400 `The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed deepseek-ai/DeepSeek-V4-Pro`

**原因：** DeepSeek 官方 API 用短名 `deepseek-v4-pro`，硅基流动用带前缀的 `deepseek-ai/DeepSeek-V4-Pro`。

**修复：** `model.default` 必须设为 `deepseek-v4-pro`。

### 坑 3：Dispatcher 缓存旧配置

**症状：** 磁盘上的 config.yaml 已修正，但 task 仍报旧的 HTTP 错误码。

**原因：** Dispatcher 是常驻进程，启动时读取配置，后续不自动重读。

**修复：** `hermes gateway restart` 或重启 hermes。若 task 已 crashed，建新 task。

### 坑 4：Board 不存在

**症状：** `kanban: board 'venture' does not exist`

**修复：** `hermes kanban boards create venture`

## DRBCV 系列 Profile（5 个，Phase 5 卡片生成用）

```bash
for p in scanner merger card-writer linker reviewer; do
  hermes profile create "$p" --clone-from default --description "DRBCV - $p"
  hermes config set --profile "$p" model.provider deepseek
  hermes config set --profile "$p" model.default deepseek-v4-pro
  hermes config set --profile "$p" model.base_url "https://api.deepseek.com/v1"
  hermes config set --profile "$p" model.api_key "sk-a81594ed1583450c8a7c832fccb66767"
done

# 启动 gateway（让 dispatcher 能调度这些 profile）
for p in scanner merger card-writer linker; do
  hermes gateway start --profile "$p"
done
```

### 坑 6：DRBCV 任务无 --parent 导致并行执行

**症状：** merger/card-writer/linker/reviewer 与 scanner 同时启动，card-writer 找不到 scanner 的中间文件而 blocked。

**原因：** `hermes kanban create` 不加 `--parent` 时所有 task 无依赖关系，dispatcher 并行派发。

**修复：** 下游 task 创建时必须指定 parent：
```bash
# Scanner 无依赖
hermes kanban --board drbcv-ai create "扫描: industry.md" --assignee scanner
# Merger 等 scanner
hermes kanban --board drbcv-ai create "合并" --assignee merger --parent <scanner_id>
```

### 坑 7：card-writer 找不到 merged_concepts.md

**症状：** card-writer 报 `merged_concepts.md 文件未找到`，blocked。

**原因：** merger 的中间产出写在工作区，card-writer 不知道路径。DRBCV 各 Agent 之间缺少共享的中间文件约定。

**缓解：** card-writer 会自愈——直接读取源文件而非依赖 merger 产出。但最好在 task prompt 中明确写出中间文件路径。
