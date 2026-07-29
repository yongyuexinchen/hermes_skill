# Cloudflare CDN Limitations for Proxy Protocols

## Key Distinction

| | Cloudflare CDN (orange cloud) | Cloudflare Tunnel |
|---|---|---|
| **What it is** | Layer 7 HTTP reverse proxy + CDN | Reverse tunnel (VPS → CF) |
| **Protocol support** | HTTP/HTTPS only | HTTP, HTTPS, SSH, TCP |
| **Works for proxies?** | ❌ No (see below) | ✅ Partial (SSH works, HTTP CONNECT blocked) |
| **Traffic direction** | CF → VPS (inbound) | VPS → CF (outbound tunnel) |

## Why Cloudflare CDN Fails for Proxy Protocols

Cloudflare CDN with "Proxied" (orange cloud) DNS terminates TLS and creates a NEW HTTP connection to the origin. It inspects the HTTP stream and:

1. **Adds HTTP headers** (X-Forwarded-For, CF-Connecting-IP, etc.) — corrupts WebSocket binary frames
2. **WAF inspects payloads** — VLESS/VMess encrypted frames look like malformed HTTP and get 403'd
3. **Modifies WebSocket framing** — CDN optimizations can alter frame boundaries

### Test Results (2026-07-27, Xray 26.3.27)

| Attempt | Architecture | Result |
|---|---|---|
| Tunnel HTTP → VMess+WS | CF Tunnel (HTTP type) → Xray:10000 | 400 — WS reached Xray but VMess handshake failed |
| CDN Flexible SSL → VLESS+WS | CF CDN → Xray:80 (HTTP) | -1ms — CF added HTTP headers, corrupted WS frames |
| CDN Full SSL → VLESS+WS | CF CDN → Xray:443 (HTTPS) | -1ms — silent failure, no errors but no data |
| Tunnel → tinyproxy HTTP CONNECT | CF Tunnel → tinyproxy:3128 | 403 — CF blocked HTTP CONNECT proxy method |
| Tunnel → SSH | CF Tunnel → sshd:22 | ✅ Works — SSH is a native supported protocol |

## What Works Through Cloudflare Free Tier

| Service | Through CDN? | Through Tunnel? | Notes |
|---|---|---|---|
| Static website | ✅ | ✅ | |
| API (REST/gRPC-Web) | ✅ | ✅ | |
| WebSocket (plain) | ✅ | ✅ | Bare WS frames pass through |
| VLESS/VMess WebSocket | ❌ | ❌ | WAF inspects/drops encrypted frames; Tunnel HTTP type can't relay raw TCP |
| SSH | ❌ | ⚠️ | Tunnel SSH type exists but dashboard-mode forces HTTP transport to origin (see below) |
| HTTP CONNECT proxy | ❌ | ❌ | Blocked as abuse by WAF |

## SSH Tunnel Through Cloudflare: What Really Happens

When setting up SSH through Cloudflare Tunnel with Access:

### The Dashboard-Managed Mode Problem

When cloudflared on VPS runs with `--token-file` (dashboard-managed), the `Public Hostname` SSH type does NOT change how cloudflared connects to the origin. It always uses HTTP transport:

```
Client cloudflared  →  Cloudflare Edge  →  VPS cloudflared  →  originService=http://localhost:22  →  sshd
                                                                              ↑
                                                                     sends HTTP request,
                                                                     sshd responds "Debian-2..."
                                                                     not valid HTTP → connection aborted
```

**Error signature:**
```
originService=http://localhost:22
net/http: HTTP/1.x transport connection broken:
  malformed HTTP status code "Debian-2"
```

### The Local Config Mode Problem

Switching to `cloudflared tunnel --config /etc/cloudflared/config.yml run` requires a credentials file (`cert.pem`), not a token. Generating credentials requires `cloudflared tunnel login` which needs a browser on the VPS — impractical for headless servers.

### What Actually Works for SSH

1. **Cloudflare Zero Trust → Access → Browser-rendered SSH**: Enable `Allow access through browser-based RDP, SSH, or VNC sessions` in the application settings. This provides web-based SSH terminal but does NOT support `-D` dynamic port forwarding (SOCKS5).

2. **Direct VPS access** (if not blocked): No Cloudflare needed.

3. **Cloudflare Spectrum** (paid, $5/mo): Layer 4 TCP proxy that preserves SSH protocol.

## Spectrum (Paid, $5/month)

Cloudflare Spectrum proxies raw TCP/UDP at Layer 4. This WOULD work for proxy protocols since it doesn't inspect payloads. But it costs $5/month per application.

## Lesson

**Do not attempt to route VLESS/VMess/Trojan/Shadowsocks through Cloudflare CDN.** It looks like it should work (WebSocket → HTTPS → CDN) but fails silently. The time spent debugging Cloudflare CDN + proxy protocol combinations is better spent on:

1. Using Hysteria2 direct (UDP, bypasses most DPI)
2. Using Cloudflare Tunnel + SSH for blocked IPs
3. Paying for Spectrum if Cloudflare routing is mandatory
