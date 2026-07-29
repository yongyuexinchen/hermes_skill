# Nginx 作为 TLS 前端 + Xray WebSocket 后端

## 架构
```
公网 → Nginx:443 (TLS) → [WS /ws] → Xray:10000 (VMess, localhost only)
```

Nginx 处理 TLS 握手（真实 nginx 指纹，ISP 看到的就是一个普通 HTTPS 网站），
WebSocket 连接转发给本地 Xray。

## 前提
- 自签名证书: `/etc/x-ui/certs/cert.pem` + `/etc/x-ui/certs/key.pem`
- Xray VMess + WS 监听 `127.0.0.1:10000`，路径 `/ws`

## Nginx 配置
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/x-ui/certs/cert.pem;
    ssl_certificate_key /etc/x-ui/certs/key.pem;

    # 根路径拒绝访问（不暴露任何信息）
    location / {
        return 404;
    }

    # WebSocket 代理到 Xray
    location /ws {
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

## 自签名证书生成
```bash
openssl req -x509 -newkey rsa:2048 \
  -keyout /etc/x-ui/certs/key.pem \
  -out /etc/x-ui/certs/cert.pem \
  -days 3650 -nodes \
  -subj '/CN=www.microsoft.com'
```

## 验证
```bash
# Nginx 正常响应
curl -sk https://VPS_IP/           # → 404
# WebSocket 升级成功到达 Xray
curl -sk -H "Upgrade: websocket" -H "Connection: Upgrade" \
  https://VPS_IP/ws                # → 400 (Xray 拒绝非 VMess 握手，正常)
```

## 客户端注意
- 端口填 443（不是 10000）
- TLS 必须开启
- 必须勾选"允许不安全连接"（allowInsecure，因为自签名证书）
- 路径填 /ws
