# DNS 污染隔离诊断法

## 背景

在中国自建 VPS 代理时，最常见的误判是：换了 N 种协议都不通 → 以为 GFW 封锁 → 实际是 DNS 污染。

## 三步隔离法

### Step 1: 确认网络层可达

在 VPS 上装 nginx：

```bash
apt install -y nginx
systemctl start nginx
```

浏览器访问 `http://VPS_IP`。能看到 nginx 欢迎页 = TCP 可达。

### Step 2: 区分 DNS vs 协议

**用 IP 直连绕过 DNS：**

1. 从 VPS 获取 Google 真实 IP：
   ```bash
   ssh root@VPS_IP "dig +short www.google.com | head -1"
   # 例如: 142.251.155.119
   ```

2. 用真实 IP 通过代理访问：
   ```bash
   curl --socks5 127.0.0.1:10808 \
     --resolve www.google.com:443:142.251.155.119 \
     https://www.google.com
   ```

- **IP 直连通，域名不通** → DNS 污染
- **IP 直连也不通** → 代理协议被封锁

### Step 3: DNS 污染 → Firefox socks_remote_dns

Firefox `about:config` → `network.proxy.socks_remote_dns` → `true`

---

## 协议逐层调试方法论

当一种协议不通时，按以下顺序逐层降级，每层都确认后再往下：

| 层 | 协议 | 诊断意图 |
|------|------|------|
| 1 | Reality/VLESS | GFW 能否识别新协议？ |
| 2 | VMess TCP | 是否纯协议被拦截？ |
| 3 | VMess WS+TLS 443 | 是否非标端口被封锁？ |
| 4 | HTTP CONNECT proxy 80 | 是否为最原始 HTTP 代理？（排除所有加密协议） |
| 5 | SSH -D SOCKS5 22 | 是否所有非 SSH 端口都被封？ |

**每层失败的信号：**

- Layer 1-3 全部超时 + Layer 4 在 80 端口能通 → **非标端口封锁**
- Layer 4 通但部分站点不行 → **DNS 污染**
- Layer 5 能通 → **所有代理协议被 DPI 识别，走 SSH 隧道兜底**

## 实测案例 (2026-07-24)

VPS: RackNerd 美国 (192.255.128.175)，中国电信宽带。

| 尝试 | 协议 | 端口 | 结果 |
|------|------|------|------|
| 1 | Reality VLESS | 34356 | REALITY auth failed (Mihomo 兼容性) |
| 2 | VMess TCP | 10000 | timeout (ISP 封非标端口) |
| 3 | VMess WS+TLS | 443 | 连上但 DNS 返回错误 IP |
| 4 | HTTP CONNECT proxy | 80 | GitHub 200! Google timeout (DNS) |
| 5 | SSH -D SOCKS5 | 22 | 全通但慢 (TCP-over-TCP) |
| 6 | Hysteria2 QUIC | 443 UDP | Google 0.6s, 全浏览器可用 |

最终结论：**不是 GFW 封锁，是 DNS 污染 + ISP 封非标端口。** Hysteria2 走 UDP 443，ISP 不拦截，延迟可用。
