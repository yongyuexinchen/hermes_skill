---
name: china-proxy-management
description: Diagnose slow/flaky VPN in China — Clash Verge config analysis, airport quality assessment, and self-hosted VPS proxy setup (X-ui + Reality). Use when user complains about VPN speed, connection reliability, or wants to self-host.
category: sysadmin
trigger_keywords:
  - VPN 慢
  - 代理太慢
  - 连不上
  - 换机场
  - 自己搭建
  - 自建代理
  - VPS 搭梯子
  - Clash 连不上
  - 代理老断
---

# China Proxy Management — Diagnosis & Self-Hosting

Covers the full lifecycle: diagnose a broken/slow Clash Verge proxy → evaluate whether to fix or replace → set up a self-hosted VPS proxy when airports are unreliable.

## Phase 1: Diagnosis

### 1.1 Is the proxy even running?

```bash
# Quick port reachability test
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/7897' 2>/dev/null && echo "PROXY OK" || echo "PROXY DOWN"
```

### 1.2 Speed test through proxy

```bash
curl -x http://127.0.0.1:7897 -s -w "time_total: %{time_total}s\nhttp_code: %{http_code}\nspeed: %{speed_download} B/s\n" -o /dev/null --max-time 10 https://www.google.com
curl -x http://127.0.0.1:7897 -s -w "time_total: %{time_total}s\nhttp_code: %{http_code}\n" -o /dev/null --max-time 10 https://github.com
```

### 1.3 Check running processes

```bash
tasklist 2>/dev/null | grep -i "clash\|mihomo\|verge"
netstat -ano 2>/dev/null | grep "7897" | head -5
```

### 1.4 Find Clash Verge config directory

**Clash Verge Rev** (community fork, the active maintained version):
```
%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\
```

Key files:
- `clash-verge.yaml` — the **active merged config** containing all proxy nodes, rules, DNS settings. Read this to see actual nodes being used.
- `config.yaml` — base Mihomo core config (ports, mode, external-controller)
- `profiles/*.yaml` — subscription profiles (URL-based imports)

**Clash Verge (original, deprecated):**
```
%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\  (same dir, old naming)
```

### 1.5 Read the active node list

Read `clash-verge.yaml` and look for the `proxies:` section. Assess:

| Red Flag | What It Means |
|----------|---------------|
| Multiple "nodes" share same `server` IP + same `password` | Not real multi-node — same server cloned with different names |
| All nodes use identical UUID/password | Budget airport with minimal infrastructure |
| Domain names are random strings (`hoxdzillavskiong.com`) | Frequent domain rotation to evade GFW; inherently unstable |
| SNI fields are fake (`jsygouer.weixin-baidu-qq.com`) | Poorly maintained, easy for GFW to fingerprint |
| Info nodes disguised as proxies ("剩余流量", "套餐到期") | Airport injecting metadata as fake proxy entries |

**Verdict**: if 3+ red flags → the airport itself is the problem, not your config. Fixing settings won't help; switch providers or self-host.

## Phase 2: Evaluate Options

Present the user with three paths and a clear comparison:

| | Fix Current | Switch Airport | Self-Host VPS |
|---|---|---|---|
| Effort | Low | Low | Medium (30min first time) |
| Monthly Cost | ¥10-20 | ¥10-30 | ¥10-35 |
| Reliability | Same problem | Depends on airport | High (with Reality protocol) |
| Learning Value | None | None | Linux/SSH/Networking skills |

### Self-hosting evaluation framework

**Cost**: VPS from $1.5/month (RackNerd US) to $6/month (Vultr JP)
**Difficulty**: 2026 level = very low. One-click panels (3X-UI) handle everything.
**Reliability**: Higher than budget airports BUT:
- IP may get blocked by GFW every 1-3 months → need to swap IP
- Reality protocol (steals real TLS fingerprints) drastically reduces block risk
- Cloudflare CDN can hide real IP at slight speed cost

**Protocol recommendation**: 
- **Hysteria2** (UDP/QUIC) — fastest, reliable, harder for DPI to fingerprint. Use as primary.
- **VLESS + Reality** (via 3X-UI panel) — TCP fallback but has client compatibility issues (Clash/Mihomo).
- **VMess + WS + TLS** — most compatible but deprecated in Xray 26.x.

**⚠️ Cloudflare CDN does NOT work for proxy protocols.** Cloudflare CDN (orange cloud) is Layer 7 HTTP proxy that inspects WebSocket payloads. VLESS/VMess frames wrapped in WebSocket will be silently discarded by Cloudflare's WAF. Use Cloudflare Tunnel + SSH for ISP-blocked IPs instead.

**⚠️ AI API geoblocking — choose VPS location accordingly:**

| Service | 🇭🇰 HK IP | 🇯🇵 JP IP | 🇺🇸 US IP |
|---------|:--:|:--:|:--:|
| OpenAI API | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |
| Google Gemini | ✅ | ✅ | ✅ |
| **Claude (Anthropic)** | ❌ | ❌ | ✅ |
| **Cursor / Windsurf** | ❌ | ⚠️ unstable | ✅ |

If the user needs Claude or Cursor, a **US VPS is mandatory**. RackNerd US ($21.99/year) is the budget pick; Vultr US ($6/month) for higher reliability.

## Phase 3: Self-Host Setup (RackNerd + X-ui + Reality)

### 3.1 Buy VPS

Recommended for budget self-hosting:
- **RackNerd**: $21.99/year (≈¥13/month) — 1 vCPU, 1GB RAM, 20GB SSD, 3TB transfer, 1 Gbps
- Datacenter: **Los Angeles DC-02** or **San Jose** (West Coast → lowest latency to China)
- OS: **Debian 12** (best X-ui compatibility)

Payment: Alipay accepted.

### 3.2 SSH in (from Windows git-bash)

```bash
ssh root@<VPS_IP>
# Enter root password from email
```

### 3.3 Install 3X-UI Panel (NOT the old X-ui)

**Use 3X-UI (mhsanaei fork)** — actively maintained, native Reality support, better UI:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

The installer auto-generates credentials and prints them. Example output:
```
Username:    <random 10-char>
Password:    <random 10-char>
Port:        <random 5-digit>
WebBasePath: <random string>
Access URL:  http://<VPS_IP>:<Port>/<WebBasePath>
```

⚠️ **Save ALL of these** — port, base path, username, password. The panel URL is NOT just `http://IP:port`.

### 3.4 Configure Reality Protocol (via 3X-UI web panel)

The panel has a tabbed form. Follow this exact sequence:

1. **基础配置 tab**:
   - 备注: any label (e.g. "US-Reality")
   - 协议: **vless** (dropdown, default might be vmess)
   - 端口: keep auto-generated (e.g. 34356), or set to any unused port
   - 地址: leave empty (listen on all IPs)

2. **安全 tab** (NOT 协议 tab — Reality config is under 安全):
   - Click radio: **Reality**
   - 目标: `www.microsoft.com:443` (steals microsoft.com's TLS fingerprint)
   - Keys: auto-generated on Reality select — note them down:
     - Public Key (公钥)
     - Private Key (私钥)
   - Short IDs: leave auto-generated default
   - Spider X: leave auto-generated (e.g. `/wDaObIf48AjXFlk`)
   - uTLS: set to `chrome` for best fingerprinting
   - SNI: should auto-match the target domain

3. Click **创建**

4. **Restart Xray** — go back to Dashboard, click "重启" under the Xray section. Changes don't apply until Xray restarts.

### 3.5 Generate Client Config

After restart, go back to 入站 → click **编辑** on the row → 安全 tab → copy these three values:

| Field | Example |
|-------|---------|
| Public Key | `0fbmDJwB4N7YHy_t_8uCLSLUjaQhIutUE5mwad42UR4` |
| Private Key | `uNVnbvNa4yyvr8LBrrZrF5hzr7lzOwxet8GgBjr1yVA` |
| Short ID | (auto-generated hex string) |

These are needed to build the client config for Clash Verge. The vless+tcp+reality share link format:
```
vless://<UUID>@<VPS_IP>:<PORT>?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.microsoft.com&fp=chrome&pbk=<PUBLIC_KEY>&sid=<SHORT_ID>&type=tcp&headerType=none#US-Reality
```

Import this as a new profile in Clash Verge, or add it as a manual proxy entry.

> See `references/reality-client-config.md` for the exact Clash Verge YAML format and share link template.

### 3.6 Verify

```bash
# Test through self-hosted proxy (Clash Verge routes through it)
curl -x http://127.0.0.1:7897 -s -o /dev/null -w "%{http_code}" --max-time 10 https://www.google.com
# Should return 200 or 302 (redirect)
```

## Pitfalls

1. **RackNerd's "timer" on deals page is fake** — always counting down, ignore it.
2. **Clash Verge Rev config is at `io.github.clash-verge-rev.clash-verge-rev`** not `clash-verge` — searching the wrong dir gives false "not found".
3. **External controller port is 9097** (not default 9090) in Mihomo config — REST API calls to 9090 will fail silently.
4. **US VPS latency to China is 150-180ms** — fine for browsing and API calls, bad for real-time gaming/4K streaming. Set expectations upfront.
5. **Self-hosted IP may get blocked** — Reality protocol + changing IP when needed is the mitigation. Don't promise "set and forget."
6. **Stripe Alipay payment may fail** — if RackNerd's Stripe→Alipay redirect crashes ("系统异常"), **turn off the VPN** and retry. The slow proxy causes the Alipay gateway to timeout. PayPal is a reliable fallback.
7. **RackNerd billing address** — fill with a US address (e.g. `123 Mission Street, San Francisco, CA 94105`). Hong Kong addresses sometimes fail state/postcode validation. Country must be United States.
8. **3X-UI install URL is `mhsanaei/3x-ui` NOT `FranzKafkaYu/x-ui`** — the old X-ui is abandoned. 3X-UI is the active fork with native Reality support.
9. **Reality settings are under "安全" tab, NOT "协议" tab** — common confusion in the 3X-UI panel. The 协议 tab only has encryption settings.
10. **Changes require Xray restart** — creating/modifying an inbound does NOT auto-apply. Go to Dashboard → click "重启" under Xray section.
11. **SSH from Windows git-bash to fresh VPS** — `ssh root@IP` works directly (no sshpass needed). If password auth fails the first time, the VPS may still be provisioning (wait 2-5 min). Use `-o StrictHostKeyChecking=no` for first connection.
12. **Don't try paramiko from Hermes venv on Windows** — Python path conflicts cause `ModuleNotFoundError` even after pip install. Plain `ssh` from git-bash terminal is the reliable path.
13. **3X-UI auto-generates a random WebBasePath** — the panel URL is NOT just `http://IP:port`. It includes a random path segment (e.g. `/ZsWMyFpA21DFHf7XWE`). Save the full URL.

## Cross-references

- `git-github-windows-china` — proxy port detection and git-over-proxy workflow
- `china-network-python-setup` — pip/conda behind the same proxy
- `windows-gitbash-quirks` — MSYS path gotchas when working with proxy config files
