---
name: china-vps-self-host-proxy
description: 从中国大陆自建 VPS 代理完全指南——选 VPS、装面板、选协议、绕过 GFW/ISP 封锁。涵盖 3X-UI 部署、协议逐层调试方法论、HTTP CONNECT 兜底方案。
category: sysadmin
trigger_keywords:
  - 自建代理
  - 搭梯子
  - VPS 翻墙
  - 自己搭 VPN
  - 买 VPS 代理
  - 机场太慢
  - 换机场
  - 3X-UI
  - Xray 面板
  - Reality 协议
  - VMess TLS WebSocket
---

# 中国大陆自建 VPS 代理完整指南

## 触发条件
用户表示当前机场/代理慢、不稳定、想自建 VPS，或询问"自己搭梯子难不难/成本多少"。

## 选 VPS

### 核心约束
- 必须支持支付宝/微信（国内支付）
- 需要美国 IP（Claude、Cursor 等 AI 工具封香港 IP）
- 预算通常 ¥30/月以内

### 推荐方案

| 商家 | 价格 | 机房 | 支付 |
|------|------|------|------|
| **RackNerd** | $21.99/年 (≈¥13/月) | 🇺🇸洛杉矶/圣何塞 | 支付宝(Stripe) |
| AkileCloud | ¥9.9/月起 | 🇭🇰/🇯🇵/🇺🇸 | 支付宝/微信 |
| Vultr | $6/月 | 🇯🇵/🇸🇬/🇺🇸 | PayPal |

**首选 RackNerd**：1GB/1核/20GB/3TB，¥158/年，延迟 170-200ms。

### 购买注意事项
- 账单地址填香港或美国地址（不验证）
- 电话不是必填，留空
- 支付宝走 Stripe 中间层偶尔崩，关掉 VPN 重试或换 PayPal
- 邮箱用 QQ 邮箱没问题
- 操作系统选 **Debian 12**

## 部署 3X-UI 面板

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

安装后获得到面板地址、用户名、密码、端口。**立即保存**。

## Cloudflare 域名（辅助，非代理方案）

域名可用于：
- 伪装 VPS 入口（A 记录橙色云 + 80/443 HTTP 服务）
- 为家里被封 IP 的电脑提供 Cloudflare Tooel SSH 入口（需 Zero Trust + cert.pem）
- 为未来 AI 项目做应用入口（FastAPI → CF CDN → VPS）

**Cloudflare 不能做代理协议透传**（VLESS/VMess/SS 帧被 WAF 丢弃，Tunnel HTTP 模式不支持 SSH）。\n**唯一可用的 CF Tunnel 用途**：ttyd 网页终端管理 VPS（`ssh.yourdomain.xin → Tunnel → ttyd:7681 → bash`）。\n详见 `references/cloudflare-limitations.md`。

## ⚠️ 协议选择策略（关键）

### 铁律：逐层验证，不要同时试多个协议

中国 ISP 的封锁是分层级的：
1. **网络层**：IP 本身是否可达（ping）
2. **传输层**：端口是否开放（80/443 vs 非标准端口）
3. **协议层**：代理协议是否被 DPI 识别

### 工程排障方法论：一次只验证一层

**核心原则**：不要一次引入 VPS + Xray + Cloudflare + Tunnel + TLS + WS + DNS 所有变量。从最简单的开始，逐层叠加。

1. **裸 HTTP**：`curl http://VPS_IP` → 验证网络层通
2. **加 CDN**：`curl https://域名` → 验证 DNS + CDN 转发
3. **加 Tunnel**：CF Tunnel → nginx → 验证 Tunnel 本地转发
4. **加协议**：替换 nginx 为目标服务

每层通过才加下一层，问题必在某层。

### 调试流程（必须按此顺序）

#### Layer 1：验证 TCP 连通性
```bash
ping VPS_IP          # 丢包率
curl http://VPS_IP   # 80 端口是否通
```

#### Layer 2：验证标准端口
**关键洞察**：很多国内 ISP 只放行 80 和 443 端口，其他端口全封。

如果 Layer 1 通但代理不通，**立刻换 80 或 443 端口再试**，不要花时间调协议参数。

#### Layer 3：验证代理协议
先试最简单的 Shadowsocks，再试 VMess，最后试 Reality。

### 已知陷阱

| 问题 | 症状 | 解决 |
|------|------|------|
| Reality `empty serverNames` | Xray 反复重启失败 | 3X-UI 面板的 SNI 字段不会自动填，需手动设置或用 SQLite 改数据库 |
| Reality `authentication failed` | Mihomo 连不上 | Clash Meta 版本可能不兼容，检查 Mihomo 版本；Reality 密钥对需验证 |
| ISP 封锁非标准端口 | 10000/8388/34356 等端口超时 | **只用 80 或 443** |
| ISP DPI 识别代理协议 | VMess/SS 全部不通，但 HTTP 裸奔能通 | 用 TLS 伪装（Nginx 前端 + WebSocket），或直接用 HTTP CONNECT 代理 |

## 终极兜底：HTTP CONNECT 代理

当所有代理协议都被 ISP 封锁时，**纯 HTTP CONNECT 代理跑在 80 端口**是最可靠的方案。ISP 看到的就是普通 HTTP 流量。

### VPS 端部署

```bash
# 停止 nginx 释放 80 端口
systemctl stop nginx

# 启动 Python HTTP 代理（保存为 /usr/local/bin/http-proxy.py）
nohup python3 -c "
import socket, select, threading
def relay(a,b):
  try:
    while True:
      r,_,_=select.select([a,b],[],[],30)
      if not r: break
      for s in r:
        d=s.recv(8192)
        if not d: return
        (b if s is a else a).sendall(d)
  except: pass
def handle(c):
  try:
    d=c.recv(8192)
    if not d: return
    l=d.split(b'\r\n')[0].decode()
    if l.startswith('CONNECT'):
      h,p=l.split()[1].split(':')
      r=socket.create_connection((h,int(p)),10)
      c.sendall(b'HTTP/1.1 200\r\n\r\n')
      relay(c,r); r.close()
  except: pass
  finally: c.close()
s=socket.socket(); s.setsockopt(1,2,1)
s.bind(('0.0.0.0',80)); s.listen(50)
while True:
  c,_=s.accept()
  threading.Thread(target=handle,args=(c,),daemon=True).start()
" > /dev/null 2>&1 &
```

### 客户端配置
Windows 设置 → 网络 → 代理 → 手动：
- 地址：`VPS_IP`
- 端口：`80`

## Nginx 前端伪装（进阶）

当 ISP 允许 443 端口但 DPI 识别 VMess 时：

```
Client → TLS → Nginx(:443) → WebSocket → Xray(127.0.0.1:10000)
```

1. 生成自签名证书
2. Nginx 监听 443，处理 TLS
3. `/ws` 路径代理 WebSocket 到 Xray 本地端口
4. 其他路径返回正常网页（伪装）

这样 ISP 看到的是标准 Nginx HTTPS 服务器。

## 3X-UI 数据库修复

面板有时不写完整配置到 config.json，需直接操作 SQLite：

```python
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
# 查 inbounds
for r in db.execute('SELECT id, remark, port, protocol FROM inbounds'):
    print(r)
# 修复 Reality
settings = json.loads(row[stream_settings_column])
settings['realitySettings']['serverNames'] = ['www.microsoft.com']
settings['realitySettings']['publicKey'] = 'PUBLIC_KEY'
db.execute('UPDATE inbounds SET stream_settings=? WHERE id=?', (json.dumps(settings), id))
db.commit()
```

## SSH 连接问题

- 用 git-bash 而非 cmd（cmd 的 SSH 密码粘贴有问题）
- 密码输入时不显示字符（正常）
- 如果超时：先 `unset http_proxy https_proxy` 清除代理环境变量
- 先关掉 Clash/V2RayN 再 SSH（代理会劫持 SSH 流量）
- Windows 的 `sshpass` 不可用，用 Python paramiko 替代（但注意 venv site-packages 路径问题）

## 验证清单
- [ ] ping VPS 延迟 <200ms，0% 丢包
- [ ] curl http://VPS_IP 返回网页（80 端口通）
- [ ] curl -sk https://VPS_IP 返回网页（443 端口通）
- [ ] 代理协议选定后，先用 curl 从本地测试连通性
- [ ] 客户端配置后，浏览器打开 google.com 验证
- [ ] 确认 Claude/OpenAI API 可访问（美国 IP）
