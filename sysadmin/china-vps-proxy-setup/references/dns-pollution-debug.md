# DNS 污染诊断流程

## 症状识别

**关键特征**：部分外网能通，部分不能。典型：
- GitHub ✅ → Google ❌
- Bing ✅ → YouTube ❌

## 三步确诊

### 1. 测基础连通性
```bash
ping VPS_IP  # 0%丢包=网络通
```

### 2. 终极测试：HTTP 裸奔
VPS 上装 nginx：
```bash
apt install nginx -y
```
浏览器访问 `http://VPS_IP`。看到 nginx 欢迎页 = **网络能通，问题在 DNS/代理协议**。

### 3. IP 直连排除 DNS
```
https://142.251.155.119  # Google 已知 IP
```
浏览器能打开 = **DNS 污染**。打不开 = 代理协议问题。

## 修复

### Firefox（推荐）
1. `about:config`
2. 搜索 `socks_remote_dns`
3. 双击改为 `true`
4. 代理设 SOCKS5 → 127.0.0.1:10808

### Chrome/Edge
1. 装 [SwitchyOmega](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif)
2. 情景模式 → 代理服务器 → SOCKS5
3. 勾选 **"使用代理服务器解析 DNS"**

## 别混淆！

- **协议被封** → 所有外网都不通（包括裸 HTTP 80 端口）
- **DNS 污染** → HTTP 能通，但特定域名不通（GitHub 通 Google 不通）
- **VPS IP 被封** → VPS 自身能 curl 通但客户端不通

**实战中 80% 的"梯子坏了"其实是 DNS 污染。**
