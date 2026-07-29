# DeepSeek Model Names (as of 2026-07)

## Current API Model IDs

| Model ID | Type | Status |
|----------|------|--------|
| `deepseek-v4-pro` | Full flagship (thinking-enabled) | ✅ Current |
| `deepseek-v4-flash` | Fast general-purpose (thinking-enabled) | ✅ Current |
| `deepseek-chat` | Legacy alias → non-thinking mode of v4-flash | ⚠️ Deprecated 2026/07/24 |
| `deepseek-reasoner` | Legacy alias → thinking mode of v4-flash | ⚠️ Deprecated 2026/07/24 |

*Source: https://api-docs.deepseek.com/* — "Your First API Call" table*

## Hermes Support Status

Hermes `.py` code already knows all four models across these subsystems:

| Subsystem | File | Models listed |
|-----------|------|---------------|
| Context lengths | `agent/model_metadata.py:268-271` | `deepseek-v4-pro` (1M), `deepseek-v4-flash` (1M), `deepseek-chat` (1M), `deepseek-reasoner` (1M) |
| Curated model lists | `hermes_cli/models.py:381-384` | All four under `"deepseek"` key |
| OpenRouter catalog | `hermes_cli/models.py:64-65` | `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash` |
| OpenCode Go/Zen | `hermes_cli/models.py:449-451, 475-476` | All four + `deepseek-v4-flash-free` |
| Pricing data | `agent/usage_pricing.py:450-471` | `deepseek-chat`, `deepseek-reasoner`, `deepseek-v4-pro` |
| Reasoning timeouts | `agent/reasoning_timeouts.py:74-75` | `deepseek-v4-flash` (600s), `deepseek-v4-pro` (600s) |

## How to Use in Hermes

```bash
# Direct DeepSeek provider (no aggregator prefix needed)
hermes -m deepseek-v4-pro --provider deepseek

# Via OpenRouter
hermes -m deepseek/deepseek-v4-pro --provider openrouter

# In-session switch
/model deepseek-v4-pro

# Permanent config
hermes config set model.default deepseek-v4-pro
hermes config set model.provider deepseek
```

## Migration Path (pre-2026/07/24)

Users still on `deepseek-chat` / `deepseek-reasoner` should migrate:

1. `deepseek-chat` → `deepseek-v4-flash` (same non-thinking behavior)
2. `deepseek-reasoner` → `deepseek-v4-pro` (full reasoning, or `deepseek-v4-flash` for thinking mode since v4-flash also supports thinking)

Both v4 models support the `thinking` / `reasoning_effort` parameter via the OpenAI-compatible API (`extra_body={"thinking": {"type": "enabled"}}`).
