# DeepSeek 官方 API 配置模板

> Grok Build 的 ~/.grok/config.toml 配置，使用 DeepSeek 官方 API（api.deepseek.com）
> 优势：国内直连无需 VPN、价格 ≈ 硅基流动 1/4、支持 deepseek-chat + deepseek-reasoner

## 完整模板

```toml
[models]
default = "deepseek-v4"

[model.deepseek-v4]
model = "deepseek-chat"
base_url = "https://api.deepseek.com/v1"
name = "DeepSeek V4"
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
context_window = 128000

[model.deepseek-reasoner]
model = "deepseek-reasoner"
base_url = "https://api.deepseek.com/v1"
name = "DeepSeek R1"
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
context_window = 128000

[session]
auto_compact = true

[memory]
enabled = false
```

## 关键字段说明

| 字段 | 值 | 说明 |
|---|---|---|
| `base_url` | `https://api.deepseek.com/v1` | OpenAI Chat Completions 兼容端点，国内直连 |
| `model` | `deepseek-chat` | DeepSeek V4 模型 ID（非思维链） |
| `model` | `deepseek-reasoner` | DeepSeek R1 推理模型（复杂任务，带 reasoning_tokens） |
| `context_window` | 128000 | DeepSeek 上下文窗口，自动压缩触发阈值 |
| `[memory] enabled` | `false` | **红线**：记忆主权归 Hermes，禁止双脑 |

## 与其他提供商的对比

| 提供商 | 端点 | 国内直连 | 相对价格 | 备注 |
|---|---|---|---|---|
| DeepSeek 官方 | api.deepseek.com | ✓ | 1x | 推荐 |
| 硅基流动 | api.siliconflow.cn | ✓ | ~4x | 欠费风险（与博客 Kanban 共用额度） |
| xAI 内置 | api.x.ai | ✗ 需 VPN | ~3x | OAuth 认证后可走 API key 模式 |

## 注意

- DeepSeek Key 取自 Hermes `.env` 的 `DEEPSEEK_API_KEY`；需确认未欠费
- 每次 headless 调用必须加 `-m deepseek-v4`，否则默认走 xAI 内置模型（计费）
- `deepseek-reasoner` 会产生 `reasoning_tokens`，成本高于 `deepseek-chat`
