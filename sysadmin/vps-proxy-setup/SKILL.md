---
name: vps-proxy-setup
description: 自建 VPS 代理全流程：选购、安装面板、配置协议、DNS 诊断、客户端接入。当用户要搭建自己的翻墙代理时加载。
trigger_keywords:
  - 自建代理
  - 搭梯子
  - VPS 代理
  - 自己搭 VPN
  - RackNerd
  - 3X-UI
  - Xray 代理
  - 翻墙 VPS
category: sysadmin
---

# 自建 VPS 代理全流程

## 触发条件
用户要自己搭建代理服务器（翻墙），而非购买现有机场。

## 核心教训：先测 DNS，别死磕协议

**最常见的错误**：换了无数协议（Reality/VMess/SS）都不通，以为是 GFW 封锁，**实际是 DNS 污染**。

诊断口诀：
1. VPS 能 ping 通 ✅
2. 端口能 TCP 连接 ✅  
3. 代理协议不通 ❌
4. → **99% 是 DNS**，不是协议被封

验证方法：用 IP 直连测试，绕过 DNS 解析。

## 标准流程

### 1. VPS 选购

首选 **RackNerd**（最便宜，$22/年 ≈ ¥158/年，支付宝）：
- https://www.racknerd.com/specials/
- 选 `1 GB KVM VPS Special`（1 vCPU/1GB RAM/20GB SSD/3TB 流量/1Gbps）
- 机房选 **Los Angeles DC-02** 或 **San Jose**（西海岸到中国延迟最低）
- 系统选 **Debian 12**
- 账单地址填美国地址（不验证）

备选：Vultr（$6/月，日本/新加坡节点，延迟更低但贵）

### 2. SSH 连接（Windows）

```bash
ssh root@<VPS_IP>
# 密码见邮件
```

**Windows 坑**：优先用 git-bash，cmd 有时密码粘贴失败。如 SSH 超时，先 `unset http_proxy https_proxy` 绕过本机代理。

### 3. 安装 Hysteria2（推荐，UDP/QUIC 最快）

Hysteria2 基于 QUIC/UDP，延迟 174ms 下比 VMess/VLESS TCP 快 3-5 倍。配置极简：

```bash
# 下载服务端
wget https://github.com/apernet/hysteria/releases/latest/download/hysteria-linux-amd64 -O /usr/local/bin/hysteria
chmod +x /usr/local/bin/hysteria

# 创建配置
cat > /etc/hysteria/config.yaml << 'EOF'
listen: :443
tls:
  cert: /etc/hysteria/cert.pem
  key: /etc/hysteria/key.pem
auth:
  type: password
  password: <你自己的密码>
masquerade:
  type: proxy
  proxy:
    url: https://www.microsoft.com
    rewriteHost: true
EOF

# 生成自签名证书
mkdir -p /etc/hysteria
openssl req -x509 -newkey rsa:4096 -keyout /etc/hysteria/key.pem \
  -out /etc/hysteria/cert.pem -days 365 -nodes -subj "/CN=www.microsoft.com"

# systemd 服务
cat > /etc/systemd/system/hysteria.service << EOF
[Unit]
Description=Hysteria2
After=network.target
[Service]
ExecStart=/usr/local/bin/hysteria server -c /etc/hysteria/config.yaml
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now hysteria
```

客户端链接：`hysteria2://密码@IP:443?sni=www.microsoft.com&insecure=1#US-VPS`

**注意事项**：
- Hysteria2 走 UDP，运营商 TCP 封锁对它无效
- 但如果运营商做了 UDP Qos 限速，可能反而不如 TCP
- 不兼容 Cloudflare CDN/Tunnel（免费 L7 代理不支持 UDP）
- 客户端 `insecure=1` 跳过证书验证——自建 VPS 只有自己用时安全

### 4. Cloudflare Tunnel 配置（针对 ISP 封锁 VPS IP 的情况）

当运营商封锁了 VPS IP（ping 通但 TCP 全超时），Cloudflare Tunnel 让 VPS 主动连 Cloudflare，用户通过域名访问。

**前提**：一个已通过实名认证的域名 + DNS 切到 Cloudflare。

**步骤**：
1. Cloudflare Dashboard → Zero Trust → Networks → Tunnels → Create
2. 命名 → 选 Debian → 复制安装命令（在 VPS 上跑）
3. Public Hostname → 添加：subdomain `vps` → Type `HTTP` → URL `http://localhost:10000`

**VPS 端 Shadowsocks 入站**（通过 3X-UI 或直接改 Xray）：
```json
{
  "protocol": "shadowsocks",
  "port": 10000,
  "settings": {
    "method": "aes-256-gcm",
    "password": "密码",
    "network": "tcp,udp"
  },
  "streamSettings": {
    "network": "ws",
    "security": "none",
    "wsSettings": { "path": "/ws" }
  }
}
```

**客户端 V2RayN 配置**：Shadowsocks，地址 `vps.你的域名`，端口 443，加密 aes-256-gcm，传输 ws，路径 /ws，TLS 开启。

**⚠️ 为什么不选 VLESS/VMess**：见 references/cloudflare-tunnel-protocol-compatibility.md。

### 5. 安装 3X-UI 面板（备选）

如需多协议管理（VLESS Reality 等）：

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

安装过程会：
- 自动生成随机端口、用户名、密码、WebBasePath
- 装完会显示面板地址和登录信息
- 记下所有信息（面板地址、用户名、密码）

### 4. 创建入站（Inbound）—通过 3X-UI

在 3X-UI 面板 → 入站 → 添加入站：

**推荐：VMess + TCP（最稳）**
- 协议：`vmess`
- 端口：`10000`（或任意 >1024）
- 传输：`tcp`
- UUID：自动生成或自定义

**Reality 踩坑**：如果选 Reality，必须在面板"安全"标签页的 SNI 下拉框中选择目标域名（如 `www.microsoft.com`），否则 Xray 报 `empty "serverNames"` 无法启动。面板的 SNI 字段有时不会自动从"目标"字段继承。

### 5. 客户端配置

**V2RayN（Windows）**：
- 手动添加服务器：地址/IP、端口、UUID、加密 auto、传输 tcp
- 启动系统代理（SOCKS5 127.0.0.1:10808）

### 6. DNS 污染解决 ⚠️ 关键步骤

默认 SOCKS5 代理使用本地 DNS 解析，国内 DNS 返回被污染的 IP。

**推荐：Windows 全局 HTTP 代理（最简单）**

Hysteria2 和 V2RayN 都提供 HTTP 代理端口（`127.0.0.1:10809`），HTTP 代理默认在服务端（VPS）解析 DNS，天然免疫 DNS 污染。Chrome/Edge/Firefox 全部可用。

Windows 设置 → 网络和 Internet → 代理 → 手动：
- 地址：`127.0.0.1`
- 端口：`10809`

**为什么优先 HTTP 代理而非 SOCKS5**：
- SOCKS5 (`10808`) 默认本地 DNS → 污染 → 需手动配远程 DNS
- HTTP 代理 (`10809`) 自动远端 DNS → 零配置
- 对 99% 的网页浏览需求，HTTP 代理足够

**备用方案 A：Firefox + 远程 DNS**
1. Firefox 地址栏 `about:config`
2. 搜索 `socks_remote_dns` → 双击改为 `true`
3. Firefox 代理设 SOCKS5 `127.0.0.1:10808`

**方案 B：直接验证 DNS 是问题**
```bash
# 从 VPS 解析 Google IP
ssh root@<VPS> "dig +short www.google.com"
# 用该 IP 直连测试（绕过 DNS）
curl --socks5 127.0.0.1:10808 --resolve www.google.com:443:<IP> https://www.google.com
```

### 7. 优化

```bash
# 开启 BBR 拥塞控制（高延迟下提升吞吐）
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

## 协议对比

| 协议 | 速度 | 抗封锁 | 兼容性 | 推荐场景 |
|------|------|--------|--------|----------|
| **Hysteria2** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | **首选直连**（QUIC/UDP，最快） |
| Shadowsocks+WS+TLS | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **走 Cloudflare Tunnel 的唯一选择** |
| VMess TCP | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 简单备用 |
| VLESS Reality | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 客户端支持时用 |

### Cloudflare Tunnel 协议兼容矩阵（2026-07-27 实战验证）

经 9 次尝试，只有 Shadowsocks+WS 能无损穿透 Cloudflare Tunnel：

| 协议 | 传输 | 结果 | 根因 |
|------|------|:--:|------|
| VMess | WS (CF CDN) | ❌ | CF CDN L7 丢弃二进制帧 |
| VLESS | WS (CF CDN 灵活 SSL) | ❌ | 灵活模式加 HTTP 头破坏帧 |
| VLESS | WS (CF CDN 完全 SSL) | ❌ | WAF 静默丢弃非标准帧 |
| VLESS | WS (CF Tunnel) | ❌ | cloudflared HTTP 代理破坏握手 |
| VLESS | XHTTP (CF Tunnel) | ❌ | 同上 |
| VLESS | HTTPUpgrade (CF Tunnel) | ❌ | 同上 |
| **Shadowsocks** | **WS (CF Tunnel)** | **✅** | **无握手，纯加密流** |
| tinyproxy | HTTP CONNECT (CF Tunnel) | ❌ | CF 拒绝正向代理请求 |
| SSH 直连 | (CF Tunnel SSH) | ❌ | cloudflared HTTP→sshd banner 冲突 |

**核心结论**：CF Tunnel 的 ingress 永远走 HTTP 协议。Shadowsocks 无握手阶段、纯加密流，是唯一能无损穿透的方案。

详见 `references/cloudflare-tunnel-protocol-compatibility.md`。

## 已知事实（本机）

- RackNerd VPS: 192.255.128.175, $22/年, Debian 12, LA DC-02
- 域名: `yongyuexinchen.xin`（Cloudflare DNS, 2028-07-25 到期）
- Cloudflare Tunnel ID: `c6767d48-79b0-4ad8-add3-dccbcd1d7d82`
- 3X-UI 面板: 端口 20321, 用户名 `2wpvGh2gHx`, 密码 `3dLGXvbD2F`
- 通用 UUID: `2542750a-5b75-466c-a43c-de1d3f973a29`
- 通用密码: `zt2nnfr2bstjeu94`
- Hysteria2: UDP 443（主力，SNI `www.microsoft.com`, insecure）
- Shadowsocks+WS: TCP 10000 → CF Tunnel → `vps.yongyuexinchen.xin:443`
- ttyd 网页终端: `https://ssh.yongyuexinchen.xin`（Access 认证）
- 延迟: ~174ms（中美物理极限）
- 桌面文件: `C:\Users\53028\Desktop\自建代理\`

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Google 打不开但 GitHub 能通 | DNS 污染 | Firefox socks_remote_dns=true |
| Reality 报 empty serverNames | 面板 SNI 未填 | 面板编辑入站 → 安全 → SNI 下拉选域名 |
| 所有协议都不通 | 先排查 DNS | 用 IP 直连测试排除 DNS 因素 |
| SSH 连不上 | 本机代理拦截 | `unset http_proxy https_proxy` 后重试 |
| pip/conda 装不了包 | 代理环境变量污染 | 同上 + 选国内镜像源 |
