# 委派 Provider 坑点

## 症状
```
Cannot resolve delegation provider 'deepseek': No usable credentials found
```

## 原因
`delegation.provider` 字段指的是 **API 网关**（如 `openai-api` = 硅基流动），而非模型厂商（如 `deepseek`）。当主模型走硅基流动中转站时，DeepSeek 的 API Key 未在 `.env` 中配置（或被注释），Hermes 找不到对应凭证。

## 解决方案
```bash
# 将委派的 provider 设为与主模型相同的 API 网关
hermes config set delegation.provider openai-api

# 模型名保持不变
hermes config set delegation.model deepseek-ai/deepseek-v4-flash
```

## 通用规则
`delegation.provider` 必须与 `model.provider` 指向**同一个 API 网关**（除非你在 `.env` 中为多个网关分别配置了凭证）。