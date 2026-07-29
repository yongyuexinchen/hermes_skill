---
name: china-vps-proxy
description: 在中国大陆网络下自建 VPS 代理全流程：买 VPS、装面板、配协议、DNS 污染处理、ISP 封锁对策。含 3X-UI/Hysteria2/VMess/Reality 实战经验。
category: sysadmin
trigger_keywords:
  - 自建代理
  - 搭梯子
  - VPS 翻墙
  - 机场太慢
  - 买 VPS 代理
  - 搭 VPN
  - Hysteria2
  - 3X-UI
  - Reality 配置
  - VMess 配置
  - DNS 污染
  - 代理连不上
---

# 中国大陆自建 VPS 代理

## 触发条件

用户抱怨现有机场慢/不稳定，想自建 VPS 代理；或已有 VPS 但代理连不上。

## 核心认知

### 三大坑（按排查顺序）

| 优先级 | 问题 | 症状 | 解法 |
|--------|------|------|------|
| 1️⃣ | **DNS 污染** | 部分站点打不开（Google/YouTube），其他 OK | 远程 DNS：Firefox `socks_remote_dns=true` 或用 HTTP 代理 |
| 2️⃣ | **ISP 协议阻断** | 非标端口（≠80/443）超时 | 走 80/443 端口，套 TLS 伪装成 HTTPS |
| 3️⃣ | **物理延迟** | 看视频卡、大文件慢 | ¥13/月 US VPS 就是 ~174ms，无解。要速度加钱换 HK/CN2 |

### 协议选择优先级

1. **Hysteria2**（首选）— UDP 暴力加速，高延迟表现最好，伪装成 HTTPS
2. **VMess + WebSocket + TLS** — 最兼容，走 443 端口，ISP 看起来像 HTTPS
3. **Shadowsocks** — 最简单，但容易被 ISP 识别
4. **Reality** — 理论上最强，但客户端兼容性差（Mihomo 经常认证失败）

### VPS 选型

- **预算方案（¥13/月）**：RackNerd 美国 KVM VPS，$22/年，1GB RAM，3TB 流量
  - 适合：GitHub、API 调用、网页浏览
  - 不适合：视频、大文件下载
- **速度方案（¥30-50/月）**：香港/日本 VPS，30-50ms 延迟
- **极致方案（¥100-200/月）**：CN2 GIA 线路，看视频无压力

## 标准搭建流程

### 1. 买 VPS

RackNerd → Black Friday 专区 → 1 GB KVM VPS：
- 位置选 Los Angeles DC-02（西海岸延迟最低）
- 系统选 Debian 12
- 支付宝付款
- 账单地址填香港或美国地址均可

### 2. 装 3X-UI 面板

```bash
ssh root@<IP>
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```
选 SQLite，跳过 SSL。

### 3. 配 Reality（3X-UI 坑）

⚠️ **致命坑**：3X-UI 不会自动保存 SNI 到 `serverNames`，配完必须手动修数据库：

```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
row = db.execute('SELECT * FROM inbounds WHERE id=1').fetchone()
settings = json.loads(row[5])  # stream_settings 列
rs = settings['realitySettings']
rs['serverNames'] = ['www.microsoft.com']
rs['publicKey'] = '<你的公钥>'
db.execute('UPDATE inbounds SET stream_settings=? WHERE id=1', (json.dumps(settings),))
db.commit()
" && x-ui restart
```

### 4. 开 BBR 加速

```bash
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

### 5. DNS 污染终极解法

| 客户端 | 方法 |
|--------|------|
| Firefox | `about:config` → `network.proxy.socks_remote_dns` → `true` |
| Chrome/Edge | 装 SwitchyOmega，勾选"使用代理服务器解析 DNS" |
| 全浏览器 | 用 **HTTP 代理** 而非 SOCKS5（HTTP 天然服务端解析 DNS） |
| Clash | `enhanced-mode: fake-ip` + `nameserver: 8.8.8.8`（但 Mihomo 经常崩） |

### 6. Hysteria2（最终推荐）

```bash
# VPS 端
curl -sL "https://github.com/apernet/hysteria/releases/download/app/v2.10.0/hysteria-linux-amd64" \
  -o /usr/local/bin/hysteria
chmod +x /usr/local/bin/hysteria

# 配置 /etc/hysteria/config.yaml
listen: :443
tls:
  cert: /etc/x-ui/certs/cert.pem
  key: /etc/x-ui/certs/key.pem
auth:
  type: password
  password: <密码>
masquerade:
  type: proxy
  proxy:
    url: https://www.microsoft.com
    rewriteHost: true
```

客户端配置见 `templates/hysteria2-client.yaml`。

## 排错速查

| 症状 | 可能原因 | 检查 |
|------|----------|------|
| 所有站点打不开 | VPS 挂了 / 端口被封 | `ping <IP>` → `ss -tlnp` |
| 部分站点打不开 | DNS 污染 | 换远程 DNS |
| Reality 认证失败 | serverNames 没保存 | 查数据库 |
| mKCP 报错 | Xray v26 废弃旧格式 | 换 TCP 或 KCP v2 格式 |
| Clash 加载就崩 | Mihomo 兼容性 | 放弃 Clash，用 V2RayN/Hysteria |
| 非 80/443 端口超时 | ISP 封锁非标端口 | 换 80/443 |
| 延迟高 | 物理距离 | 正常。US VPS 就是 170ms+ |

## 参考资源

- `references/racknerd-setup.md` — RackNerd 购买和初始配置细节
- `templates/hysteria2-client.yaml` — Hysteria2 Windows 客户端配置模板
- `references/3x-ui-common-pitfalls.md` — 3X-UI 面板常见坑
