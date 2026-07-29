---
name: self-hosted-proxy-vps
description: 自建 VPS 代理全流程——买 VPS、装 3X-UI、配 Hysteria2/VMess、诊断 DNS 污染、ISP 封锁排查、客户端兼容性。最终方案：Hysteria2(UDP 443) 主力 + VMess(TCP) 备用。
category: networking
trigger_keywords:
  - 自建代理
  - 搭梯子
  - VPS 代理
  - 翻墙
  - VPN 太慢
  - 换机场
  - 代理协议
  - Reality
  - VMess
  - Hysteria2
  - Xray
  - 3X-UI
  - DNS 污染
  - socks_remote_dns
  - 代理不通
  - ISP 封 IP
---

# 自建 VPS 代理

## 触发条件
用户抱怨现有机场慢/不稳定、想自建代理、需要美国 IP 访问 AI API、代理通了但部分站点打不开、某台设备连不上。

## 核心结论（2026-07 实战验证）

**DNS 污染 > 协议封锁** — 大多数"代理不通"的根因不是 GFW 识别协议，而是本地 DNS 返回被污染的 IP。修复 DNS 后几乎所有协议都能通。

**Hysteria2 在中国可用** — UDP 443 未被全面封锁，实测 Google 0.6s 响应，GitHub/Claude 全通。不是旧版记录的"国内不适用"。

**Nginx TLS 前端方案被废弃** — 引入额外复杂度、端口抢占、Xray listen 地址锁定 127.0.0.1 不易恢复。直接用 Hysteria2(UDP) + VMess(TCP) 双协议更简洁。

## 选 VPS

| 需求 | 推荐 | 价格 | 延迟 |
|------|------|------|------|
| 最便宜、美国 IP | RackNerd 洛杉矶 | $22/年 | 170-200ms |
| 香港低延迟 | AkileCloud | ¥10-30/月 | 30-50ms |
| 大厂稳定 | Vultr 日本 | $6/月 | 80-120ms |

## 部署流程

### 1. 买 VPS → 拿到 IP + root 密码
RackNerd 支付宝支付：https://www.racknerd.com/specials/，选 Debian 12，洛杉矶 DC-02。

### 2. 装 3X-UI 面板
```bash
ssh root@<IP>
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
# 选 SQLite，跳过 SSL（非必须）
```
安装完输出面板 URL/用户名/密码。**立即保存**。

### 3. 添加 VMess TCP 入站（备用）
面板 → 入站 → 添加：
- 协议: vmess, 端口: 10000, 传输: tcp
- UUID: 自动生成

### 4. 装 Hysteria2（主力）
```bash
# 下载最新版
curl -sL "https://github.com/apernet/hysteria/releases/download/app/v2.10.0/hysteria-linux-amd64" \
  -o /usr/local/bin/hysteria
chmod +x /usr/local/bin/hysteria

# 配置 /etc/hysteria/config.yaml
cat > /etc/hysteria/config.yaml << EOF
listen: :443
tls:
  cert: /etc/x-ui/certs/cert.pem
  key: /etc/x-ui/certs/key.pem
auth:
  type: password
  password: <生成一个密码>
masquerade:
  type: proxy
  proxy:
    url: https://www.microsoft.com
    rewriteHost: true
bandwidth:
  up: 100 mbps
  down: 200 mbps
EOF

# systemd 服务
systemctl enable --now hysteria
```

### 5. 客户端配置

#### 电脑 Hysteria2（推荐）
```yaml
# hysteria2-config.yaml
server: <VPS_IP>:443
auth: <密码>
tls:
  sni: www.microsoft.com
  insecure: true
socks5:
  listen: 127.0.0.1:10808
http:
  listen: 127.0.0.1:10809
```
启动：`hysteria-windows-amd64.exe -c hysteria2-config.yaml`

#### 手机 Nekobox
`hysteria2://<密码>@<VPS_IP>:443?sni=www.microsoft.com&insecure=1#US-VPS`

#### 电脑 VMess（备用）
地址: VPS_IP:10000, UUID: 同上, 加密: auto, 传输: tcp

### 6. DNS 配置（关键！）
- **⭐ 首选：Windows HTTP 代理 `127.0.0.1:10809`** — 天然服务端解析 DNS，Chrome/Edge/Firefox 全部零配置可用。Hysteria2 配了 `http.listen: 0.0.0.0:10809` 就有。
- **Firefox SOCKS5**: `about:config` → `network.proxy.socks_remote_dns` → true
- **Chrome/Edge SOCKS5**: 装 SwitchyOmega，勾选 "使用代理服务器解析 DNS"
- **Clash fake-ip**: 自动解决 DNS，但 Clash Verge Rev 的 Mihomo 内核经常崩溃，不推荐

## ⚠️ 关键陷阱

### DNS 污染诊断法
```bash
# 通过代理用已知 IP 直连 Google
curl --socks5 127.0.0.1:10808 --resolve www.google.com:443:142.251.155.119 \
  -sk https://www.google.com
# 200 = DNS 污染，不是代理问题
```

### 3X-UI Reality SNI 未保存
**症状**: Xray 日志 `empty "serverNames"`。**修复**: 直接写 SQLite：
```sql
UPDATE inbounds SET stream_settings = json_set(
  stream_settings, '$.realitySettings.serverNames', json_array('www.microsoft.com')
) WHERE id = 1;
```

### VMess listen 地址卡 127.0.0.1
**症状**: 配置过 nginx 前端后改回来，`ss -tlnp` 显示 `127.0.0.1:10000`。外部连不上。
**修复**: `UPDATE inbounds SET listen = '' WHERE id = 2;` 然后重启 x-ui。

### SSH 被本地代理劫持
**症状**: ping 通但 SSH 超时。**原因**: V2RayN/Hysteria 开了系统代理，SSH 走代理循环。
**修复**: 先 `taskkill /F /IM v2rayn.exe /IM hysteria-windows-amd64.exe` 再 SSH。

### Clash Verge Rev 崩客户端
Mihomo 内核兼容性差，加载 VMess/Hysteria2 配置后经常进程崩溃。**不要用它作为主力客户端**。用原版 Hysteria CLI 或 sing-box。

### ISP 级别 IP 封锁
**症状**: 特定网络（如家庭宽带）所有端口超时，其他网络（手机热点/笔记本）正常。
**解决**: RackNerd 面板换 IP（$3），或走中转链式代理。
**诊断**: 先 `ping` 通 → `tcping` 各端口 → 只有 ping 通 TCP 全超时 = ISP 拉黑了 IP 段。

### V2RayN 路由劫持国内 API
**症状**: Hermes 用 DeepSeek API 报 timeout，但 DeepSeek 国内直连可用。
**原因**: V2RayN/sing-box 的 `MATCH → proxy` 把 DeepSeek 也送美国 VPS 绕一圈。
**修复**: 在 routing rules 最前面加 `{"domain": ["domain:api.deepseek.com"], "outboundTag": "direct"}`。

### Hermes httpx 依赖崩溃
**症状**: 新安装或更新后 `Failed to initialize agent: cannot import name 'URL' from 'httpx'`。
**原因**: Python 3.14 与 httpx 0.28 不兼容。系统 pip 和 Hermes venv pip 是两套环境。
**修复**: 用 Hermes 自己的 Python 装：`C:\Users\<用户>\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m pip install httpx --upgrade`（不用系统 pip）。

### V2RayN sing-box 进程名
V2RayN 内嵌 sing-box，不是独立进程。`taskkill /F /IM sing-box.exe` 找不到是正常的。重启 V2RayN 通过托盘图标退出再打开。

### 端口选择
- 非标端口（10000+）可能被 ISP 限速/阻断 → 用 443
- Hysteria2 UDP 443 实测可用，但部分运营商拦 UDP → 备 VMess TCP

## 客户端兼容性

| 客户端 | Hysteria2 | VMess | 推荐 |
|------|:--:|:--:|:--:|
| Hysteria CLI (Windows) | ✅ | ❌ | ⭐⭐⭐⭐⭐ 最稳 |
| Nekobox (Android) | ✅ | ✅ | ⭐⭐⭐⭐ |
| V2RayN (Xray 内核) | ✅ | ✅ | ⭐⭐⭐ |
| sing-box | ✅ | ✅ | ⭐⭐⭐⭐ |
| Clash Verge Rev (Mihomo) | ⚠️ | ⚠️ | ⭐⭐ 常崩溃 |

## 速度预期

| 价位 | 延迟 | 写代码/API | 看视频 |
|------|------|:--:|:--:|
| ¥13/月 US VPS | 170-200ms | ✅ | ❌ |
| ¥30/月 HK VPS | 30-50ms | ✅ | ✅ |

BBR 拥塞控制有帮助但无法突破物理延迟：
```bash
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

## 验证清单
- [ ] `ping <VPS_IP>` 通
- [ ] `ss -ulnp | grep 443` 确认 Hysteria2 在 UDP 443
- [ ] `ss -tlnp | grep 10000` 确认 VMess 在 `*:10000`（非 127.0.0.1）
- [ ] Firefox `socks_remote_dns=true` + SOCKS5 代理能开 Google
- [ ] HTTP 代理 10809 所有浏览器通用（推荐）
- [ ] 手机 Nekobox Hysteria2 导入能连
