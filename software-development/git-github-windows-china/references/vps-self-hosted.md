# 自建 VPS 代理 — 完整流程与故障手册

> 基于 2026-07-24 实战：RackNerd $22/年 VPS + 3X-UI + Hysteria2/VMess

## 一、购机与初始化

### 选型原则
- **必须有美国 IP**：Claude/OpenAI API 需要美国 IP，香港/日本不行
- **年付 $12-22**：RackNerd Black Friday 专区，1-2 GB KVM VPS
- **机房**：Los Angeles DC-02 或 San Jose（西海岸延迟最低）
- **系统**：Debian 12，轻量且 3X-UI 兼容最好

### 付款
- 支持支付宝（Stripe 网关），¥158/年
- 地址填香港或加州都可以，不验证
- 邮件收 root 密码，等 2-5 分钟

### 3X-UI 安装

```bash
ssh root@<IP>
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
# 选 SQLite，跳过 SSL
```

安装完会输出面板地址、用户名、密码。**立刻记下来。**

### 开 BBR 拥塞控制

```bash
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

## 二、协议配置

### VMess TCP（最通用，端口 10000）

3X-UI 面板 → 入站 → 添加：
- 协议：vmess
- 端口：10000
- 传输：tcp
- UUID：自生成或手设
- **地址留空**（监听所有接口，千万别填 127.0.0.1）

客户端 vmess 链接格式：
```json
{"v":"2","ps":"US","add":"<IP>","port":"10000","id":"<UUID>","aid":"0","net":"tcp","type":"none","tls":""}
```
然后 `base64` 编码，前面加 `vmess://`。

### Hysteria2（高速，端口 443 UDP）

#### 服务端安装

```bash
# 下载
curl -sL "https://github.com/apernet/hysteria/releases/download/app/v2.10.0/hysteria-linux-amd64" \
  -o /usr/local/bin/hysteria
chmod +x /usr/local/bin/hysteria

# 生成自签名证书（伪装 microsoft.com）
mkdir -p /etc/hysteria
openssl req -x509 -newkey rsa:2048 -keyout /etc/hysteria/key.pem \
  -out /etc/hysteria/cert.pem -days 3650 -nodes -subj '/CN=www.microsoft.com'

# 配置 /etc/hysteria/config.yaml
cat > /etc/hysteria/config.yaml << 'EOF'
listen: :443
tls:
  cert: /etc/hysteria/cert.pem
  key: /etc/hysteria/key.pem
auth:
  type: password
  password: <密码>
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
cat > /etc/systemd/system/hysteria.service << 'EOF'
[Unit]
Description=Hysteria2
After=network.target
[Service]
ExecStart=/usr/local/bin/hysteria server -c /etc/hysteria/config.yaml
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now hysteria
```

#### 客户端配置（hysteria2-config.yaml）

```yaml
server: <IP>:443
auth: <密码>
tls:
  sni: www.microsoft.com
  insecure: true
bandwidth:
  up: 50 mbps
  down: 200 mbps
socks5:
  listen: 0.0.0.0:10808
http:
  listen: 0.0.0.0:10809
```

启动：`hysteria-windows-amd64.exe -c hysteria2-config.yaml`

#### V2Ray/sing-box 版（家里电脑用）

```json
{
  "dns": {"servers": [
    {"address": "119.29.29.29", "domains": ["geosite:cn"], "skipFallback": true},
    "https://cloudflare-dns.com/dns-query"
  ]},
  "inbounds": [{
    "port": 10808, "listen": "127.0.0.1", "protocol": "mixed",
    "settings": {"auth": "noauth", "udp": true}
  }],
  "outbounds": [{
    "tag": "proxy", "protocol": "hysteria",
    "settings": {"address": "<IP>", "port": 443, "version": 2},
    "streamSettings": {
      "network": "hysteria", "security": "tls",
      "tlsSettings": {"allowInsecure": true, "serverName": "www.microsoft.com"},
      "hysteriaSettings": {"version": 2, "auth": "<密码>"}
    }
  }, {"tag": "direct", "protocol": "freedom"}],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {"type": "field", "domain": ["domain:deepseek.com", "geosite:cn"], "outboundTag": "direct"},
      {"type": "field", "ip": ["geoip:private", "geoip:cn"], "outboundTag": "direct"},
      {"type": "field", "outboundTag": "proxy"}
    ]
  }
}
```

> ⚠️ **绝对不能**加 `{"port": "443", "network": "udp", "outboundTag": "block"}` —— Hysteria2 自己就是 UDP 443，这条规则会自残。

### VLESS Reality（GFW 最难识别，端口 34356）

3X-UI → 入站 → 添加：
- 协议：vless
- 端口：34356
- 安全 → Reality
- 目标：www.microsoft.com:443
- SNI：必须手动填（3X-UI bug：只填目标不填 SNI 会导致 `empty "serverNames"` 错误，Xray 启动失败）

**数据库补救**（如果面板 SNI 没存进去）：
```bash
sqlite3 /etc/x-ui/x-ui.db "
SELECT id, settings, stream_settings FROM inbounds WHERE id=1"
# 手动设 serverNames 和 publicKey，改完 restart
```

## 三、致命坑合集

### 坑 1：DNS 污染 ≠ 协议被封
- 症状：VMess/SS/Reality/Hysteria2 全试过都不通，GitHub 能通 Google 不通
- 根因：本地 DNS 返回被污染的假 IP
- 验证：用 IP 直连 `curl --resolve google.com:443:<真实IP>` 如果能通就是 DNS
- 修复：Firefox `socks_remote_dns=true`，或 HTTP 代理模式（服务端解析 DNS）

### 坑 2：VMess 监听 127.0.0.1
- 症状：`ss` 显示端口在听，外网连不上
- 根因：配 nginx 反代时改了 listen，之后忘改回
- 修复：`UPDATE inbounds SET listen='' WHERE id=2; systemctl restart x-ui`

### 坑 3：nginx 自启占 TCP 443
- 之前安装的 nginx 在重启后自动启动，占用 TCP 443
- 修复：`systemctl stop nginx && systemctl disable nginx`
- Hysteria2 用 UDP 443，不受影响

### 坑 4：V2Ray Hysteria2 自残规则
- JSON 里 `UDP 443 → block` 会直接杀死 Hysteria2 自己
- 修复：删掉所有对 UDP 443 的 block 规则

### 坑 5：非标端口被 ISP 封锁
- 端口 10000、8388、34356 在某些运营商下不通
- 只有 80（HTTP）和 443（HTTPS/UDP）稳
- 优先用 443

### 坑 6：运营商级别 IP 封锁
- 同一台 VPS，笔记本能连，家里电脑不能连
- 原因：不同运营商封锁策略不同
- 解法：Cloudflare Tunnel、换 IP（$3）、或链式代理中转

### 坑 7：SSH 被本地代理劫持
- 本地 Clash/V2Ray/Hysteria2 运行时，SSH 流量也会走代理
- 代理挂了 → SSH 也超时
- 修法：每条 SSH 命令前 `unset http_proxy https_proxy ...`

### 坑 8：Clash Verge + Mihomo 崩溃
- 新配置加载后 Mihomo 直接 crash，Clash Verge GUI 打不开
- 修法：`taskkill /F /IM clash-verge.exe & taskkill /F /IM verge-mihomo.exe`
- 放弃 Clash，改用 Hysteria2 CLI 或 sing-box

### 坑 9：pkKCP 格式废弃
- Xray v26 废弃了旧 mKCP header 字段
- 报错：`The feature mkcp header & seed has been removed`
- 改用新格式或放弃 mKCP

## 四、运维速查

```bash
# SSH（配免密后不再弹窗）
# 首次配免密：
ssh-keygen -t rsa -f ~/.ssh/vps_key -N ""
ssh root@<IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys" < ~/.ssh/vps_key.pub
# ~/.ssh/config 加：
#   Host <IP>
#     IdentityFile ~/.ssh/vps_key
#     StrictHostKeyChecking no
#     User root

# 服务状态
systemctl status x-ui hysteria

# 端口
ss -tlnp                    # TCP
ss -ulnp                    # UDP
ss -tlnp | grep -E '10000|34356|20321|22'  # 关键端口

# Xray 日志
journalctl -u x-ui -f

# Hysteria 日志
journalctl -u hysteria -f

# 3X-UI 数据库
sqlite3 /etc/x-ui/x-ui.db "SELECT id, remark, port, protocol, listen FROM inbounds;"

# 改监听地址
sqlite3 /etc/x-ui/x-ui.db "UPDATE inbounds SET listen='' WHERE id=2;"
systemctl restart x-ui

# 防火墙（默认无）
iptables -L -n

# 测连通性
timeout 3 bash -c 'echo > /dev/tcp/<IP>/<PORT>' && echo "OK" || echo "BLOCKED"
```

### 坑 10：Python 3.14 + httpx 版本冲突 → Hermes 初始化超时

```python
# 症状
Failed to initialize agent: cannot import name 'URL' from 'httpx'
```

python 3.14 与 httpx<0.28 不兼容。Hermes 自带 venv：
```cmd
C:\Users\<user>\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m pip install httpx --upgrade
```

### 坑 11：DeepSeek API 走代理绕地球一圈

Hermes 配的 DeepSeek 官方 API，但系统代理把所有流量劫持到美国 VPS 再回国内 → 超时。V2Ray/sing-box 路由里必须加：
```json
{"type": "field", "domain": ["domain:deepseek.com", "geosite:cn"], "outboundTag": "direct"}
```

## 五、Cloudflare Tunnel（运营商封锁终解）

当运营商把 VPS IP 拉黑时，Cloudflare Tunnel 免费中转，让流量看起来是访问 Cloudflare CDN。

### 前提
- 域名一个（.xyz ¥7/年 Porkbun，.xin 需实名阿里云）
- Cloudflare 免费账号

### 步骤

1. 阿里云 DNS 切到 Cloudflare NS（`deb.ns.cloudflare.com` + `drew.ns.cloudflare.com`）
2. Cloudflare → Zero Trust → Networks → Tunnels → Create
3. VPS 装 cloudflared：
```bash
curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
cloudflared service install <token>
```
4. Public Hostname：`vps.yourdomain.com` → `http://localhost:10000`
5. VMess 切 WebSocket 传输，客户端连域名而非 IP
6. Cloudflare 自动签发 SSL 证书，客户端设 `tls: true` 无需 `allowInsecure`

### 流转发路径
```
客户端 → vps.yourdomain.com:443 (Cloudflare CDN, 真实证书)
       → Cloudflare Tunnel (内网穿透)
       → localhost:10000 (Xray VMess+WebSocket)
```

ISP 只能看到用户访问 Cloudflare，看不到背后的 VPS。

## 六、客户端选择

| 客户端 | 协议支持 | 适合场景 |
|------|------|------|
| Hysteria2 CLI | Hysteria2 | 笔记本主力 |
| sing-box | 全协议 | 家里电脑 |
| V2RayN | VMess/VLESS | 简单场景 |
| v2rayNG (Android) | VMess/Hysteria2 | 手机 |
| Nekobox (Android) | 全协议 | 手机 |
| Shadowrocket (iOS) | 全协议 | 手机 |

## 六、浏览器 DNS 全兼容方案

| 方案 | 配置 | 适用 |
|------|------|------|
| **HTTP 代理 (10809)** | Windows 系统代理 `127.0.0.1:10809` | **所有浏览器零配置** |
| Firefox SOCKS5 | `socks_remote_dns=true` | 单浏览器 |
| Chrome SwitchyOmega | 勾"使用代理解析 DNS" | 单浏览器 |

HTTP 代理模式天然服务端解析 DNS，无污染问题，推荐。
