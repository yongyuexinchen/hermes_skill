---
name: self-hosted-proxy
description: 自建 VPS 代理全流程：买 VPS → 装 3X-UI → 配协议 → 接 Clash Verge。RackNerd、Reality 协议、常见故障排查。
trigger_keywords:
  - 自建代理
  - 搭梯子
  - 买 VPS
  - 3X-UI
  - X-ui
  - Reality
  - VLESS
  - VMess
  - RackNerd
  - 代理太慢
  - 换机场
  - 搭节点
---

# 自建 VPS 代理全流程

## 触发条件

用户抱怨 VPN/机场太慢、频繁断连，或主动要求自建代理。

## 流程概览

1. **选 VPS** → 2. **买 VPS** → 3. **装 3X-UI** → 4. **配协议** → 5. **接 Clash**

---

## 1. 选 VPS

### 需要美国 IP（Claude/Cursor 等 AI 工具）
- **RackNerd**：$21.99/年 (≈¥13/月)，1GB RAM，3TB 流量，洛杉矶/圣何塞
- **Vultr**：$6/月，日本/新加坡，更灵活但贵

### 只需要亚洲 IP
- **AkileCloud**：¥9.9/月，香港/日本，支付宝

### 用户预算 ≤¥30/月 → 推荐 RackNerd 1GB 套餐

---

## 2. 买 VPS（RackNerd）

### 关键选项
- **Location**：Los Angeles DC-02 或 San Jose（西海岸到中国最快）
- **OS**：Debian 12
- **支付**：支付宝（Stripe 中转）

### ⚠️ 支付坑
- **Stripe 支付宝支付页报错**："系统异常" → **关掉 VPN/代理** 再刷支付页。挂着慢代理访问 Stripe 支付宝网关会超时崩。
- 账单地址填香港和美国都行，不验证。电话号码可留空。
- QQ 邮箱能收国际邮件，垃圾箱翻一下

---

## 3. 装 3X-UI

```bash
# SSH 连上 VPS 后一条命令
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

安装后输出：
- 面板 URL + 端口
- 用户名 / 密码
- WebBasePath（URL 路径前缀）

**安全提醒**：装完立即截图保存凭据。

---

## 4. 配协议

### ⚠️ 协议选择铁律：从简到繁，逐步验证

**不要一上来就用 Reality！** 按以下顺序逐步验证：

| 顺序 | 协议 | 目的 | 端口 |
|------|------|------|------|
| 1 | **Shadowsocks** (aes-256-gcm) | 验证 VPS 网络可达 | 8388 |
| 2 | **VMess + TCP** | 验证 VMess 握手 | 10000 |
| 3 | **VMess + WebSocket** | 可套 CDN 隐藏 IP | 10000 |
| 4 | **VLESS + Reality** | 最强抗封锁 | 34356 |

**铁律：先用 SS 验证 VPS 可达，通了再往上升级。** 一步到位上 Reality 大概率翻车——Mihomo 对 Reality 的支持不稳定，Reality authentication failed 是高频问题且无优雅解法。

### Shadowsocks（第一步验证）

**面板操作**：
1. 入站 → 添加入站
2. 协议选 **shadowsocks**，端口 8388
3. 加密方法选 **aes-256-gcm**，密码用 `zt2nnfr2bstjeu94`（用户已有的 Hysteria 认证密码）
4. 传输 tab → tcp
5. 创建 → 重启 Xray

**生成 SS 链接**：
```bash
echo -n "aes-256-gcm:密码@IP:8388" | base64 -w0
# 链接格式: ss://BASE64#名称
```

SS 链接可导入 V2RayN 或任何 SS 客户端。

### VMess + TCP（第二步，Clash 兼容性最好）

```yaml
proxies:
  - name: "US"
    type: vmess
    server: VPS_IP
    port: 10000
    uuid: UUID
    alterId: 0
    cipher: auto
    udp: true
```

### VMess + WebSocket（第三步）

```yaml
proxies:
  - name: "US-VMess"
    type: vmess
    server: VPS_IP
    port: 10000
    uuid: UUID
    alterId: 0
    cipher: auto
    network: ws
    ws-opts:
      path: /ws
```

### Reality 协议（最后一步，GFW 最难识别但兼容性最差）

**⚠️ 三个致命坑**：

#### 坑1：面板 UI 不保存 serverNames 和 publicKey
3X-UI v3.5.0 的 Reality 安全设置页，填了 Target 和 SNI 后**创建入站不会把这些值写入数据库**。必须手动修：

```python
import sqlite3, json
db = sqlite3.connect("/etc/x-ui/x-ui.db")
row = db.execute("SELECT id, stream_settings FROM inbounds WHERE id=1").fetchone()
settings = json.loads(row[1])
settings["realitySettings"]["serverNames"] = ["www.microsoft.com"]
settings["realitySettings"]["publicKey"] = "PUBLIC_KEY_HERE"
db.execute("UPDATE inbounds SET stream_settings=? WHERE id=1", (json.dumps(settings),))
db.commit()
```

#### 坑2：直接改 config.json 会被面板覆盖
3X-UI 重启时会从数据库重新生成 `config.json`。必须改数据库。

#### 坑3：Mihomo Reality 认证失败
症状：sidecar 日志 `REALITY authentication failed`，但 TCP 连接成功（端口可达）。这是 Mihomo 与 Xray Reality 握手实现差异，**无优雅解法**。降级到 Shadowsocks 或 VMess。

### 当 API 不可用时：SQLite 直写创建入站

```bash
ssh root@VPS_IP "python3 << 'PYEOF'
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')

# 用已存在的行作模板
row = db.execute('SELECT * FROM inbounds WHERE id=1').fetchone()
cols = [c[1] for c in db.execute('PRAGMA table_info(inbounds)')]
tmpl = dict(zip(cols, row))

# 修改为想要的值
settings = json.dumps({'clients': [{'password': 'PWD', 'method': 'aes-256-gcm'}]})
stream = json.dumps({'network': 'tcp', 'security': 'none'})

tmpl['id'] = None; tmpl['remark'] = 'SS'; tmpl['port'] = 8388
tmpl['protocol'] = 'shadowsocks'; tmpl['settings'] = settings
tmpl['stream_settings'] = stream; tmpl['tag'] = 'inbound-8388'

placeholders = ','.join(['?'] * len(cols))
colnames = ','.join(cols)
vals = [tmpl[c] for c in cols]
db.execute(f'INSERT INTO inbounds ({colnames}) VALUES ({placeholders})', vals)
db.commit()
db.close()
PYEOF"
x-ui restart
```

---

## 5. 客户端连接

### ⚠️ 客户端选择优先级

| 优先级 | 客户端 | 说明 |
|--------|--------|------|
| 1 | **SSH 隧道** | 零安装，验证网络最快：`ssh -D 10808 -N root@IP` |
| 2 | **V2RayN** | 协议支持全，导入 vmess:// / ss:// 链接即用，比 Clash 稳 |
| 3 | **Clash Verge Rev** | 规则分流强，但 Reality 兼容性差，VMess 也可能因 Mihomo 版本问题失败 |

**当 Clash 反复失败时，立刻切 V2RayN 或 SSH 隧道，不要死磕。**

### SSH 隧道（最快验证）

```bash
# git-bash 里跑（不能用 cmd——cmd 的 SSH 可能不认密码）
ssh -D 10808 -N root@VPS_IP
# 密码不显示，粘完回车
```

然后 Windows 设置 → 代理 → 手动 → SOCKS5：`127.0.0.1:10808`。绕过所有客户端直接验证 VPS 是否可用。

### V2RayN

1. 下载 [V2RayN](https://github.com/2dust/v2rayN/releases) 最新版 zip，解压即用
2. 复制 vmess:// 或 ss:// 链接 → 服务器 → 从剪贴板导入
3. 设为活动服务器 → 系统代理 → 自动配置

### Clash Verge Rev

**配置文件放在正确位置**：`%APPDATA%/io.github.clash-verge-rev.clash-verge-rev/profiles/`

**导入必须用 URL**，本地文件不会自动出现在列表。启 Python HTTP 服务：
```bash
cd "配置文件目录"
python -m http.server 8888
```
Clash Verge → 导入 → URL：`http://127.0.0.1:8888/config.yaml`

### 配置切换后排查

1. **查 Mihomo 内核日志**（不在面板日志里）：
   ```
   %APPDATA%/io.github.clash-verge-rev.clash-verge-rev/logs/sidecar/sidecar_latest.log
   ```
   这里能看到 `REALITY authentication failed`、`i/o timeout` 等底层错误。

2. **查 VPS Xray 日志**：
   ```bash
   ssh root@VPS_IP "journalctl -u x-ui --no-pager -n 20"
   ```

3. **Clash 崩溃**：如果 Clash Verge 打不开，用 taskkill 杀干净：
   ```bash
   taskkill /F /IM "clash-verge.exe"
   taskkill /F /IM "verge-mihomo.exe"
   ```
   然后重开。

---

## 6. DNS 污染——代理不通的首要嫌疑

**国内环境下，90% 的"代理不通"不是协议被封，而是 DNS 污染。**

### 诊断三步法

1. **VPS 能否直接访问目标**（排除 VPS 侧问题）：
   ```bash
   ssh root@VPS 'curl -sk -o /dev/null -w "%{http_code}" --max-time 5 https://www.google.com'
   ```
   返回 200 = VPS 侧没问题。

2. **直连 IP 绕过 DNS**（确认 DNS 污染）：
   ```bash
   curl --socks5 127.0.0.1:10808 --resolve www.google.com:443:<VPS上解析到的真实IP> -sk https://www.google.com
   ```
   能通 = 确认 DNS 污染。

3. **用已知真实 IP 验证**：
   ```bash
   curl --socks5 127.0.0.1:10808 -sk https://142.251.155.119  # Google IP
   ```

### 解决方案（按优雅度排序）

| 方案 | 适用 | 操作 |
|------|------|------|
| **Clash Fake-IP** | 所有浏览器零配置 | `enhanced-mode: fake-ip` + `nameserver: [8.8.8.8]` |
| **Firefox** | 单浏览器 | `about:config` → `socks_remote_dns` → `true` |
| **Chrome + SwitchyOmega** | 单浏览器 | 装插件，勾选"使用代理服务器解析 DNS" |
| **HTTP 代理** | 所有浏览器零配置 | 用 HTTP 代理（不是 SOCKS5），服务端解析 DNS |

**为什么 SOCKS5 和 HTTP 代理不同？** SOCKS5 默认由**客户端**解析 DNS（本地中国 DNS → 得到被污染的 IP），HTTP CONNECT 代理由**服务端**解析 DNS（走 VPS 的美国 DNS → 得到真实 IP）。

### Fake-IP 极简 Clash 配置

```yaml
dns:
  enable: true
  enhanced-mode: fake-ip          # ← 核心：劫持所有 DNS 走代理
  fake-ip-range: 198.18.0.1/16
  nameserver:
    - 8.8.8.8
    - 1.1.1.1
  fallback:
    - 223.5.5.5
  fallback-filter:
    geoip: true
    geoip-code: CN
```

开了 Fake-IP 后，Chrome/Edge/Firefox 全部零配置就能用。

## 7. Hysteria2——高延迟网络加速

Hysteria2 是 UDP-based 协议，专为高延迟/丢包网络设计。比 VMess TCP 快但**不能突破物理延迟天花板**。

### VPS 安装

```bash
curl -sL "https://github.com/apernet/hysteria/releases/download/app/v2.10.0/hysteria-linux-amd64" -o /usr/local/bin/hysteria
chmod +x /usr/local/bin/hysteria
```

服务端配置见 `templates/hysteria2-server.yaml`。
客户端配置见 `templates/hysteria2-client.yaml`。

### ⚠️ 版本更新
Hysteria2 更新频繁（v2.6.1 → v2.10.0），VPS 和客户端**必须同版本**，否则协议不兼容。更新后 `systemctl restart hysteria`。

### ⚠️ V2Ray/Xray 路由规则自杀陷阱

**用 V2Ray/Xray 做 Hysteria2 客户端时，最常见的失败原因：路由规则误杀了自己的 UDP 流量。**

Hysteria2 走 UDP 443 端口。如果在 routing 里写了：
```json
{ "type": "field", "port": "443", "network": "udp", "outboundTag": "block" }
```
这条规则会把 Hysteria2 自己的 UDP 443 连接直接丢弃——**代理还没建立就被杀了**。

**排查**：检查 V2Ray 配置的 `routing.rules`，确保没有 `"outboundTag": "block"` 指向 UDP 流量的规则。完整工作配置见 `templates/v2ray-hysteria2.json`。

### 手机客户端
- **Android Nekobox**：支持 Hysteria2 直连，链接格式 `hysteria2://password@IP:443?sni=www.microsoft.com&insecure=1#Name`
- **iOS Shadowrocket / Sing-box**：手动填地址 `IP:443`，密码，SNI `www.microsoft.com`，允许不安全

### systemd 服务
```ini
[Unit]
Description=Hysteria2
After=network.target
[Service]
ExecStart=/usr/local/bin/hysteria server -c /etc/hysteria/config.yaml
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

## 8. Nginx 前端伪装（可选）

当 ISP 封锁非标准端口时，用 Nginx 在 443 端口做 TLS 终止，内部转发 WebSocket 给 Xray：

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/x-ui/certs/cert.pem;
    ssl_certificate_key /etc/x-ui/certs/key.pem;

    location / { root /var/www/html; }  # 伪装成正常网站

    location /ws {
        if ($http_upgrade != "websocket") { return 404; }
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Xray 入站改为 `listen: 127.0.0.1`（只监听内网，由 Nginx 转发）。

**⚠️ 恢复注意**：停用 Nginx 后必须把 Xray 的 listen 改回 `""`（空 = 0.0.0.0），否则外网连不上。检查：`ss -tlnp | grep 10000`，看到 `127.0.0.1:10000` 就是锁在内网了。

## 9. 运营商封锁——同 VPS 不同网络表现不同

**同一台 VPS，不同运营商/不同网络封锁策略完全不同。** 常见场景：笔记本（运营商 A）能连，家里电脑（运营商 B）所有 TCP 端口超时，只有 ICMP ping 通。

### 诊断
- 从能通的网络 SSH 上去确认服务正常
- 从不通的网络 `ping` VPS（通 = 不是 IP 全封，是 TCP/UDP 被拦）
- 从不通的网络 `curl` 裸 TCP 端口 → 超时 = 运营商 DPI 封锁

### 解法

| 方案 | 成本 | 说明 |
|------|------|------|
| **Cloudflare Tunnel** | 域名 ¥7/年 | CF 中转，ISP 看不到真实 IP，首发推荐 |
| **换 VPS IP** | $3 一次性 | RackNerd 面板换 IP，赌新 IP 没被封 |
| **链式代理** | 0 | 走现有能通的机场中转，配置复杂 |

### Cloudflare Tunnel 完整流程

**前置**：阿里云买域名（`.xin` 需实名认证，上传身份证几分钟过）。NS 切换后生效需几分钟到 2 小时，`curl` 测试确认 `HTTP 400` 即表示隧道转发成功。

**关键教训：不要用 Cloudflare CDN 橙色云（Proxy mode）直代代理流量。** CDN 会在 WebSocket 上注入 `X-Forwarded-For` 等 HTTP 头，破坏 VLESS/VMess 握手。代理协议必须走 Tunnel 或关橙色云（DNS only）。

**1. 阿里云 DNS 解析**（过渡用）：
- 添加 A 记录：`@` → VPS IP，`www` → VPS IP

**2. Cloudflare 注册 → 添加站点**：
- 输入域名，选 Free 套餐
- CF 会显示两个 NS 服务器（如 `deb.ns.cloudflare.com`, `drew.ns.cloudflare.com`）

**3. 阿里云切 NS**：
- 域名控制台 → DNS 修改 → 自定义 DNS
- 填入 CF 的两个 NS，删掉原有的 `dns13/14.hichina.com`
- 等待生效（几分钟到 2 小时）

**4. VPS 装 cloudflared**：
```bash
curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

**5. CF Zero Trust → Networks → Tunnels → Create**：
- 命名，复制 token 命令
- VPS 上跑：`cloudflared service install <token>`（root 用户不加 sudo）
- 确认：`systemctl status cloudflared`

### ⚠️ cloudflared 远程模式忽略本地 config.yml

`cloudflared service install <token>` 启动后使用**仪表盘远程配置**——所有路由规则在 Cloudflare Dashboard 管理。本地写的 `/etc/cloudflared/config.yml` **被忽略**。

验证当前模式：
```bash
ps aux | grep cloudflared
# 输出含 --token-file → 远程模式，Dashboard 管理
```

想改路由：去 CF Dashboard → Zero Trust → Networks → Tunnels → 点 Tunnel 名 → Public Hostname → Edit URL。

**6. Public Hostname 配置**：
- Subdomain: `vps`（或其他）
- Domain: 你的域名
- Type: `HTTP`
- URL: `localhost:10000`（Xray VMess+WS 端口，填 `http://` 不是 `https://`）

**7. VPS 端 VMess 必须切 WebSocket**：
Tunnel 只转发 HTTP/WebSocket，不走裸 TCP。在 3X-UI 面板或 SQLite 改 `stream_settings.network = "ws"`。

**8. 客户端配置**：
- 地址：`vps.你的域名`
- 端口：`443`
- 传输：`ws`，路径：`/ws`
- TLS：开（CF 提供正规证书，不需 `allowInsecure`）
- 运营商看到的就是普通 HTTPS 到 Cloudflare CDN

## 10. 诚实边界——廉价 VPS 的能力上限

| ¥13/月 US VPS 能做到 | 做不到 |
|------|------|
| GitHub 克隆/推送 | 看 YouTube/Netflix |
| Claude/GPT API 调用 | 视频会议 |
| Stack Overflow / Google | 打外服游戏 |
| HuggingFace 下模型 | 刷 TikTok |

**174ms 是中美物理延迟天花板。** 要看视频需要香港 CN2 GIA VPS（¥100-200/月，30ms 延迟）。

---

## 常见故障排查

| 症状 | 原因 | 修复 |
|------|------|------|
| Xray 启动失败 `empty "serverNames"` | Reality 没填 SNI | 面板安全 tab 填 Target + SNI，或改数据库 |
| `REALITY authentication failed` | Mihomo/Xray 握手实现差异 | **降级到 Shadowsocks 或 VMess，不要死磕** |
| 面板改了配置不生效 | 直接改 config.json 被覆盖 | 改数据库 `/etc/x-ui/x-ui.db` |
| SSH 连不上 VPS | 本地代理劫持了 SSH | 关代理或 `unset http_proxy...` 后直连 |
| Clash 导入后代理不通 | 看 sidecar_latest.log | 确认协议格式和密钥正确 |
| Clash Verge 打不开/崩溃 | 上次配置导致 Mihomo 崩溃 | `taskkill /F /IM verge-mihomo.exe` 杀干净 |
| VMess TCP 端口超时 | 本地代理环境变量干扰 | 确认 Clash 未在后台运行 |
| **Google 不通但 GitHub 通** | **DNS 污染** | Fake-IP / socks_remote_dns / HTTP代理 |
| Hysteria 连不上 | VPS/客户端版本不一致 或 **V2Ray 路由误拦 UDP 443** | 两边都更新到同一版本；删掉 `UDP 443 → block` 路由规则 |
| gost HTTP 代理部分站点超时 | 被访问站点封锁数据中心 IP | 正常现象（Google 不封，OpenAI 封 421） |
| **VMess 端口外网不通** | **Xray 监听在 127.0.0.1** | 改 `listen=""` 或 `"0.0.0.0"`，检查 `ss -tlnp` |
| **V2RayN allowInsecure 不可用** | Xray 26.x 废弃了 `allowInsecure`，改用 `pinnedPeerCertSha256` | 用 Cloudflare Tunnel（正规证书）或生成证书 pin |
| **mKCP 配置报错 `header & seed has been removed`** | Xray 26 废弃了旧 mKCP 格式 | 放弃 mKCP，用 Hysteria2 或 TCP |
| **Cloudflare CDN 橙色云破坏 WebSocket** | CF CDN 代理在 WS 上加 HTTP 头（X-Forwarded-For） | 用 Tunnel 而非 CDN 直代；或用 nginx 前端 |
| **Cloudflare Tunnel 的 HTTP hostname 选 `http://` 不是 `https://`** | Tunnel 内部不走 TLS | URL 填 `http://localhost:PORT` |
| **SSH 弹窗审批烦人** | 没配 SSH 免密 | `ssh-keygen` + `~/.ssh/config` 配 `IdentityFile` + `StrictHostKeyChecking no` |
| **SSH 反复弹密码框** | 没配免密 | `ssh-keygen` + `ssh-copy-id`，写入 `~/.ssh/config` |
| **cloudflared 写的 config.yml 不生效** | `service install` 用远程模式，本地配置被忽略 | Dashboard Public Hostname 改路由；或切本地模式 |

## 验证清单

- [ ] VPS 能 SSH 直连（`unset` 代理变量后测）
- [ ] 面板能打开：`http://IP:PORT/BASEPATH`
- [ ] 先用 VMess TCP / Shadowsocks 验证链路通
- [ ] Xray 日志无 ERROR
- [ ] 用真实 IP 直连测试确认 DNS 污染 vs 协议问题
- [ ] Fake-IP DNS 或 socks_remote_dns 已配置
- [ ] `curl --socks5 127.0.0.1:10808 --resolve google.com:443:142.251.155.119 -sk https://google.com` 返回 200
- [ ] 多浏览器验证通过
