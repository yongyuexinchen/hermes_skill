# Hysteria2 Windows 客户端配置模板

```yaml
server: <VPS_IP>:443
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

## 使用方式

```cmd
cd <目录>
hysteria-windows-amd64.exe -c hysteria2-config.yaml
```

## 浏览器配置

- **全浏览器通用**：Windows 系统代理 → HTTP `127.0.0.1:10809`
- **Firefox**：SOCKS5 `127.0.0.1:10808` + `socks_remote_dns=true`

## 下载

https://github.com/apernet/hysteria/releases

> ⚠️ 客户端和服务器版本必须匹配。VPS 跑的版本用 `hysteria --version` 确认。
