# SiliconFlow (硅基流动) Provider Pattern

## Why
硅基流动提供 OpenAI 兼容 API，价格便宜，支持 DeepSeek V3/V4/R1、Qwen 全系列。是中国用户绕过 DeepSeek 官方余额/充值问题的最佳替代方案。

## Configuration

### config.yaml
```yaml
model:
  default: deepseek-ai/DeepSeek-V4-Pro
  provider: openai                      # ⚠️ 是 openai，不是 deepseek！
  base_url: https://api.siliconflow.cn/v1
```

### .env
```
OPENAI_API_KEY=sk-xxx你的硅基流动key
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
```

**关键：provider 必须设为 `openai`，因为硅基流动是 OpenAI 兼容 API。**

## 推荐模型

| 用途 | 模型 ID |
|------|---------|
| 最强对话 | `deepseek-ai/DeepSeek-V4-Pro` |
| 快速/便宜 | `deepseek-ai/DeepSeek-V4-Flash` |
| 稳定版 | `deepseek-ai/DeepSeek-V3.2` |
| 推理专用 | `deepseek-ai/DeepSeek-R1` |
| 视觉 | `Qwen/Qwen3-VL-8B-Instruct` |

列出所有可用模型：
```bash
curl -s https://api.siliconflow.cn/v1/models \
  -H "Authorization: Bearer <key>" \
  | python -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

## 切换命令

```bash
# DeepSeek 官方 → 硅基流动
hermes config set model.provider openai
hermes config set model.default deepseek-ai/DeepSeek-V4-Pro
hermes config set model.base_url https://api.siliconflow.cn/v1
hermes gateway restart    # 必须在独立终端执行！

# 硅基流动 → DeepSeek 官方
hermes config set model.provider deepseek
hermes config set model.default deepseek-chat
hermes config set model.base_url ""
hermes gateway restart
```

## 视觉模型单独配置

```yaml
auxiliary:
  vision:
    provider: openai
    model: Qwen/Qwen3-VL-8B-Instruct
    base_url: https://api.siliconflow.cn/v1
```

## 常见错误

### HTTP 402: Insufficient Balance
DeepSeek 官方 API 余额不足。切换到硅基流动即可。

### "No usable credentials found for provider 'deepseek'"
.env 中 DEEPSEEK_API_KEY 未设置。如已切换到 openai provider，可忽略（自动用 OPENAI_API_KEY）。