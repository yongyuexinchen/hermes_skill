---
name: vps-proxy-selfhost
description: Self-host a proxy server on a cheap VPS to bypass GFW. Covers VPS purchase, 3X-UI panel setup, protocol selection, DNS pollution debugging, ISP-level blocking, Hysteria2 deployment, Cloudflare limitations, and multi-device deployment.
category: sysadmin
---

# VPS 自建代理（中国网络环境）

完整流程：买 VPS → 装面板 → 配协议 → 连客户端。核心：DNS 污染 + ISP 封锁 + Cloudflare 限制。

## 核心理念（新会话必读）

- **DNS 污染是首要敌人**——代理连通但打不开 Google，90% 是 DNS 返回假 IP
- **Cloudflare 免费版不能透传代理协议**——CDN 是 Layer 7 HTTP 代理，VLESS/VMess/SS 帧会被丢弃。3 天实测验证，不要再试！
- **分层排查**：VPS 出站 → 协议握手 → 客户端 DNS → 逐层确认

## 第一步：买 VPS

**推荐方案**（2026 实测）：

| 商家 | 最低价 | 位置 | 支付 | 备注 |
|------|------|------|------|------|
| RackNerd | $21.99/年 | 🇺🇸洛杉矶 | 支付宝 | 性价比王者，但 Stripe 支付宝偶抽风 |
| AkileCloud | ¥9.9/月 | 🇭🇰/🇯🇵 | 支付宝/微信 | 中国人开的，原生支付宝 |

**选美国**如果你需要 Claude/OpenAI API（它们封禁香港 IP）。账单地址填香港或美国都行。

## 第二步：装 3X-UI 面板

VPS 选 **Debian 12**。拿到 IP + root 密码后：

```bash
ssh root@<IP>
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
# 选 SQLite，跳过 SSL
```

## 第三步：配协议

### 协议选择

| 协议 | 端口 | 速度 | ISP 封锁 | 适用 |
|------|------|:--:|:--:|------|
| **Hysteria2** | 443 UDP | ⚡最快 | ⭐低 | 主力推荐 |
| VMess TCP | 10000 | 🐢中等 | ⭐中 | 最通用 |
| VLESS+Reality | 34356 | 🐢中等 | ⭐⭐高 | 高级抗封锁 |
| SSH 隧道 (-D) | 22 | 🐢慢 | ⭐最低 | 最后手段 |

### ⚠️ 3X-UI Reality 配置坑

**症状**：Xray 报 `empty "serverNames"`，客户端 `REALITY authentication failed`。
**根因**：面板创建 Reality 入站时 `serverNames` 和 `publicKey` 没写入数据库。
**修复**：SQLite 手动补，参考 `references/3x-ui-reality-pitfall.md`

### Hysteria2 部署（推荐主力）

```bash
# 下载 binary
curl -sL "https://github.com/apernet/hysteria/releases/download/app/v2.10.0/hysteria-linux-amd64" -o /usr/local/bin/hysteria
chmod +x /usr/local/bin/hysteria

# 配置 /etc/hysteria/config.yaml（自签名证书 + 伪装微软）
# systemd service 启动
```

客户端配置（所有设备通用）：
```
hysteria2://<password>@<IP>:443?sni=www.microsoft.com&insecure=1#US-VPS
```

### ISP 端口封锁（2026 实测）

- ✅ 80 (HTTP), 443 (HTTPS/UDP), 22 (SSH) — 放行
- ❌ 10000, 8388, 34356 等非标端口 — 部分 ISP 封锁
- **结论**：代理优先跑在 443 端口

## 第四步：DNS 污染解决

这是 3 天排障的核心发现——不是协议被封锁，是 DNS 返回假 IP。

| 方案 | 配置 | 效果 |
|------|------|:--:|
| Firefox socks_remote_dns | `about:config` → `true` | ✅ |
| Windows HTTP 代理 | 系统代理 :10809 | ✅ |
| Nekobox 手机 | 默认代理 DNS | ✅ |
| Clash fake-ip | DNS 规则 | ⚠️ Mihomo 不稳定 |

## 第五步：Cloudflare 域名 + Tunnel

**用途**：家里 ISP 封了 VPS IP，走域名绕过。

### 域名注册
- 阿里云 .xin/.xyz ¥7-30/年，必须实名
- NS 切 Cloudflare（deb.ns + drew.ns）

### ⚠️ Cloudflare 免费版核心限制（3 天深度实测）

**CDN (orange cloud) 不能代理任何非 HTTP 协议：**
- CDN 是 Layer 7 HTTP 代理，不是 Layer 4 TCP 隧道
- VLESS/VMess 封装在 WebSocket 里，但 payload 被 WAF 丢弃
- curl 测 WebSocket 握手返回 400（Xray 收到），V2RayN 连不上
- 可用端口仅 HTTP/HTTPS：80, 443, 8080, 8443 等

**Tunnel 仪表盘模式永远用 HTTP 连源站：**
- `cloudflared tunnel run --token` 从 API 拉远程配置，本地 config.yml 被忽略
- 入站规则总是 `http://localhost:<port>`，不支持 `tcp://` 或 `ssh://`
- SSH Public Hostname 类型只影响边缘层，隧道到源站仍是 HTTP → sshd 返回 SSH banner → `malformed HTTP status code "Debian-2"` 崩溃
- **要本地配置模式需要 tunnel credentials JSON**（见下方）

**Cloudflare Access SSH 的真相：**
- `cloudflared access ssh` 已重命名为 `access tcp`（但 `ssh-config` 生成的命令未更新）
- 浏览器 SSH 渲染依赖隧道到源站的连接，同样受 HTTP 传输限制
- **唯一可用方案：ttyd**（web 终端，讲 HTTP/WebSocket，Tunnel 能转发）
- Spectrum（$5/月）是唯一支持原始 TCP 透传的免费替代

### Tunnel 凭证体系

| 文件 | 来源 | 用途 |
|------|------|------|
| `cert.pem` | `cloudflared tunnel login`（浏览器） | 账户级凭证 |
| token | Dashboard 创建隧道时复制 | 仪表盘模式启动 |
| credentials JSON | 从 token 解析 | 本地配置模式 |

**Token 解析**（base64 → JSON，字段 `a`=AccountTag, `t`=TunnelID, `s`=TunnelSecret）：
```bash
python3 -c "
import base64, json
t = open('/etc/cloudflared/token').read().strip()
d = json.loads(base64.b64decode(t + '=='))
print(json.dumps({'AccountTag': d['a'], 'TunnelSecret': d['s'], 'TunnelID': d['t']}))
" > /etc/cloudflared/tunnel-creds.json
```

### Tunnel 安装（仪表盘模式）
```bash
cloudflared service install <token>
# 远程管理，配置在 Cloudflare Dashboard 改
```

### ttyd：Web 终端（绕过 HTTP/SSH 不兼容）
```bash
# VPS 装 ttyd + systemd，Dashboard 改 Public Hostname → HTTP → localhost:7681
wget https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 -O /usr/local/bin/ttyd
chmod +x /usr/local/bin/ttyd
# systemd: ExecStart=/usr/local/bin/ttyd --port 7681 --interface 127.0.0.1 bash
# 浏览器: https://ssh.yongyuexinchen.xin → Access 认证后直接进终端
```

## 客户端部署

- **笔记本**：Hysteria2 CLI + Windows HTTP 代理 :10809（全浏览器通用）
- **手机**：Nekobox Hysteria2 链接导入
- **家里电脑**（IP 被封）：V2RayN VLESS 走域名，或 Tunnel HTTP 代理

## 调试流程

1. **裸 HTTP**：浏览器 `http://<IP>` → 确认网络可达
2. **VPS 出站**：`curl https://www.google.com` → 确认 VPS 能上网
3. **端口**：`timeout 5 bash -c 'echo > /dev/tcp/<IP>/<PORT>'`
4. **握手**：`curl -H "Upgrade: websocket" https://<IP>/ws` → 400 = 协议可达
5. **DNS**：绕过本地 DNS 直连 IP 测试
6. **Xray 日志**：`journalctl -u x-ui | grep error`

## 常见卡点

| 现象 | 原因 | 修复 |
|------|------|------|
| Xray empty serverNames | 面板没保存 SNI | SQLite 补 |
| 端口外网不通 | listen='127.0.0.1' | 改 `listen=''` |
| 代理通但 Google 不通 | DNS 污染 | socks_remote_dns / HTTP 代理 |
| Clash 加载崩溃 | Mihomo 兼容性 | 放弃 Clash |
| CF CDN+VLESS 不通 | CF 丢代理帧 | 放弃，用直连（详见 `references/cloudflare-free-limits.md`） |
| Tunnel SSH 不通 | Dashboard 模式 HTTP 连 sshd | ttyd web 终端 or Spectrum $5/月 |
| `x509 unknown authority` | 自签名+Xray 26.x | 用 CF 域名（正规证书） |
| 家里 TCP 全超时 | ISP 封 IP 段 | CF 域名 Tunnel |
| Nginx 占 443 | 自启动 | `disable nginx` |

## 记住
- ¥13/月 174ms 是物理极限，够开发不够视频
- Cloudflare 免费版是 HTTP 代理不是 TCP 隧道——别再试 VLESS/VMess 走 CDN
- 用户桌面 `自建代理/` 有完整手册，优先参考
