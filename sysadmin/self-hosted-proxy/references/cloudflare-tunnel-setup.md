# Cloudflare Tunnel Setup Reference

## What It Solves

ISP/carrier blocks VPS IP (ping works, TCP times out). Cloudflare Tunnel hides the real IP behind CF's CDN.

## Architecture
```
Client → vps.domain.com:443 (CF HTTPS) → CF Tunnel → localhost:10000 (Xray VMess+WS)
```

## Step-by-Step

### 1. Buy Domain
- Alibaba Cloud: `.xin` ~¥7/year (needs real-name verification via Alipay)
- Namecheap: `.xyz` ~$1/year (no verification)
- Add temporary A records: `@` → VPS_IP, `www` → VPS_IP

### 2. Cloudflare
- Sign up at dash.cloudflare.com
- Add Site → enter domain → Free plan
- CF gives two NS servers: `deb.ns.cloudflare.com`, `drew.ns.cloudflare.com`

### 3. Cut Over NS
- Alibaba Cloud → Domain → DNS Modification → Custom DNS
- Replace `dns13.hichina.com` / `dns14.hichina.com` with CF's NS
- Wait 5-120 minutes for propagation
- Verify: `curl -sk https://vps.domain.com/ws` should return 400 (from Xray)

### 4. Install cloudflared on VPS
```bash
curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

### 5. Create Tunnel
- CF Dashboard → Zero Trust → Networks → Tunnels → Create
- Name: `vps-proxy`
- Copy the install command (contains token)
- On VPS (NOTE: skip `sudo` if already root):
  ```bash
  cloudflared service install <token>
  ```
- Verify: `systemctl status cloudflared`

### 6. Public Hostname
- CF → Tunnels → click tunnel name → Public Hostname tab → Add
- Subdomain: `vps`
- Domain: your domain
- Type: `HTTP` (not HTTPS — internal traffic is HTTP)
- URL: `localhost:10000`

### 7. VPS: Switch VMess to WebSocket
Cloudflare Tunnel only forwards HTTP/WebSocket. Plain TCP won't work.
```sql
UPDATE inbounds SET stream_settings='{"network":"ws","security":"none","wsSettings":{"path":"/ws"}}' WHERE protocol='vmess';
```

### 8. Client Config
- Address: `vps.yourdomain.com`
- Port: `443`
- UUID: same as before
- Network: `ws`
- Path: `/ws`
- TLS: ON (CF provides real certificate, no allowInsecure needed)

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `curl` says "Could not resolve host" | DNS not propagated yet, wait |
| HTTP 404 on `/` | Normal — root path has no handler, `/ws` is the proxy path |
| HTTP 400 on `/ws` | Working! Xray received WebSocket but expects VMess protocol |
| V2RayN delay `-1 ms` | Check tunnel status: `systemctl status cloudflared` |
| Cloudflare error page | Tunnel down, check `journalctl -u cloudflared` |
