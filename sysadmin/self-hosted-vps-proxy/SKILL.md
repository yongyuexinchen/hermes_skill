---
name: self-hosted-vps-proxy
description: 自建 VPS 代理完整流程：选 VPS、装 3X-UI、配 Reality 协议、生成 Clash 配置。含 3X-UI Reality serverNames 空白坑、数据库直修、Clash Verge 导入方案、VMess 回退策略。
trigger_keywords:
  - 自建代理
  - 搭梯子
  - VPS 翻墙
  - 自己搭 vpn
  - 买 VPS 翻墙
  - 3X-UI
  - Reality 协议
  - VLESS Reality
  - 机场太慢
  - 换机场
  - 自建节点
category: sysadmin
---

# 自建 VPS 代理（3X-UI + Clash Meta）

从零搭建个人代理服务器，替代廉价机场。总成本 ~¥13-22/月，独享带宽，美国原生 IP。

## 前置：判断是否值得自建

读 Clash Verge 配置文件（`%APPDATA%/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml`），检查 `proxies:` 下：
- 多个不同名字的节点指向**同一 IP + 同一密码** → 假节点，机场差
- 域名看起来像随机生成的（如 `hoxdzillavskiong.com`）→ 廉价机场
- 以上红旗 ≥ 3 个 → 建议自建

## 选 VPS

| 需求 | 推荐 | 价格 | 延迟 |
|------|------|------|------|
| AI API（Claude/GPT）需美国 IP | **RackNerd 洛杉矶** | $21.99/年 (≈¥13/月) | 170-180ms |
| 预算宽松、多机房 | Vultr 日本/美国 | $6/月 (≈¥43) | 130-160ms |
| 中文面板、支付宝 | AkileCloud HK/US | ¥10-20/月 | 变化 |

**关键**：Claude API 封禁香港 IP，必须用美国 VPS。

## 协议选择策略

### 🥇 VMess + TCP：首选，从零搭建的第一步

**VMess 纯 TCP 是目前兼容性最好、最稳的协议。** 从零搭建时，先建一个 VMess TCP 入站确认连通，再考虑 Reality/WS/TLS 等高级协议。

3X-UI 创建：协议 `vmess`，传输 `tcp`，端口如 10000。Clash 最简配置：

```yaml
proxies:
  - name: "US"
    type: vmess
    server: VPS_IP
    port: 10000
    uuid: CLIENT_UUID
    alterId: 0
    cipher: auto
    udp: true
```

### 🥈 Reality：进阶，仅在确认 Mihomo 版本支持时使用

Reality 是 GFW 最难识别，但 **Clash Meta/Mihomo 各版本 Reality 支持参差不齐**。常见 `REALITY authentication failed` 即使 VPS 端配置完全正确。优先 VMess TCP 打通，Reality 作为后续优化。

## 完整流程

### Step 1：买 VPS

RackNerd 优惠页：`https://www.racknerd.com/specials/`
- 选 **1 GB KVM VPS**（$21.99/年）就够了
- Location: **Los Angeles DC-02**（西海岸到中国最优）
- OS: **Debian 12**
- 支付：支付宝（Stripe 中间层偶尔崩 → 关 VPN 重试或换 PayPal）

邮件收 `IP + root 密码`。

### Step 2：SSH 连接

```bash
ssh root@<IP>
# 密码在邮件里，输入时不回显
```

如果 SSH 超时但 ping 通 → **代理环境变量劫持了 SSH**。必须先 unset：

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
ssh root@<IP>
```

这个 `unset` 是每轮新 terminal 调用都要做的——环境变量会在 session 间继承。

### Step 3：装 3X-UI

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

安装过程会生成随机端口、用户名、密码、WebBasePath。**一定要记下来**。面板默认 HTTP（无 SSL）。

### Step 4：创建第一个入站（VMess TCP）

1. 浏览器打开面板 `http://<IP>:<port>/<basepath>`
2. 左侧 **入站** → **添加入站**
3. **基础配置**：备注填 `VMess-TCP`，协议选 `vmess`，端口 10000
4. **传输** 标签确认 `tcp`
5. 底部 **添加客户端**，记下 UUID
6. 创建 → 回仪表盘 → **重启 Xray**

> VMess TCP 通了之后再考虑加 Reality 入站。不要一起上，出问题无法定位。

### Step 5：配 Reality 入站（可选，进阶）

1. **入站** → **添加入站**
2. **基础配置**：备注 `US-Reality`，协议 `vless`，端口保持自动
3. **安全** 标签：选 `Reality`，目标 `www.microsoft.com:443`
4. ⚠️ **SNI 必须手动设置**！详见 Pitfall #1
5. 创建 → 添加客户端 → 记 UUID、公钥、Short ID → 重启 Xray

### Step 6：调试 — 侧车日志是关键

连通失败时**直接看 Mihomo 侧车日志**，不要猜：

```
%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\logs\sidecar\sidecar_latest.log
```

关键错误：
- `REALITY authentication failed` → 密钥/SNI/ShortID 不匹配，或 Mihomo 版本不支持 Reality
- `i/o timeout` → 端口不通（先确认 VPS 端 `ss -tlnp | grep xray` + 无防火墙）
- `Process terminated with code: 1` → Clash 配置导致崩溃（切回最简 VMess TCP 配置）

### Step 7：生成 Clash 配置并导入

**Clash Verge 只支持 HTTP URL 导入**。用 Python 临时 HTTP：

```bash
cd "C:/Users/53028/AppData/Roaming/io.github.clash-verge-rev.clash-verge-rev/profiles"
python -m http.server 8888
```

导入 URL：`http://127.0.0.1:8888/<name>.yaml`

模板见 `templates/` 目录。

## Pitfalls

### #1 ⚠️ 3X-UI Reality `serverNames` 为空（致命）

**症状**：入站创建成功，Xray 日志反复：
```
ERROR - XRAY: Failed to start: ... > empty "serverNames"
```

**根因**：3X-UI 面板创建 Reality 入站时，SNI（`serverNames`）不自动从 Target 填充，`publicKey` 也可能为空。

**修复**：直接修 SQLite 数据库（`config.json` 会被 3X-UI 重启覆盖）：

```bash
ssh root@<IP> 'python3 -c "
import sqlite3, json
db = sqlite3.connect(\"/etc/x-ui/x-ui.db\")
row = db.execute(\"SELECT id, stream_settings FROM inbounds WHERE id=1\").fetchone()
settings = json.loads(row[1])
rs = settings[\"realitySettings\"]
rs[\"serverNames\"] = [\"www.microsoft.com\"]
rs[\"publicKey\"] = \"<PUBLIC_KEY>\"
db.execute(\"UPDATE inbounds SET stream_settings=? WHERE id=1\", (json.dumps(settings),))
db.commit()
print(\"Fixed\")
db.close()
" && x-ui restart'
```

### #2 Clash Meta Reality 客户端兼容性

即使 VPS 端完全正确，Mihomo 仍可能报 `REALITY authentication failed`。**这不是配置错误，是 Mihomo 版本问题**。应对：切到 VMess TCP 协议。

### #3 SSH 被代理劫持

每次 `terminal()` 调用继承上一个 session 的环境变量。SSH 超时时先 `unset` 所有代理变量再试。如果还不行，检查 `~/.ssh/config` 有没有 `ProxyCommand`。

### #4 调试时关掉本地 Clash

Clash 开着时所有流量（包括 SSH）走代理，VPS 还没配通就变成死循环。调试 VPS 时先退出 Clash（右键任务栏图标 → 退出）。

## 模板

- `templates/clash-reality-config.yaml`：完整的 Clash Meta Reality 配置
- `templates/clash-vmess-tcp-config.yaml`：最简 VMess TCP 配置（调试首选）
