# Grok Build 安装与配置

## 安装方式

### npm（推荐 — 国内用户首选）

```bash
npm i -g @xai-official/grok
grok --version  # 验证: 应为 0.2.103+
```

优点：不需要 VPN、不需要 OAuth 认证。
headless 模式直接调用自定义模型 API（如硅基流动 DeepSeek），零阻塞。

### 直装（海外 / VPN 用户）

```powershell
# Windows PowerShell
irm https://x.ai/cli/install.ps1 | iex
```

```bash
# macOS / Linux
curl -fsSL https://x.ai/cli/install.sh | bash
```

直装版本首次启动需浏览器 OAuth 认证 x.ai 账号。

## 模型配置模板 (~/.grok/config.toml)

### 方案 A：DeepSeek 官方（推荐 — 最便宜，国内直连）

```toml
[models]
default = "deepseek-v4"

[model.deepseek-v4]
model = "deepseek-chat"
base_url = "https://api.deepseek.com/v1"
name = "DeepSeek V4 (官方)"
api_key = "<DeepSeek 官方 API Key>"
context_window = 128000

[session]
auto_compact = true

[memory]
enabled = false
```

优势：≈硅基 1/4 价格、国内直连无需 VPN、API 稳定。

### 方案 B：硅基流动（备用 — 注意与博客 Kanban 共用额度池，有欠费风险）

```toml
[models]
default = "siliconflow-v4"

[model.siliconflow-v4]
model = "deepseek-ai/DeepSeek-V4-Pro"
base_url = "https://api.siliconflow.cn/v1"
name = "DeepSeek V4 Pro (硅基)"
api_key = "<硅基流动 API Key>"
context_window = 128000
```

### 强制禁用 Grok 内建记忆

```toml
[memory]
enabled = false
```

这是架构红线：记忆主权归 Hermes，不让 Grok 产生独立记忆导致双脑分叉。
Adapter 启动时还会额外设 `GROK_MEMORY=0` 环境变量作双重保障。

## 验证安装

```bash
# 1. 版本检查
grok --version

# 2. 模型列表（应看到自定义模型 + 内置 grok-build）
grok models

# 3. API 连通性测试
grok -m deepseek-v4 -p "1+1=?" --yolo --output-format json
# 正常应返回: {"text":"2",...,"stopReason":"EndTurn"}
# 401 = key 无效; 403 = 余额不足; timeout = 网络不通
```

## 常见故障

| 错误 | 原因 | 解决 |
|---|---|---|
| 401 Authentication Fails | API Key 过期/无效 | 更新 config.toml 的 api_key |
| 403 Insufficient Balance | 账户欠费 | 充值硅基或切换模型 |
| 连接超时 | 网络不通 | 硅基/DeepSeek 国内应直连，如超时检查 DNS |
| `grok: command not found` | npm 全局路径未在 PATH | `npm root -g` 确认路径，或重开终端 |
