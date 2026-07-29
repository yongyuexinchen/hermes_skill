# 辅助视觉模型配置

## 硅基流动 (SiliconFlow)

国内可用，OpenAI 兼容接口。

### 配置
```bash
hermes config set auxiliary.vision.provider openai
hermes config set auxiliary.vision.model Qwen/Qwen3-VL-8B-Instruct
hermes config set auxiliary.vision.base_url https://api.siliconflow.cn/v1
```

### API Key
在 `.env` 中设置：
```
OPENAI_API_KEY=sk-xxxxxxxx  # 硅基流动的 key（sk- 开头）
```

### 可用视觉模型
查询命令：
```bash
curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
  "https://api.siliconflow.cn/v1/models" | \
  python -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[]) if 'VL' in m['id']]"
```

已验证可用：`Qwen/Qwen3-VL-8B-Instruct`、`Qwen/Qwen3-VL-32B-Instruct`

### 生效
`/reload` 后生效。验证：发一张图 → `vision_analyze` 能返回描述即成功。

## Google Gemini（海外用户）

```bash
hermes config set auxiliary.vision.provider google
hermes config set auxiliary.vision.model gemini-2.0-flash
# .env: GOOGLE_API_KEY=xxx
```

## DeepSeek 不支持视觉

DeepSeek 模型（v4-pro/v4-flash）不支持 vision_analyze，必须配置辅助视觉模型。
