# Cloudflare Tunnel 分层调试法

## 核心原则

**一次只验证一层。** 不要同时改 VPS + Tunnel + Protocol + DNS + Client。

## 协议栈对照

```
应用层: VLESS / HTTP CONNECT / nginx
  ↑
WebSocket / HTTP
  ↑
TLS (Cloudflare 处理)
  ↑
TCP
  ↑
IP (Cloudflare Tunnel)
```

每一层独立验证，确认通才往上走。

## 分层验证流程

### 第 0 层：Tunnel 本身是否转发 HTTP

```bash
systemctl status cloudflared  # 确认 running
```

VPS 上装 nginx 监听 80 端口，Dashboard Public Hostname URL → `localhost:80`，浏览器访问 `https://vps.domain.com`。

- 403/404 = **Tunnel 通**（nginx 响应了但无内容）
- 000/timeout = Tunnel 或 DNS 不通

### 第 1 层：Tunnel 能否转发 WebSocket

```bash
curl -sk -H "Upgrade: websocket" -H "Connection: Upgrade" \
  https://vps.domain.com/ws
```

- HTTP 400 = **WebSocket 升级成功，到达 Xray**
- HTTP 000 = WebSocket 被 Cloudflare 拦截

### 第 2 层：V2RayN 能否握手

```bash
curl --socks5 127.0.0.1:10808 https://www.google.com
```

- HTTP 200 = 代理通
- HTTP 000 = V2RayN 或远端协议问题
- `x509` 错误 = TLS 证书链问题（allowInsecure 或 CF 证书链）

### 第 3 层：浏览器能否访问

确认系统代理指向正确端口（10808 = SOCKS5, 10809 = HTTP），浏览器开 Google。

## 常见跨层错误

| 错误 | 层的边界 | 原因 |
|------|--------|------|
| V2RayN 延迟 -1ms | L2→L1 | CF CDN 注入 HTTP 头破坏 WS 帧 |
| VPS Xray 日志无请求 | L0→L1 | Tunnel 指向错误端口 |
| `X-Forwarded-For` 警告 | L1→L2 | CF CDN 橙色云干扰，改 Tunnel |
| `certificate signed by unknown authority` | L1 | 自签名证书，Xray 26.x 需 pinnedPeerCertSha256 |
| curl 直连 VPS 能通，经 CF 不通 | L0 | CF 路由/DNS 未生效 |

## Tunnel vs CDN 决策

| | Tunnel | CDN 橙色云 |
|------|:--:|:--:|
| 转发方式 | L7 HTTP/WS | L7 HTTP/WS |
| 是否注 HTTP 头 | 否 | **是（X-Forwarded-For）** |
| 代理协议兼容 | 可能（需验证） | **不兼容** |
| 免费 | 是 | 是 |
| 适用场景 | 隐蔽 IP | 网站加速 |

**代理协议必须走 Tunnel，不能走 CDN 橙色云。**
