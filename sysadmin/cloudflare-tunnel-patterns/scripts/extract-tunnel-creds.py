#!/usr/bin/env python3
"""从 cloudflared token 提取 Tunnel 凭据，生成 credentials.json"""
import base64, json, sys

token_path = sys.argv[1] if len(sys.argv) > 1 else "/etc/cloudflared/token"
with open(token_path) as f:
    token = f.read().strip()

data = json.loads(base64.b64decode(token + "=="))

creds = {
    "AccountTag": data["a"],
    "TunnelSecret": data["s"],
    "TunnelID": data["t"]
}

with open("/etc/cloudflared/tunnel-creds.json", "w") as f:
    json.dump(creds, f)

print(f"TunnelID: {creds['TunnelID']}")
print(f"CNAME: {creds['TunnelID']}.cfargotunnel.com")
print("credentials → /etc/cloudflared/tunnel-creds.json")
