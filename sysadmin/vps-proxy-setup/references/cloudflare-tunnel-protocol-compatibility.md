# Cloudflare Tunnel 协议兼容性完整报告

> 2026-07-24 ~ 2026-07-27 实战验证，9 次尝试的完整记录

## 前提条件

- VPS：RackNerd $22/年，IP `192.255.128.175`，Debian 12
- 域名：`yongyuexinchen.xin`，DNS 切到 Cloudflare
- 目标：家里电脑 ISP 封锁 VPS IP（ping 通 TCP 全超时），需通过 Cloudflare 访问

## 测试矩阵

| # | 协议 | 传输层 | 载体 | 结果 | 根因分析 |
|:--:|------|------|------|:--:|------|
| 1 | VMess | WS | CF CDN (橙色云) | ❌ | CF CDN 是 L7 HTTP 代理，VMess 二进制帧被丢弃 |
| 2 | VLESS | WS | CF CDN (灵活 SSL) | ❌ | 灵活模式在 Cloudflare→源站走 HTTP，添加 HTTP 头破坏帧结构 |
| 3 | VLESS | WS | CF CDN (完全 SSL) | ❌ | CF WAF 静默丢弃非标准 WebSocket 帧 |
| 4 | VLESS | WS | CF Tunnel (HTTP ingress) | ❌ | cloudflared HTTP 代理破坏 VLESS 握手时序 |
| 5 | VLESS | XHTTP | CF Tunnel (HTTP ingress) | ❌ | 同 #4 |
| 6 | VLESS | HTTPUpgrade | CF Tunnel (HTTP ingress) | ❌ | 同 #4 |
| 7 | **Shadowsocks** | **WS** | **CF Tunnel (HTTP ingress)** | **✅** | **无握手，纯 AES 加密流，WebSocket 二进制帧不被干预** |
| 8 | - | HTTP CONNECT | CF Tunnel → tinyproxy | ❌ | CF 拒绝正向代理请求（403） |
| 9 | - | SSH (直连) | CF Tunnel SSH type | ❌ | cloudflared 用 HTTP 连 sshd，收到 SSH banner 后 HTTP 解析器崩溃 |

## 成功方案详细配置

### VPS 端（Xray Shadowsocks Inbound）

```json
{
  "protocol": "shadowsocks",
  "port": 10000,
  "settings": {
    "method": "aes-256-gcm",
    "password": "zt2nnfr2bstjeu94",
    "network": "tcp,udp"
  },
  "streamSettings": {
    "network": "ws",
    "security": "none",
    "wsSettings": {
      "path": "/ws",
      "headers": {}
    }
  },
  "sniffing": { "enabled": false }
}
```

### Cloudflare Tunnel Public Hostname

- Subdomain: `vps`
- Type: `HTTP`
- URL: `http://localhost:10000`

### 客户端 V2RayN

| | |
|------|------|
| 协议 | Shadowsocks |
| 地址 | `vps.yongyuexinchen.xin` |
| 端口 | `443` |
| 加密 | `aes-256-gcm` |
| 密码 | `zt2nnfr2bstjeu94` |
| 传输 | `ws` |
| 路径 | `/ws` |
| TLS | ✅ |
| 伪装域名 | `vps.yongyuexinchen.xin` |

### 实测性能

| 目标 | HTTP 状态码 | 延迟 |
|------|:--:|------|
| Google | 200 | 2.5s |
| GitHub | 200 | 3.1s |

## 为什么 Shadowsocks 能过而 VLESS 不能？

### 协议握手对比

```
VLESS 连接建立：
  客户端 → TLS 握手 → 服务器
         → WebSocket 升级 → 服务器
         → VLESS 协议握手（认证+加密协商+流控，多轮）→ 服务器
         → 数据传输
         ↑ cloudflared HTTP 代理在这一步缓存/重组帧 → 握手断裂

Shadowsocks 连接建立：
  客户端 → TLS 握手 → Cloudflare（终止）
         → WebSocket 升级 → cloudflared → Xray
         → 加密 TCP 流（从第一个字节开始，无握手）→ Xray → 目标
         ↑ cloudflared 看到的是标准 WebSocket 二进制帧 → 不干预
```

### 关键技术细节

1. **cloudflared 添加 X-Forwarded-For 头**：Xray 日志显示 `received "X-Forwarded-For" from 127.0.0.1`，协议嗅探可能将连接误判为 HTTP

2. **WebSocket 帧的掩码和分片**：cloudflared 作为代理需要重新掩码/分片 WebSocket 帧，VLESS 的多帧握手数据可能在重分片后丢失帧边界信息

3. **Shadowsocks 的单向流特性**：SS 从 WebSocket 升级完成后的第一个字节就是加密数据，没有 "hello/ack/negotiate" 阶段，cloudflared 的帧处理不影响数据完整性

## 关键坑记录

### 坑 1: cloudflared 仪表盘模式总是走 HTTP

`cloudflared tunnel run --token` 从 Cloudflare API 拉取远程 ingress 配置。本地 config.yml 中的 `tcp://` 或 `ssh://` 被忽略，所有规则强制转为 `http://`。

**诊断方法**：
```bash
journalctl -u cloudflared | grep "Updated to new configuration"
```
显示的实际配置中 ingress 永远是 `http://`。

### 坑 2: Cloudflare DNS 记录类型

- Tunnel public hostname 应该自动创建 Tunnel 类型 DNS 记录
- 如果没自动创建，手动添加 CNAME → `tunnel-id.cfargotunnel.com`
- A 记录（指向 VPS IP）走 CDN（橙色云），不是 Tunnel

### 坑 3: 删除 DNS A 记录会断开 Tunnel 绑定

删掉 `vps.yongyuexinchen.xin` 的 A 记录后，Tunnel public hostname 也失效。需重新创建。

### 坑 4: Xray sniffing 应关闭

cloudflared 的 HTTP 头会导致 Xray 协议嗅探误判。关闭 sniffing：`"sniffing": { "enabled": false }`。

## 不可能走通的方案

以下方案在 Cloudflare 免费版下绝对不可行，不要尝试：
- Hysteria2 + CF CDN/Tunnel（QUIC/UDP，CF 不解 UDP）
- VLESS/VMess 裸 TCP + CF CDN（非 HTTP，L7 代理不转发）
- Raw SSH + CF Tunnel（cloudflared HTTP ingress 与 SSH 协议冲突）
- HTTP CONNECT 正向代理 + CF Tunnel（403 Forbidden）
