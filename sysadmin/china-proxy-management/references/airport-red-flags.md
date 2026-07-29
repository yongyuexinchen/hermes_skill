# Airport Quality Assessment — Red Flag Checklist

From real-world diagnosis of 极速789.com (jsylianjie8.com).

## The Five Red Flags

### 1. Cloned Nodes (Same Server, Different Names)

```
🇭🇰 香港_01 → server: jjjpenjv-1-4.asmgwmfdn.hoxdzillavskiong.com:443
🇭🇰 香港_02 → server: jjjpenjv-1-4.asmgwmfdn.hoxdzillavskiong.com:443
🇭🇰 香港_03 → server: jjjpenjv-1-4.asmgwmfdn.hoxdzillavskiong.com:443
🇭🇰 香港_04 → server: jjjpenjv-1-4.asmgwmfdn.hoxdzillavskiong.com:443
🇯🇵 日本_01 → server: jjjpenjv-1-4.asmgwmfdn.hoxdzillavskiong.com:443
🇸🇬 新加坡_01 → server: jjjpenjv-1-4.asmgwmfdn.hoxdzillavskiong.com:443
```

Four "Hong Kong" nodes, a "Japan" node, and a "Singapore" node all pointing to the **exact same IP**. There's no geographic diversity — just one server with different labels.

### 2. Universal UUID

```yaml
password: ddeda9e9-12af-48c2-884a-d6b9b1c44453  # Every single node
```

Legitimate multi-server setups use different authentication per server. A shared UUID means there's no actual server differentiation.

### 3. Auto-Generated Domain Names

```
hoxdzillavskiong.com
sddsafgfhyghf.com
asmgwmfdn.hoxdzillavskiong.com
```

Random-string domains are a sign of frequent rotation (every few weeks/months) to evade GFW blocking. Each rotation means:
- All your client configs break
- You need to re-subscribe
- Downtime during the transition

### 4. Fake SNI

```yaml
sni: jsygouer.weixin-baidu-qq.com  # Pretends to be WeChat + Baidu + QQ
sni: Honkai-hoyoverse.com           # Pretends to be a game
```

These SNI values are designed to look like legitimate Chinese services, but GFW's deep packet inspection can detect mismatches between SNI and actual traffic patterns.

### 5. Info Nodes as Proxy Entries

```yaml
- name: 剩余流量：956.02 GB
  type: trojan
  server: hk15.jsylianjie8.com
  # This is NOT a real proxy — it's metadata injected as a fake node
```

Budget airports inject account info (remaining traffic, reset date, expiry date, website URL) as fake proxy nodes. If your proxy list shows "剩余流量" or "官网" entries, the airport is using a lazy subscription template.

## When to Abandon

**3+ red flags** → the airport is the root cause. No amount of config tweaking, node switching, or software updating will fix it. The infrastructure itself is poor.

## What a Good Airport Looks Like

- Each node has a unique `server` IP
- Geographic labels match actual server locations (testable via `curl ipinfo.io` through each node)
- SNI values are real, active domains (e.g., `www.microsoft.com`, `cloudflare.com`)
- No info nodes mixed into the proxy list
- Subscription updates actually add/remove nodes (not just rename the same ones)
