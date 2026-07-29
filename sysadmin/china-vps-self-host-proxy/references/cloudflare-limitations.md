# Cloudflare 免费版对代理协议的硬限制

## 核心结论

**Cloudflare 免费版 = Layer 7 HTTP 代理，不是 Layer 4 TCP 隧道。**
任何非 HTTP 协议无法通过免费层透传。

## 已验证的失败路径

### 1. Cloudflare CDN（橙色云）+ VLESS/VMess WebSocket → 失败

**链路**：V2RayN → CF CDN(HTTPS) → VPS:443(Xray VLESS+WS+TLS)

**失败原因**：CF CDN 在 L7 层检查 WebSocket 数据帧。VLESS/VMess 的二进制加密帧虽封装在 WebSocket 里，但 payload 非合法 WebSocket 数据，被 WAF 丢弃或触发 403。

**证据**：curl WebSocket 握手返回 400（Xray 收到连接），但 V2RayN 客户端连接无响应（-1ms），VPS Xray 无任何连接日志。

### 2. Cloudflare Tunnel + tinyproxy HTTP CONNECT → 失败

**链路**：curl -x → CF Tunnel(仪表盘 HTTP 类型) → tinyproxy:3128 → 互联网

**失败原因**：Cloudflare 的 HTTP 代理层检测到 `CONNECT` 方法（正向代理请求），直接返回 403 Forbidden。

### 3. Cloudflare Tunnel SSH Access → 失败

**根因日志**：
```
originService=http://localhost:22
malformed HTTP status code "Debian-2"
```

**失败原因**：使用 `--token`（仪表盘远程配置）启动时，cloudflared 从 CF API 拉取配置，**所有 ingress 都是 `http://` 协议**。即使本地 config.yml 写 `ssh://localhost:22`，仪表盘配置会覆盖。cloudflared 用 HTTP 连 sshd，sshd 返回 SSH banner → HTTP 解析器崩溃。

**本地配置模式需要 cert.pem**：`cloudflared tunnel login`（需要浏览器授权域名），生成 `~/.cloudflared/cert.pem`。有此文件后才能脱离仪表盘，使用 `ssh://` 或 `tcp://` ingress。

## 仪表盘模式 vs 本地配置模式（重要）

### 仪表盘模式（`--token-file`）
- cloudflared 启动后从 CF API 拉取远程配置
- **日志标识**：`Updated to new configuration config="..." version=N`
- **所有 ingress 强制为 `http://`**，即使 Dashboard UI 选 "SSH" 类型
- 本地 `config.yml` **被完全忽略**

### 本地配置模式（`--config config.yml` + `credentials-file`）
- 需要 `tunnel-creds.json`（含 AccountTag, TunnelSecret, TunnelID）
- **从 token 提取 tunnel-creds.json 的方法**：
  ```python
  import base64, json
  token = open("/etc/cloudflared/token").read().strip()
  data = json.loads(base64.b64decode(token + "=="))
  creds = {"AccountTag": data["a"], "TunnelSecret": data["s"], "TunnelID": data["t"]}
  json.dump(creds, open("/etc/cloudflared/tunnel-creds.json", "w"))
  ```
- `cert.pem` 通过 `cloudflared tunnel login` 在笔记本上生成，再 scp 到 VPS
- **但即使本地配置模式，`tcp://` 和 `ssh://` ingress 也不被 cloudflared 支持**（会自动降级为 `http://`）

## ✅ 唯一通的路：Tunnel + ttyd（浏览器 SSH）

### 架构
```
浏览器 → https://ssh.yongyuexinchen.xin → CF Access → Tunnel → ttyd:7681 → bash
```

### VPS 部署
```bash
# 安装 ttyd
wget -q "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64" -O /usr/local/bin/ttyd
chmod +x /usr/local/bin/ttyd

# systemd 服务（监听 127.0.0.1）
cat > /etc/systemd/system/ttyd.service << EOF
[Unit]
Description=ttyd web terminal
After=network.target
[Service]
ExecStart=/usr/local/bin/ttyd --port 7681 --interface 127.0.0.1 bash
Restart=always
[Install]
WantedBy=multi-user.target
EOF

systemctl enable ttyd --now
```

### Cloudflare Dashboard 配置
- Tunnel Public Hostname: Subdomain `ssh`, Type `HTTP`, URL `http://localhost:7681`
- Access Application（可选）: 加 Email 规则保护

### 局限性
- 只能管理 VPS（敲命令），**不能做 SOCKS5 代理**
- 代理仍需 Hysteria2 等直连协议

## Cloudflare Tunnel HTTP CONNECT 被拒

Tunnel HTTP 类型返回 `403 Forbidden`（含 `cloudflare` 标识），CF 检测到正向代理请求并拒绝。

## Cloudflare 免费版端口限制

只代理 HTTP/HTTPS，且仅限以下端口：

| 协议 | 支持端口 |
|------|------|
| HTTP | 80, 8080, 8880, 2052, 2082, 2086, 2095 |
| HTTPS | 443, 2053, 2083, 2087, 2096, 8443 |

端口 22（SSH）、非标准端口不会被代理。即使 DNS 设橙色云，CF 也会回退到 DNS-only（灰色云）。

## 什么能通

| 场景 | 能否通 |
|------|:--:|
| Tunnel + nginx/网站 | ✅ 原生支持 |
| Tunnel + API (FastAPI) | ✅ HTTP 协议匹配 |
| CDN + 普通 WebSocket | ✅ |
| CDN + VLESS over WS | ❌ WAF 丢包 |
| Tunnel + HTTP CONNECT 代理 | ❌ CF 拒绝 |
| Tunnel + SSH | ❌ 仪表盘用 http:// 连源站 |

## 要透传 TCP 需要什么

- **Cloudflare Spectrum**：$5/月起，L4 TCP/UDP 代理，不解析协议
- **自建 frp/nps**：需额外中转服务器
- **直接换 VPS IP**：RackNerd $3/次，简单但可能再次被封

## 正确使用 Cloudflare 的场景

Cloudflare 不是用来翻墙的，是用来做**应用入口**的：

```
用户浏览器
  ↓  HTTPS
Cloudflare CDN
  ↓  Tunnel
VPS Nginx
  ↓
FastAPI :8000
  ↓
PostgreSQL
```

这才是 Cloudflare 的设计场景。
