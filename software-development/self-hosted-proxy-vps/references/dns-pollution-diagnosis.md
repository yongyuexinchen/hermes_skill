# DNS 污染诊断流程

## 症状识别
- 浏览器通过代理访问 `google.com` → 超时/白屏
- 浏览器通过代理访问 `github.com` → 正常
- SSH 隧道 curl 测试: `curl --socks5 ... https://github.com` 能通，谷歌不通

## 三步确诊

### 第一步：确认基本连通性
```bash
ping VPS_IP          # 通 = 网络层 OK
curl http://VPS_IP/  # 通 = TCP/HTTP OK
```

### 第二步：隔离 DNS
从 VPS 上查真实 IP：
```bash
ssh root@VPS "dig +short google.com"
# 或
ssh root@VPS "curl -sk -o /dev/null -w '%{remote_ip}' https://www.google.com"
```

拿到真实 IP 后，本地绕过 DNS：
```bash
curl --socks5 127.0.0.1:10808 \
  --resolve www.google.com:443:142.251.155.119 \
  -sk -o /dev/null -w "%{http_code}" \
  https://www.google.com
```

**返回 200 = DNS 污染，返回 000 = IP 封锁。**

### 第三步：修复
- Firefox: `about:config` → `socks_remote_dns` → `true`
- Chrome/Edge: 装 SwitchyOmega 插件，勾选"使用代理解析 DNS"
- 全局: 本地跑 dnscrypt-proxy，上游走加密 DNS

## 原理
国内 DNS 服务器（114.114.114.114、运营商 DNS）对 `google.com` 等域名返回虚假 IP。
SOCKS5 代理默认由客户端本地解析 DNS，拿到假 IP 后请求失败。
`socks_remote_dns=true` 让 DNS 请求也走 SOCKS5 隧道，由 VPS 端的 DNS（8.8.8.8）解析，拿到真实 IP。
