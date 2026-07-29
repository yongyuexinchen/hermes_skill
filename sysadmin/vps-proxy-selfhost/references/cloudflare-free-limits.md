# Cloudflare 免费版限制——完整技术分析

## 核心事实

**Cloudflare 免费版 = HTTP 世界。不认识的协议全丢。**

## CDN (orange cloud) 限制

### 支持的端口（HTTP/HTTPS）

| 协议 | 可用端口 |
|------|------|
| HTTP | 80, 8080, 8880, 2052, 2082, 2086, 2095 |
| HTTPS | 443, 2053, 2083, 2087, 2096, 8443 |

端口 22（SSH）、10000（VMess）、34356（Reality）等一律不代理。DNS 设了橙色云也绕回直连。

### 为什么 VLESS+WS 也穿不过

```
正确链路：V2RayN → WebSocket → HTTPS → CF → WebSocket → Xray
实际发生：V2RayN → WebSocket → HTTPS → CF HTTP Proxy 检查帧 → 丢弃非标准 payload
```

curl 测试 `https://域名/ws` 返回 400（WebSocket 升级成功），但 V2RayN 的 VLESS 帧被 Cloudflare WAF 判定为非法 HTTP payload 静默丢弃。不是 TLS 证书问题，不是端口问题，是协议层被拦。

## Tunnel 限制

### 仪表盘模式

`cloudflared service install <token>` 启用的模式。**本地 config.yml 被忽略**，配置完全从 Cloudflare API 拉取。

所有 ingress 规则底层都是 `http://host:port`——包括 SSH 类型 Public Hostname：
```
originService=http://localhost:22
```
sshd 返回 SSH banner → cloudflared 解析为 `malformed HTTP status code "Debian-2"` → 崩溃。

### 本地配置模式

需要 tunnel credentials JSON（非 token）：
```json
{"AccountTag":"...", "TunnelSecret":"...", "TunnelID":"..."}
```

来源：从 token（base64 → JSON，字段 `a/t/s`）解析。

即使本地配置写了 `tcp://` 或 `ssh://`，命名 tunnel 仍从 API 拉覆盖配置。**命名 tunnel = 远程管理，不可本地覆盖。**

### Access SSH 的真相

- `cloudflared access ssh` 已废弃，重命名为 `access tcp`
- `cloudflared access ssh-config` 生成的 ProxyCommand 仍引用旧命令名（cloudflared bug）
- 浏览器 SSH 渲染：Cloudflare 边缘处理 SSH 协议，但隧道到源站仍是 HTTP → 同 "Debian-2" 错误

## 能用的方案

| 方案 | 协议 | 限制 |
|------|------|------|
| ttyd (web 终端) | HTTP/WebSocket | 非原生 SSH，是网页终端 |
| Spectrum | L4 TCP | $5/月 |
| 直连 (Hysteria2) | QUIC/UDP | 不需要 CF，就是最好方案 |

## ttyd 部署（VPS 端）

```bash
wget https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 -O /usr/local/bin/ttyd
chmod +x /usr/local/bin/ttyd
# systemd: ExecStart=/usr/local/bin/ttyd --port 7681 --interface 127.0.0.1 bash
```

Dashboard: Public Hostname → Type: HTTP → `localhost:7681`
浏览器: `https://ssh.域名` → 经 Access 认证 → 直接进终端

## 协议层排查方法论

遇到"代理不通"时，逐层确认：

```
应用层:  V2RayN 配置校验 → 地址/端口/路径/UUID
WebSocket: curl -H "Upgrade: websocket" → 400 = 可升级
TLS:      V2RayN 日志无 x509 错误 = 证书 OK
TCP:      ss -tlnp 确认 VPS 端口在监听
网络:     curl --socks5 代理 确认代理进程在转发
Cloudflare: CF 日志 `originService=http://` 确认到源站协议
```

**核心教训：Cloudflare 日志 `originService=http://` = 永远 HTTP，找非 HTTP 替代方案。**
