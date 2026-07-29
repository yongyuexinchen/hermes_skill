---
name: china-vps-proxy-setup
description: Buy and self-host a VPS proxy from China — RackNerd purchase, 3X-UI panel, protocol selection (VMess/Reality/Hysteria2), DNS pollution diagnosis, client setup (V2RayN/Firefox), and common failure patterns.
trigger_keywords:
  - 搭梯子
  - 自建代理
  - 买VPS
  - VPS翻墙
  - RackNerd
  - 3X-UI
  - DNS污染
  - GFW
  - socks_remote_dns
---

# 自建 VPS 代理（从中国出发）

从零搭建：买 VPS → 装面板 → 配协议 → 客户端 → 排错。

## 0. 前置：需求判断

| 预算 | VPS 方案 | 适合 |
|------|----------|------|
| ¥10-30/月 | RackNerd 美国（$22/年） | 写代码、GitHub、AI API、Google 搜索 |
| ¥50-100/月 | Vultr/搬瓦工 日本/香港 | 看 YouTube、视频会议 |
| ¥200+/月 | CN2 GIA 香港 | 低延迟游戏、4K 视频 |

**¥13/月的美国 VPS 延迟 170-200ms，不能看视频。** 诚实设定期望。

## 1. 买 VPS

### RackNerd（最便宜）
- 网址：`racknerd.com` → 找 Specials 页面
- 选 $21.99/年 套餐（1G RAM, 20G SSD, 3TB 流量）
- **机房**：Los Angeles DC-02 或 San Jose（西海岸，到中国延迟最低）
- **系统**：Debian 12
- **支付**：Stripe 支付宝（关掉本地代理再付，否则易超时）
- **账单地址**：填美国地址（随便填，不验证）
- 邮件会收到 IP + root 密码

### 其他选项
- **Vultr**：$6/月起，日本/新加坡节点，PayPal
- **AkileCloud**：¥9.9/月，香港节点，支付宝

## 2. 装 3X-UI 面板

SSH 进 VPS，一行命令：

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

安装过程选 SQLite，SSL 先跳过。记录输出的面板地址、用户名、密码。

## 3. 配代理协议

### 🔥 端口选择：ISP 封锁非标准端口

**关键发现：中国大陆 ISP 封锁几乎所有非标准端口。** 实测：

| 端口 | 封锁 | 证据 |
|------|:--:|------|
| 80 (HTTP) | ❌ 否 | nginx 欢迎页可见 |
| 443 (HTTPS) | ❌ 否 | HTTPS 握手成功 |
| 10000 | ✅ 是 | TCP timeout |
| 8388 | ✅ 是 | TCP timeout |
| 3128 | ✅ 是 | HTTP proxy timeout |

**代理必须跑在 80 或 443 端口。** 其他端口一律不通，不是协议问题。

### 推荐协议优先级

| 优先级 | 协议 | 端口 | 延迟 | 带宽 | 适用 |
|--------|------|------|------|------|------|
| ⭐ | **Hysteria2 (QUIC)** | 443 UDP | 0.6s 开 Google | ~17KB/s | 网页浏览、API 调用 |
| ⭐ | **VMess + TCP** | 10000 → **改 443** | 同左 | 同左 | 最兼容，需 nginx 反向代理上 443 |
| | VMess + WS + TLS | 443 | 1s | ~10KB/s | 伪装 HTTPS |
| ❌ | Shadowsocks | 8388 | N/A | N/A | 端口被封 + 协议特征明显 |
| ❌ | Reality | 任意 | N/A | N/A | Clash 兼容差，3X-UI 有 serverNames 空值 bug |
| 💀 | SSH SOCKS5 隧道 | 22 | ~2s | 极慢 | **仅诊断用**，TCP-over-TCP |

> Hysteria2 延迟低但带宽受限。适合写代码、查文档、调 API；不适合下载大文件或看视频。

### 创建 VMess TCP 入站
1. 3X-UI → 入站 → 添加入站
2. 协议选 `vmess`，端口 `10000`（如 ISP 封端口则改 443，需配合 nginx）
3. 传输选 `tcp`
4. 添加客户端，记下 UUID

### Reality 常见坑
- `empty "serverNames"` → 3X-UI 面板创建时 SNI 未填入，需手动修 SQLite：
  ```python
  rs['serverNames'] = ['www.microsoft.com']
  rs['publicKey'] = '<公钥>'
  ```
- Clash Meta 报 `REALITY authentication failed` → Mihomo 版本兼容性问题，弃用换 VMess

## 4. 客户端

### Windows: V2RayN
- 下载：[v2rayN releases](https://github.com/2dust/v2rayN/releases)
- 添加服务器：地址 VPS_IP，端口 10000，UUID xxx，VMess TCP
- 系统代理 → 自动配置

### macOS: V2RayX / Sing-box

### 手机
- Android: **v2rayNG**
- iOS: **Shadowrocket** 或 **Sing-box**

直填 VMess 参数即可，不经过电脑。

## 5. 🔥 最关键：DNS 污染诊断

**症状**：GitHub 能打开，Google/YouTube 打不开。

**根因**：不是协议被封！是 **DNS 污染**——本地 DNS 返回错误 IP。

**验证方法**：浏览器直接访问 Google 已知 IP `https://142.251.155.119`。能打开 = DNS 问题。

**解决**：
- **Firefox**：`about:config` → `socks_remote_dns` → `true`，代理设 SOCKS5
- **Chrome/Edge**：装 SwitchyOmega 插件，勾选"使用代理服务器解析 DNS"

### 判断到底是 DNS 还是协议被封

终极测试：在 VPS 上装 nginx（`apt install nginx`），浏览器访问 `http://VPS_IP`。能看到 nginx 欢迎页 = 网络能通，问题在 DNS 或代理协议。

详见：`references/dns-pollution-isolation.md`

## 6. 常见故障

| 症状 | 原因 | 修复 |
|------|------|------|
| 所有代理协议都超时 | ISP 封非标准端口 | 换 80/443 端口 |
| GitHub 通 Google 不通 | **DNS 污染** | Firefox socks_remote_dns=true |
| Reality auth failed | 密钥不匹配/SNI 空 | 修 SQLite serverNames |
| SSH 连不上 VPS | 本地代理干扰 SSH | `taskkill` 代理进程 + `unset http_proxy` |
| Clash 崩溃 | Mihomo 兼容性 | 弃用，换 V2RayN |
| Hysteria2 带宽低 | UDP 在中国被限速 | 正常，延迟低够浏览，下载慢是预期内 |
| VPS 端口通但无法代理 | VPS 出口被封 | 测 `curl google.com`，IP 段被谷歌封 |

## 7. SSH 被本地代理干扰的修复

```bash
# 杀干净
taskkill /F /IM "clash-verge.exe"
taskkill /F /IM "verge-mihomo.exe"
taskkill /F /IM "v2rayn.exe"
# 清除环境变量
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
# 再 SSH
ssh root@VPS_IP
```

## 8. 速度优化

- VPS 开 BBR：`sysctl -w net.ipv4.tcp_congestion_control=bbr`
- 物理延迟无法突破，要更快只能换更贵的 VPS（CN2 GIA 香港）
- UDP 协议（Hysteria2/KCP）在中国 ISP 下常被严重限速，不推荐

## 9. ISP 封锁 VPS IP 的绕过：Cloudflare Tunnel SSH

**场景**：运营商封锁了整个 RackNerd IP 段（ping 通但 TCP 全超时），换协议无效。

**方案**：Cloudflare Tunnel 是一根"反向网线"——VPS 主动连 Cloudflare，用户通过 Cloudflare 域名访问，运营商看不到 VPS IP。

### 原理（关键区别）

| 误解 | 正确理解 |
|------|------|
| Cloudflare 帮你代理所有流量 | Cloudflare Tunnel 只是帮你建立一条到 VPS 内网服务的通道 |
| 跟 VLESS/VMess 一样是代理 | Tunnel 是**入口通道**，进去后用什么协议是你的事 |

### Cloudflare 免费版根本限制：Tunnel ingress 永远是 HTTP

**核心发现（2026-07-27 实测）**：无论 Dashboard 选什么 Type（SSH/TCP/HTTP），cloudflared 到源站永远用 `http://`。

```bash
# Tunnel 日志铁证 — 即使 Type=SSH
originService=http://localhost:22
# sshd 返回 SSH banner → Tunnel HTTP 解析器崩溃
net/http: malformed HTTP status code "Debian-2"
```

**这意味着：任何不讲 HTTP 的服务（sshd、Xray VLESS、tinyproxy CONNECT）都不能直连 Tunnel。**

### 实测矩阵（2026-07-27 全量测试）

| 尝试 | 结果 | 死因 |
|------|:--:|------|
| CDN + VLESS+WS (灵活/完全 SSL) | ❌ | CF WAF 丢弃/修改非 HTTP 帧 |
| Tunnel SSH type → sshd:22 | ❌ | `malformed HTTP status code "Debian-2"` |
| Tunnel 本地 config `ssh://` / `tcp://` | ❌ | 仍被 Dashboard 覆盖为 `http://` |
| Tunnel + tinyproxy CONNECT | ❌ | CF 拒绝正向代理 → 403 |
| Tunnel + VLESS+WS (Xray) | ❌ | cloudflared 加 `X-Forwarded-For` 头搅乱 Xray 协议检测 |
| Tunnel + VLESS+XHTTP | ❌ | 同上，XHTTP 帧被 HTTP 代理层破坏 |
| Tunnel + VLESS+HTTPUpgrade | ❌ | 同上 |
| Tunnel + Shadowsocks+WS | ❌ | SS 二进制帧不兼容 HTTP 代理 |
| **Tunnel HTTP type → ttyd:7681** | **✅** | ttyd 原生 WebSocket，完美兼容 HTTP 升级 |
| Tunnel HTTP type + Cloudflare Access | ✅ | 加邮箱认证保护 ttyd（需 Zero Trust 绑卡） |

> **结论**：Xray 所有协议（VLESS/VMess/Shadowsocks）+ 所有传输方式（WS/XHTTP/HTTPUpgrade）通过 CF Tunnel 均失败。**唯一通的是原生 HTTP/WebSocket 服务。**
>
> 代理走 Hysteria2 直连；远程管理走 Tunnel + ttyd。不要混用。

### ttyd 网页终端方案（唯一可行的 Tunnel 远程访问）

把 bash 渲染成 WebSocket 网页终端，完美匹配 Tunnel HTTP 层。带 Cloudflare Access 邮箱保护。

详见：`references/cloudflare-tunnel-ssh.md`

### Cloudflared 两种模式

| 模式 | 启动方式 | ingress | 非 HTTP 服务 |
|------|------|------|:--:|
| 仪表盘管理 | `cloudflared service install <token>` | API 远程下发 | ❌ |
| 本地配置 | `cloudflared tunnel --config run` | 本地 `config.yml` | ❌（实测仍被覆盖） |

**结论：两种模式 ingest 都是 HTTP。不要浪费时间试 `ssh://` 或 `tcp://` ingress。**

## 10. 排障方法论：逐层验证

代理链路排障核心原则：**一次只验证一层。**

```
应用层 (VLESS/SSH/HTTP)
    ↑
HTTP / WebSocket
    ↑
TLS
    ↑
TCP
    ↑
IP
```

**工程顺序**：
1. DNS 能解析吗？
2. IP 能 ping 通吗？
3. 端口 TCP 能连吗？
4. TLS 握手能过吗？
5. WebSocket 升级成功吗？
6. 应用层协议握手成功吗？

**永远不要一次引入太多变量**（VPS + Xray + Cloudflare + Tunnel + TLS + WS + DNS 同时调试）。

## 11. 维护

- 3X-UI 面板定期更新：面板设置 → 更新
- 流量监控：面板首页
- 换 VPS：SolusVM 面板重装系统即可

## 参考文件
- `references/racknerd-signup.md` — RackNerd 注册填表细节
- `references/protocol-comparison.md` — 各协议实测对比
- `references/cloudflare-tunnel-ssh.md` — Cloudflare Tunnel SSH 绕过 ISP 封锁详细指南
