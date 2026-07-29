---
name: cloudflare-tunnel-patterns
description: Cloudflare Tunnel 实战排障模式 — ttyd 网页终端、DNS 修复、凭据提取、代理协议兼容性。当需要通过 Cloudflare Tunnel 暴露 VPS 服务、调试 521/403/WebSocket 穿透、或用 ttyd 替代直连 SSH 时加载。
trigger:
  - Cloudflare Tunnel 配置/排障
  - ttyd 网页终端部署
  - 521 Web Server Down / 403 Forbidden / malformed HTTP
  - cloudflared DNS 记录不自动生成
  - Tunnel 凭据 (cert.pem / credentials.json) 提取
  - 代理协议 (VLESS/VMess/SSH) 穿透 Cloudflare Tunnel
---

# Cloudflare Tunnel 实战排障模式

## 核心认知

**Cloudflare Tunnel 内部永远用 HTTP 连接源站。** 即使 Public Hostname 类型选 "SSH"，cloudflared 到本地服务仍然是 `http://origin:port`。这是所有问题的根源。

```
客户端 → Cloudflare Edge → (HTTP/2 or QUIC) → cloudflared → HTTP → 源站
```

## 模式一：ttyd 网页终端（替代直接 SSH）

**问题**：SSH public hostname → `localhost:22` → cloudflared 用 HTTP 连 sshd → `malformed HTTP status code "SSH-2.0"` → 崩溃。

**方案**：用 ttyd 提供 WebSocket 网页终端，Tunnel 完美匹配。

```bash
# VPS 安装
wget -q "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64" -O /usr/local/bin/ttyd
chmod +x /usr/local/bin/ttyd

# systemd 服务
cat > /etc/systemd/system/ttyd.service << 'EOF'
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

Cloudflare Dashboard: Public Hostname → Type: HTTP → URL: `http://localhost:7681`。

配合 Access Application（Email 白名单）保护。

## 模式二：DNS CNAME 手动修复

**问题**：Tunnel Public Hostname 创建后 DNS 记录不自动生成，`nslookup` 解析失败。

**手动创建**：DNS → Add record → Type: `CNAME`

| | |
|------|------|
| Name | 子域名（如 `vps`） |
| Target | `<tunnel-id>.cfargotunnel.com` |
| Proxy | 🟠 Proxied |

Tunnel ID 从 token 解码获取（见模式三）。

## 模式三：Tunnel 凭据提取

**token 解码**：`/etc/cloudflared/token` 是 base64(JSON)

```python
import base64, json
token = open("/etc/cloudflared/token").read().strip()
data = json.loads(base64.b64decode(token + "=="))
# {"a": "AccountTag", "t": "TunnelID", "s": "TunnelSecret"}
```

**credentials.json 生成**（本地 config 模式需要）：

```json
{
  "AccountTag": "<a>",
  "TunnelSecret": "<s>",
  "TunnelID": "<t>"
}
```

本地 config 模式 systemd：

```
ExecStart=/usr/local/bin/cloudflared --no-autoupdate tunnel --config /etc/cloudflared/config.yml run
```

但 SSH 类协议即使在本地模式也可能被 cloudflared 转成 HTTP（`ssh://` 不被支持）。

## 模式四：代理协议兼容性

**不可行**：
- VLESS/VMess + WebSocket 通过 Cloudflare CDN（橙色云 A 记录）→ CF 检查 WebSocket 帧
- SSH 直接通过 Tunnel → cloudflared HTTP 连接 sshd 崩溃
- HTTP CONNECT 代理通过 Tunnel → CF 拒绝 403

**可行**：
- ttyd 网页终端（HTTP/WebSocket）
- 任何标准 HTTP 服务（nginx、FastAPI）
- Hysteria2 直连（不经过 CF，UDP QUIC）

## 排障速查

| 现象 | 根因 | 修复 |
|------|------|------|
| 521 Web Server Down | DNS A 记录而非 Tunnel CNAME；或源站未监听 | 改 CNAME 记录 |
| `malformed HTTP "SSH-2.0"` | cloudflared HTTP→sshd 协议不匹配 | 换 ttyd |
| 403 Forbidden (tinyproxy) | CF 检测到 HTTP CONNECT 代理 | 放弃代理方案 |
| cloudflared 重启 hang | systemd restart 超时 | `pkill -9 cloudflared && systemctl start` |
| V2RayN 延迟 -1ms | VLESS 帧被 CF CDN/WAF 丢弃 | 走 Tunnel + ttyd 或直连 Hysteria2 |
| Public Hostname DNS 不生成 | CF 内部延迟 | 手动 CNAME |

## 工具速查

```bash
# 提取 Tunnel 凭据 + CNAME
python3 scripts/extract-tunnel-creds.py

# cloudflared 健康
systemctl status cloudflared

# 手动重启（避免 hang）
pkill -9 cloudflared && systemctl start cloudflared

# 查看配置版本
journalctl -u cloudflared --no-pager | grep 'Updated to new'
```

## 笔记

Cloudflare 免费版是 L7 HTTP 代理。它理解 HTTP/WebSocket，但不理解 SSH/TCP/UDP/VLESS 协议。不要试图把非 HTTP 协议硬塞进 Tunnel — 要么用 HTTP 封装（ttyd），要么绕过 CF（Hysteria2 直连）。
