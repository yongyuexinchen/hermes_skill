# Reality Protocol Debugging & 3X-UI Database Fixes

## Reality "empty serverNames" Error

### Symptom
```
ERROR - XRAY: Failed to start: infra/conf: failed to build inbound config 
> Failed to build REALITY config. > infra/conf: empty "serverNames"
```

### Root Cause
3X-UI web panel does NOT automatically populate the `serverNames` field when you set the Reality target. The SNI dropdown stays empty. When Xray tries to load the config, RealitySettings has `serverNames: []` which is invalid.

### Fix: Via SQLite
```bash
ssh root@VPS_IP
python3 -c "
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
row = db.execute('SELECT id, stream_settings FROM inbounds WHERE id=1').fetchone()
settings = json.loads(row[1])
rs = settings['realitySettings']
rs['serverNames'] = ['www.microsoft.com']
rs['publicKey'] = 'YOUR_PUBLIC_KEY'
settings['realitySettings'] = rs
db.execute('UPDATE inbounds SET stream_settings=? WHERE id=1', (json.dumps(settings),))
db.commit()
print('Fixed')
db.close()
"
x-ui restart
```

**Important**: Just editing `/usr/local/x-ui/bin/config.json` is NOT enough — 3X-UI regenerates it from the database on every restart.

## Reality "authentication failed" via Clash Meta

### Symptom (Mihomo sidecar log)
```
[TCP] dial GLOBAL ... --> ... error: 192.255.128.175:34356 connect error: REALITY authentication failed
```

### Possible Causes
1. **Public/private key mismatch** between client and server
2. **Short ID mismatch** — client must use one of the server's `shortIds`
3. **Clash Meta version incompatibility** — older versions may have Reality bugs
4. **Flow mismatch** — `xtls-rprx-vision` vs older flows

### Debugging
1. Verify key pair:
```python
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import base64

private_b64 = 'SERVER_PRIVATE_KEY'
expected_public_b64 = 'CLIENT_PUBLIC_KEY'

private_bytes = base64.b64decode(private_b64 + '==')
expected_public_bytes = base64.b64decode(expected_public_b64 + '==')

priv = x25519.X25519PrivateKey.from_private_bytes(private_bytes)
pub = priv.public_key()
pub_bytes = pub.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
computed_public_b64 = base64.b64encode(pub_bytes).decode().rstrip('=')
print('Keys match:', expected_public_b64 == computed_public_b64)
```

2. Check Mihomo version: Reality support improved significantly in v1.18+. Older versions may silently fail.

3. Preferred fix: **Don't use Reality.** It's the most finicky protocol. Use VMess+WS+TLS behind nginx instead.

## 3X-UI Database Schema (inbounds table)

Key columns for manual manipulation:
```
id, user_id, up, down, total, remark, sub_sort_index, enable, 
expiry_time, traffic_reset, listen, port, protocol, 
settings (JSON), stream_settings (JSON), tag, sniffing (JSON),
node_id, share_addr_strategy, share_addr, origin_node_guid
```

### Example: Creating a VMess inbound via SQL
```python
settings = json.dumps({
    'clients': [{
        'id': 'UUID',
        'alterId': 0,
        'security': 'auto',
        'email': 'user@example.com'
    }]
})
stream = json.dumps({
    'network': 'ws',
    'security': 'none',
    'wsSettings': {'path': '/ws', 'headers': {}}
})
sniffing = json.dumps({'enabled': True, 'destOverride': ['http', 'tls']})
```

### Example: Creating a Shadowsocks inbound
```python
settings = json.dumps({
    'clients': [{
        'password': 'PASSWORD',
        'method': 'aes-256-gcm',
        'email': 'user@example.com'
    }]
})
stream = json.dumps({'network': 'tcp', 'security': 'none'})
```
