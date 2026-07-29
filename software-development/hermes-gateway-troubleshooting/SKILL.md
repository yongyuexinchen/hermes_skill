---
name: hermes-gateway-troubleshooting
description: Diagnose Hermes gateway failures and provider errors.
version: 1.1.0
---

# Hermes Gateway Troubleshooting

Systematic workflow for diagnosing and fixing Hermes gateway issues — startup failures, provider errors, and platform connection problems.

## When to Load

- Gateway fails to start or keeps restarting
- Messaging platform (WeChat/微信, Telegram, etc.) not responding
- API errors from the gateway's model provider

## Diagnostic Workflow

### 1. Check status
```bash
hermes gateway status
```

### 2. Read logs (priority order)

| Log | Contents |
|-----|----------|
| `gateway.log` | Timeline: startups, platform connections, messages, shutdowns |
| `gateway-stdio.log` | Console output: API errors, auth failures, warnings |
| `gateway-exit-diag.log` | Start/exit with PID, timestamps, clean vs crash |
| `errors.log` | All errors across sessions (large, tail it) |

All logs under `~/.hermes/logs/`.

### 3. Find the error
```bash
tail -50 ~/.hermes/logs/gateway-stdio.log
```

Key patterns:
- `HTTP 402: Insufficient Balance` → provider out of credits
- `HTTP 401/403` → bad API key
- `No usable credentials for provider 'X'` → .env missing key
- `Unauthorized user` → platform allowlist/pairing
- `Failed to resolve CDP endpoint` → browser not running (cosmetic, not fatal)

### 4. Verify platform connection
```bash
grep "weixin\|connected\|disconnected" ~/.hermes/logs/gateway.log | tail -20
```

If a platform shows as not connected, run `hermes gateway setup` to reconfigure it.

## Common Fixes

### HTTP 402 — Provider Balance Exhausted

The most common cause of gateway "failures": provider ran out of credits. **But verify before switching** — HTTP 401 (Unauthorized) means the key is dead, not the balance. A dead key and an empty balance produce identical symptoms (failed API calls, silent degradation).

**Diagnose first (direct API call, bypasses Hermes config):**
```python
import json, urllib.request

# DeepSeek balance check
req = urllib.request.Request('https://api.deepseek.com/user/balance')
req.add_header('Authorization', 'Bearer sk-xxx')
print(json.loads(urllib.request.urlopen(req, timeout=10).read()))
# → {"is_available":true,"balance_infos":[{"total_balance":"48.80",...}]}

# SiliconFlow user info (HTTP 401 = dead key, not balance)
req = urllib.request.Request('https://api.siliconflow.cn/v1/user/info')
req.add_header('Authorization', 'Bearer sk-xxx')
urllib.request.urlopen(req, timeout=10)  # 401 = bad key; 200 = check totalBalance
```

**Fix:** Switch to a provider with working credentials. Full provider-switching guide: skill `hermes-custom-provider`.

Quick switch to DeepSeek official:
```bash
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-pro
hermes config set model.base_url ""
hermes config set model.api_key ""              # clear residual custom key!
hermes gateway restart  # from SEPARATE terminal!
```

### Gateway Keeps Restarting

Check `gateway-exit-diag.log` for rapid start/stop cycles. Usually caused by:
1. API error on every startup → fix the error first
2. Windows Scheduled Task firing too frequently → check `taskschd.msc`

### Gateway Restart Blocked

Error: "Refusing to restart the gateway from inside the gateway process"

**Fix:** Open a NEW terminal window, run `hermes gateway restart`.
Or kill + let Scheduled Task auto-restart: `taskkill /PID <pid> /F`

## Platform-Specific Notes

### WeChat / 微信 (Weixin)

- Connection endpoint: `https://ilinkai.weixin.qq.com`
- Account data stored at `~/.hermes/weixin/`
- Pairing/allowlist managed via `hermes gateway setup`

## Windows-Specific Notes

- Gateway runs as a **Windows Scheduled Task** (name: `Hermes_Gateway`)
- `hermes gateway restart` MUST run from a separate terminal — blocked inside the gateway process
- `taskkill /PID <pid> /F` as escape hatch; Scheduled Task auto-restarts
- Log paths: `$HOME/AppData/Local/hermes/logs/`
- `%1 不是有效的 Win32 应用程序` in errors.log = LSP binary incompatible (cosmetic)