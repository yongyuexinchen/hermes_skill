# 本地 Chrome CDP 绕过反爬

## 适用场景

目标网站使用 JS 挑战（如知乎 zse-ck、百度验证码），Browserbase/curl/requests 均被拦截。

## 完整操作步骤（按顺序，一步不能少）

### 1. 杀光所有 Chrome 进程
```bash
taskkill /F /IM chrome.exe
```
残留进程会导致新 Chrome 无法以调试模式启动。

### 2. 启动 Chrome 调试模式

**Windows（关键：必须加 --user-data-dir）：**
```bash
# 先创建独立目录（仅首次）
mkdir "%USERPROFILE%\chrome-debug-profile"

# 启动（CMD 窗口绝对不能关！）
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug-profile"
```

**macOS：**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**为什么必须加 --user-data-dir？** Windows 上如果已有 Chrome 进程在跑，不带此参数的启动命令会被已有进程"吞掉"——新窗口打开了但 9222 端口不监听。指定独立目录强制创建全新 Chrome 实例。

### 3. 验证调试模式已启动
在 Chrome 地址栏访问 `http://localhost:9222/json/version`——必须看到 JSON 数据（含 `webSocketDebuggerUrl`），不是"拒绝连接"。

### 4. 连接
在 Hermes 中输入 `/browser`。这一步设置 `BROWSER_CDP_URL` 环境变量，后续所有 `browser_*` 工具走 CDP。

### 5. 验证成功
`browser_navigate` 返回的 `stealth_features` 中包含 `cdp_override` 即为成功。

## 可选：持久化配置

如果不想每次 `/browser`，可以写入 config（重启后保留）：
```bash
hermes config set browser.cdp_url http://localhost:9222
```
但 Chrome 调试模式仍需每次手动启动。

## 常见故障排查

| 症状 | 原因 | 修复 |
|------|------|------|
| `localhost:9222/json` 拒绝连接 | Chrome 没以调试模式启动，或残留进程 | taskkill 杀光 → 加 --user-data-dir 重试 |
| CMD 窗口关了 → Chrome 也没了 | CMD 是 Chrome 调试模式的父进程 | 重新走流程 |
| `/browser` 后仍超时 | CDP 连接未建立 | 确认 9222 端口有 JSON 响应，再 `/browser` |
| `/browser` 后 stealth_features 是 local 不是 cdp_override | 环境变量没设上 | 重启 Hermes 再 `/browser` |

## 可用性矩阵

| 平台 | Browserbase | 本地 CDP | curl |
|------|------------|---------|------|
| 知乎 | ❌ 403 zse-ck | ✅ | ❌ |
| 百度搜索 | ❌ | ✅ | ❌ |
| 百度百科 | ❌ 验证码 | ✅ | ❌ |
| 腾讯云开发者社区 | ✅ | ✅ | ✅ |
| 博客园/CSDN | ✅ | ✅ | ✅ |

## CDP 工作原理

```
用户 /browser → Hermes 设 BROWSER_CDP_URL=http://localhost:9222
    ↓
browser_navigate 被调用
    ↓
_resolve_cdp_override() 访问 http://localhost:9222/json/version
    ↓
提取 webSocketDebuggerUrl → ws://localhost:9222/devtools/browser/xxx
    ↓
通过 WebSocket 发送 CDP 命令 → Chrome 执行 → 返回结果
```
