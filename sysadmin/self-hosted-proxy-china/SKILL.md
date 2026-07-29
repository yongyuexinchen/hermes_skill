---
name: self-hosted-proxy-china
description: Self-host a VPS proxy for bypassing GFW from China — VPS selection, protocol architecture, diagnostic methodology, ISP DPI workarounds, and the Nginx+VMess+WS+TLS pattern.
category: sysadmin
---

# Self-Hosted Proxy for China (GFW Bypass)

## When to Use
User wants to self-host a proxy on a VPS instead of using commercial VPN/机场. Covers end-to-end: VPS purchase, Xray setup, protocol selection, GFW evasion, and client configuration.

## VPS Selection

### Budget US VPS (¥15-30/month)
| Provider | Price | Latency | Payment |
|----------|-------|---------|---------|
| **RackNerd** | $22/year (¥158) | 170-200ms | Alipay via Stripe |
| AkileCloud | ¥10-20/month | 150-180ms | Alipay/WeChat |
| Vultr | $6/month | 130-160ms | PayPal/Credit |

**Recommendation**: RackNerd 1GB KVM VPS ($22/year, 3TB, Los Angeles DC-02) hits the sweet spot. For AI API access (Claude/GPT), US IP is required — HK/JP nodes won't work for Claude.

### Purchase Checklist
- OS: **Debian 12** (best Xray compatibility)
- Datacenter: Los Angeles DC-02 or San Jose (West coast = lowest latency to China)
- Billing address: use fake US address (not verified)
- Payment: Alipay via Stripe (may require turning off existing VPN during checkout)

## Installation: 3X-UI Panel

```bash
ssh root@<VPS_IP>
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

3X-UI provides a web panel at `http://<IP>:<port>/<basepath>`. **Save all credentials** — username, password, port, and web base path are randomized.

## Protocol Architecture Decision Tree

```
Can user access VPS via plain HTTP (port 80)?
├─ NO  → IP or port blocked entirely
│   ├─ ISP-level IP block (ping works, TCP times out) → Cloudflare Tunnel + SSH (see below)
│   └─ VPS dead → Try different VPS/datacenter
└─ YES → TCP works. Can user connect via HTTPS (port 443)?
    ├─ NO  → ISP blocks TLS to this IP; try different VPS
    └─ YES → TLS works. Try Hysteria2 first (UDP, best performance):
        ├─ WORKS → Done. Use Hysteria2 as primary.
        └─ FAILS → Try VMess+WS+TLS on 443:
            ├─ WORKS → Done.
            └─ FAILS → ISP DPI on WebSocket.
                → Fallback: Cloudflare Tunnel + SSH (see ISP IP Block Workaround).

⚠️ DO NOT use Cloudflare CDN (orange cloud / "Proxied" DNS) for proxy protocols.
Cloudflare CDN is Layer 7 HTTP proxy — it inspects/modifies WebSocket payloads,
silently discarding VLESS/VMess frames even when wrapped in WebSocket.
See `references/cloudflare-limitations.md`.
```

**Preferred protocol order** (based on reliability testing):
1. **Hysteria2** (UDP/QUIC, fastest, hardest to DPI)
2. **VMess+WS+TLS** (TCP, most compatible, moderate speed)
3. **SSH Tunnel** (fallback, slow but never blocked)

## The Golden Pattern: Nginx Frontend + Xray Backend

**Why**: Many Chinese ISPs perform DPI that detects proxy protocol handshakes (VMess, Shadowsocks, Reality, Trojan) even over TLS. The solution is to put a **real Nginx** in front that terminates TLS, making the traffic indistinguishable from a normal HTTPS website.

### Architecture
```
Client (V2RayN) ──TLS──▶ Nginx :443 ──WS──▶ Xray :10000 (localhost only)
                           │                    │
                     Looks like real         VMess inside
                     HTTPS website           WebSocket frames
```

### Step-by-Step Setup

**1. Install Xray + 3X-UI** (see above)

**2. Create VMess+WS inbound (internal only)**
In 3X-UI panel → Inbounds → Add:
- Protocol: `vmess`
- Port: `10000`
- Listen: `127.0.0.1` (CRITICAL — internal only)
- Network: `ws`
- Path: `/ws`
- Security: `none` (TLS handled by Nginx)
- Client UUID: generate or reuse existing

**3. Install Nginx + self-signed cert**
```bash
apt-get install -y nginx
mkdir -p /etc/x-ui/certs
openssl req -x509 -newkey rsa:2048 \
  -keyout /etc/x-ui/certs/key.pem \
  -out /etc/x-ui/certs/cert.pem \
  -days 3650 -nodes \
  -subj '/CN=www.microsoft.com'
```

**4. Configure Nginx reverse proxy**
```nginx
server {
    listen 443 ssl;
    server_name _;
    ssl_certificate /etc/x-ui/certs/cert.pem;
    ssl_certificate_key /etc/x-ui/certs/key.pem;

    location / {
        root /var/www/html;
        index index.html;
    }

    location /ws {
        if ($http_upgrade != "websocket") { return 404; }
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

**5. Verify the chain**
```bash
# Plain HTTPS should show nginx default page (or 403)
curl -sk https://<VPS_IP>/

# WebSocket upgrade should reach Xray (returns 400 = expected)
curl -sk -H "Upgrade: websocket" -H "Connection: Upgrade" \
  https://<VPS_IP>/ws -o /dev/null -w '%{http_code}'
# Expected: 400 (Xray received WS but no VMess data)
```

### Client Config (V2RayN / v2rayNG)
```
Type: vmess
Address: <VPS_IP>
Port: 443
UUID: <client_uuid>
Network: ws
Path: /ws
TLS: ON
Allow Insecure: ON (self-signed cert)
```

## Xray 26.x Breaking Changes ⚠️

Xray 26.3.x introduced breaking changes that cause silent failures:

### `allowInsecure` Removed
**Error**: `The feature "allowInsecure" has been removed and migrated to "pinnedPeerCertSha256"`

**Client-side fix**: Instead of `allowInsecure=true`:
- **Cloudflare CDN route** (wraps traffic in Cloudflare's real cert): set `security=tls` with NO `allowInsecure`. Cloudflare provides a valid certificate.
- **Direct VPS with self-signed cert**: use `pinnedPeerCertSha256` with the cert's SHA256 fingerprint, OR regenerate cert with a real CA (Let's Encrypt).

### VMess + WebSocket Deprecated
**Warning**: `The feature WebSocket transport is deprecated. Please migrate to XHTTP H2 & H3.`
**Warning**: `The feature VMess is deprecated. Please migrate to VLESS Encryption.`

**What to do**: Migrate to **VLESS + XHTTP** for new deployments. Existing VMess+WS continues to work but may be removed in a future version.

### Client Config Migration
Old (VMess+WS, Xray <26): `security=tls&allowInsecure=true`
New (VLESS+WS, Xray 26+): `security=tls` (no allowInsecure, use Cloudflare cert or Let's Encrypt)

## ISP IP Block Workaround: Cloudflare Tunnel + SSH

When the ISP blocks the VPS IP directly (ping works, all TCP times out), use Cloudflare Tunnel to create a reverse tunnel. The ISP only sees Cloudflare IPs, not the VPS.

### Architecture
```
Home PC (blocked ISP)                  Cloudflare                 VPS
cloudflared access tcp    ──→  ssh.yongyuexinchen.xin  ──→  Tunnel  ──→  sshd:22
(ISP sees: Cloudflare HTTPS)           (DNS resolves to CF IP)    (Tunnel internal)
```

### Setup

**1. VPS**: `cloudflared` installed as service (see Cloudflare Zero Trust dashboard)

**2. Cloudflare Dashboard**: Zero Trust → Networks → Tunnels → Public Hostname:
- Subdomain: `ssh`, Type: SSH, URL: `localhost:22`

**3. Client (Windows)**:
```cmd
:: Download cloudflared from GitHub
:: First-time login (opens browser, use Cloudflare account):
cloudflared.exe access login

:: Start SSH tunnel (keep this window open):
cloudflared.exe access tcp --hostname ssh.yourdomain.com --url 127.0.0.1:2222

:: In another terminal, connect:
ssh -p 2222 root@127.0.0.1

:: For SOCKS5 proxy (browser can use):
ssh -p 2222 -D 1080 -N root@127.0.0.1
```

### Limitations
- SSH is TCP single-connection, not optimized for bulk traffic
- Each `cloudflared access tcp` instance = one TCP stream
- Better for management/emergency access than daily proxy use
- The laptop/phone that CAN reach VPS directly should use Hysteria2

### Critical Pitfall: Dashboard-Managed Tunnel Uses HTTP Transport
When cloudflared on VPS runs in dashboard-managed mode (`--token-file`), ALL ingress connections use HTTP transport to the origin — even for SSH-type public hostnames. You'll see this error:

```
originService=http://localhost:22
net/http: HTTP/1.x transport connection broken:
  malformed HTTP status code "Debian-2"
```

**What happens**: cloudflared sends an HTTP request to sshd. sshd responds with its SSH banner (`Debian-2...`). cloudflared can't parse it as HTTP and drops the connection.

**Why this matters**: The SSH public hostname + Cloudflare Access flow works correctly ONLY when cloudflared runs with a **local config.yml** that uses protocol annotations (`service: ssh://localhost:22`). Dashboard-managed tunnels always use `http://` regardless of the SSH type setting — this is an upstream limitation.

**Workaround**: Cloudflare Zero Trust → Access → Applications can add browser-rendered SSH (enable `Allow access through browser-based RDP, SSH, or VNC sessions`), but this provides web-based SSH only — not raw TCP forwarding for SOCKS5.

**Verification log**: Always check before debugging SSH tunnel:
```bash
journalctl -u cloudflared --no-pager --since '1 min ago' | grep originService
# http://localhost:22 → dashboard HTTP transport bug (will fail)
# ssh://localhost:22   → correct local config mode (will work)
```

## Reality Protocol Pitfalls

Reality (VLESS+XTLS) is promising but has compatibility issues:

### "empty serverNames" Error
**Root cause**: 3X-UI web panel sometimes fails to persist the SNI field to the database.

**Fix**: Edit the SQLite database directly:
```python
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
row = db.execute('SELECT id, stream_settings FROM inbounds WHERE id=1').fetchone()
settings = json.loads(row[1])
settings['realitySettings']['serverNames'] = ['www.microsoft.com']
settings['realitySettings']['publicKey'] = '<public_key>'
db.execute('UPDATE inbounds SET stream_settings=? WHERE id=1',
           (json.dumps(settings),))
db.commit()
```
Then `x-ui restart`.

### Clash Meta (Mihomo) Reality Issues
- "REALITY authentication failed" is common even with correct keys
- Some Mihomo versions don't support the full Reality handshake
- **Recommendation**: Skip Reality for Clash users; use VMess+WS+TLS instead
- Reality works better with V2RayN/Xray-core clients

## Hysteria2 Setup (Recommended Primary Protocol)

Hysteria2 over UDP/QUIC consistently outperforms TCP-based protocols (VMess/SS) and is harder for ISP DPI to fingerprint.

### Server (3X-UI or manual)
```bash
# Manual install
bash <(curl -fsSL https://get.hysteria.sh/)
# Config at /etc/hysteria/config.yaml
```

### Client: `templates/hysteria2-client-config.yaml`

### Windows Browser Setup (DNS Pollution Fix)
The root cause of "proxy works but Google won't load" is **DNS pollution**:
- Chrome/Edge resolve domains locally → get fake IPs → proxy can't route
- **Fix**: Use HTTP proxy mode (Hysteria2's `http.listen: 10809`), which resolves DNS on the VPS
- Firefox alternative: SOCKS5 + `about:config` → `network.proxy.socks_remote_dns = true`

### Windows System Proxy
```
HTTP Proxy: 127.0.0.1:10809
```
Set via Windows Settings → Network → Proxy, or `reg add`:
```cmd
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:10809" /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f
```

## Diagnostic Methodology: Layer-by-Layer

When proxy doesn't work, do NOT change multiple things at once. Test one layer at a time, bottom-up:

```
Layer 6: Application  (Google loads?)
Layer 5: Protocol     (V2Ray/VLESS handshake succeeds?)
Layer 4: WebSocket    (WS upgrade returns 101/400?)
Layer 3: TLS          (HTTPS certificate accepted?)
Layer 2: HTTP/TCP     (curl reaches VPS?)
Layer 1: DNS          (domain resolves correctly?)
Layer 0: Network      (ping works?)
```

**Layer 0 — Network**: `ping <VPS_IP>` → no = IP blocked or VPS dead
**Layer 1 — DNS**: `nslookup <DOMAIN>` → resolves to Cloudflare IPs (proxied) or VPS IP (direct)
**Layer 2 — TCP/HTTP**: `curl -sk https://<DOMAIN>/` → 403/404 = tunnel works, 000 = not reaching
**Layer 3 — TLS**: Check V2RayN logs for `x509:` errors → self-signed cert issues (see Xray 26.x section)
**Layer 4 — WebSocket**: `curl -sk -H "Upgrade: websocket" -H "Connection: Upgrade" https://<DOMAIN>/ws` → 400 = WS upgrade reached Xray, protocol mismatch expected
**Layer 5 — Protocol**: Check `journalctl -u x-ui` on VPS — if no connections logged, upstream (CDN/Tunnel) is blocking
**Layer 6 — Application**: Browser loads Google? → Done.

**Golden rule**: If Layer N passes but Layer N+1 fails, the problem is in between those two layers. Don't touch layers above or below.

## Common Pitfalls

### DNS Pollution (Most Common)
Symptom: Proxy connected, some sites work, Google/YouTube don't.
Cause: Local DNS resolves to fake IPs before proxy can route.
Fix: Use HTTP proxy mode (server-side DNS) or Firefox `socks_remote_dns`.

### Port Conflicts
Symptom: Service starts then dies, or port already in use.
Check: `ss -tlnp` (TCP) and `ss -ulnp` (UDP).
Common: nginx auto-starts on port 80/443 → `systemctl disable nginx`.

### V2RayN Changes System Proxy
V2RayN sets system proxy when active (typically `127.0.0.1:10808` SOCKS5).
When switching from V2RayN to Hysteria2, the proxy port must be manually changed to `10809`.

## Client Preference
- **V2RayN** (Windows): More stable, better protocol support
- **Clash Verge Rev**: Unstable with custom configs, frequent crashes. Only use with well-tested subscription profiles.
- **v2rayNG** (Android), **Shadowrocket** (iOS)

## Reference Files
- `references/racknerd-purchase.md` — Step-by-step RackNerd purchase walkthrough
- `references/cloudflare-limitations.md` — Why Cloudflare CDN fails for VLESS/VMess and what alternatives work
- `templates/hysteria2-client-config.yaml` — Hysteria2 Windows client config template
