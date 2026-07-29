# Cloudflare Tunnel 诊断信号

## 确认 Tunnel 转发成功

```bash
curl -sk https://vps.你的域名/ws
```

- HTTP 400 Bad Request → ✅ WebSocket 升级成功，Xray 收到请求
- HTTP 000 / timeout → ❌ DNS 未生效或 Tunnel 未连接
- HTTP 404 → Tunnel 通但路径不对

## 确认是否被 Cloudflare CDN 破坏

检查 VPS Xray 日志：
```bash
journalctl -u x-ui --no-pager --since "2 min ago"
```

如果看到大量 `X-Forwarded-For` 警告 → Cloudflare CDN 橙色云在中间注入了 HTTP 头，WebSocket 帧被破坏。**必须改用 Tunnel 或关橙色云。**

Cloudflare IP 特征：`172.71.x.x`, `104.23.x.x`, `162.159.x.x`

## Tunnel 连接确认

```bash
systemctl status cloudflared
# Active: active (running) 即正常
```

## 安装（root 用户不加 sudo）
```bash
cloudflared service install <token>
```
Debian 最小安装没有 sudo，root 直接跑。
