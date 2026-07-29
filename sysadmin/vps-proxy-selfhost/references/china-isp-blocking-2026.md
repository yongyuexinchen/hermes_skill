# 2026 年 7 月中国 ISP 代理协议封锁实测

测试环境：中国某 ISP，VPS 为 RackNerd 洛杉矶节点 (192.255.128.175)。

## 端口可达性

| 端口 | 协议 | 结果 | 备注 |
|------|------|:--:|------|
| 80 | HTTP (nginx) | ✅ 通 | 浏览器能访问 |
| 80 | HTTP CONNECT (tinyproxy) | ⚠️ 部分通 | GitHub/Bing 通，Google/YouTube 不通 |
| 443 | HTTPS (nginx) | ✅ 通 | 自签名证书会弹警告 |
| 443 | VMess+WS+TLS (Xray) | ❌ 不通 | ISP 检测到代理握手 |
| 22 | SSH | ✅ 通 | 偶发超时（代理干扰） |
| 10000 | VMess TCP | ❌ 超时 | 非标端口直接封锁 |
| 8388 | Shadowsocks | ❌ 超时 | 同上 |
| 34356 | VLESS+Reality | ⚠️ TCP 通但认证失败 | Reality 配置问题而非 ISP 封锁 |

## 结论

1. **只用 80 和 443 端口**——其他端口全部被 QoS 或封锁
2. **代理协议握手被 DPI 检测**——即使走 443 + TLS，VMess 握手特征仍可被识别
3. **HTTP CONNECT 代理部分可用**——GitHub/Bing 等可通过，Google 等大站不通（可能 TLS 指纹识别）
4. **SSH 隧道最可靠**——SSH 协议本身不会被误判为代理，且走 22 端口

## 最稳方案

SSH 动态端口转发（`ssh -D`），配合免密登录：

```bash
ssh -D 10808 -N -i ~/.ssh/vps_key root@<VPS_IP>
```

Windows 设 SOCKS5 代理 `127.0.0.1:10808`。
