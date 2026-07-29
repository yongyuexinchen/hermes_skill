# Cloudflare Tunnel SSH — 绕过 ISP IP 封锁

> 适配场景：运营商封锁 VPS IP（ping 通但 TCP 全超时），需通过 Cloudflare 域名访问。

## ⚠️ 关键认知：Cloudflare Tunnel ingress 永远是 HTTP

**实测确认（2026-07-27）**：无论 Dashboard 里选什么 Type（SSH/HTTP/TCP），cloudflared 到源站的连接永远用 `http://` 协议。

```
# tunnel 日志证据
originService=http://localhost:22   # ← 即使 Type=SSH，也是 http://
# 连接 sshd 后崩溃
net/http: HTTP/1.x transport connection broken: malformed HTTP status code "Debian-2"
```

**这意味着 Tunnel 不能直连 sshd（sshd 不讲 HTTP）。**

## 正确方案：ttyd 网页终端

**ttyd** 把 bash 渲染成 WebSocket 网页终端——纯 HTTP/WebSocket，Cloudflare Tunnel 完美兼容。

### 架构

```
浏览器 → https://ssh.域名.com → Cloudflare Access → Tunnel → ttyd:7681 → bash
                                        ↑
                                  （可选）认证保护
```

### 步骤

#### 1. VPS 装 ttyd

```bash
wget -q "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64" \
  -O /usr/local/bin/ttyd
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
systemctl daemon-reload && systemctl enable --now ttyd
```

**安全注意**：`--interface 127.0.0.1` 确保只监听本地，外部只能通过 Tunnel 访问。

#### 2. Cloudflare Dashboard — Tunnel 入口

```
Zero Trust → Networks → Tunnels → [Tunnel名] → Public Hostname → Add
```

| 字段 | 值 |
|------|-----|
| Subdomain | `ssh` |
| Domain | `你的域名` |
| Type | **HTTP**（不是 SSH！） |
| URL | `http://localhost:7681` |

#### 3. Cloudflare Access（可选，安全推荐）

```
Zero Trust → Access → Applications → Add → Self-hosted
```

| 字段 | 值 |
|------|-----|
| Name | `vps-ssh` |
| Subdomain | `ssh` |
| Domain | `你的域名` |

Policy：Add include rule → Emails → `你的邮箱` → Allow。

**⚠️ 插件提示**：Zero Trust 首次使用会要求绑信用卡（免费用户 50 人以下不扣费，仅防滥用验证）。

#### 4. 使用

浏览器直接打开 `https://ssh.你的域名`，Access 认证后进入网页终端。

### Cloudflared 两种工作模式

| 模式 | 启动方式 | ingress 来源 | 用途 |
|------|------|------|------|
| **仪表盘管理**（推荐） | `cloudflared service install <token>` | Cloudflare API 远程下发 | 日常使用，Dashboard 管理规则 |
| **本地配置** | `cloudflared tunnel --config config.yml run` | 本地 `config.yml` | 需要 `ssh://` 等非 HTTP ingress（基本不适用） |

**⚠️ 本地模式陷阱**：
- 需要 `cert.pem`（`cloudflared tunnel login` 生成，需浏览器）
- 即使写 `ssh://localhost:22` 或 `tcp://localhost:22`，日志仍显示 `http://localhost:22`
- 结论：**本地配置模式也改不了 ingress 协议，Tunnel 底层就是 HTTP**

### 与代理的关系

| 方案 | 用途 | 适用 |
|------|------|:--:|
| ttyd 网页终端 | 远程管理 VPS | ✅ 任何设备 |
| Hysteria2 直连 | 主力代理 | ✅ 未被封的 ISP |
| VLESS+WS+Tunnel | 代理 | ❌ Tunnel HTTP 层破坏 VLESS 帧 |

**不要尝试让 VLESS/VMess 穿过 Tunnel 的 HTTP 层。** 这是协议不兼容，不是配置问题。

### 已知不可行方案

| 方案 | 失败原因 | 日志特征 |
|------|------|------|
| Dashboard SSH type → localhost:22 | Tunnel 用 HTTP 连 sshd | `malformed HTTP status code "Debian-2"` |
| 本地 config `ssh://` | 仍被 API 覆盖为 `http://` | `originService=http://localhost:22` |
| 本地 config `tcp://` | 同上 | `originService=http://localhost:22` |
| Tunnel + VLESS+WS | HTTP 层有 VLESS 帧的 WebSocket payload | 521/无声丢弃 |
| Tunnel + tinyproxy CONNECT | CF 拒绝正向代理 | 403 Forbidden |

### 排障：521 Web Server Down

`521` = Cloudflare 边缘收到请求但 cloudflared 连不上源站。常见原因：

1. **DNS 记录缺失**：Cloudflare DNS → Records 里该子域名的记录被删了（切 NS 后旧记录可能丢失）
2. **Tunnel 未重载配置**：Dashboard 改了 public hostname 但 cloudflared 没收到 `Updated to new configuration` → `systemctl restart cloudflared`
3. **源服务挂了**：在 VPS 上 `curl http://localhost:<端口>` 确认本地可访问
