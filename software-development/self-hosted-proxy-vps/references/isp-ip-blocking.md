# ISP 级别 IP 封锁排查

## 症状
- VPS 所有 TCP 端口（22/80/443/10000 等）从特定网络超时
- ICMP ping 能通（有些 ISP 只封 TCP 不封 ICMP）
- 换网络（手机热点）后正常
- VPS 本身服务正常（通过其他网络可验证）

## 诊断流程

```
1. 手机热点 → VPS 通？ → YES → 家庭宽带被 ISP 拉黑
                         → NO  → VPS 本身挂了

2. ping VPS → 通？
   → YES + TCP 不通 → ISP 只封了 TCP，ICMP 放行
   → NO → IP 被完全拉黑或 VPS 宕机
```

## 解决

| 方案 | 成本 | 操作 |
|------|------|------|
| RackNerd 换 IP | $3 一次性 | 面板 → VPS → Change IP |
| 链式代理中转 | 0 | 客户端出站走现有可用代理绕到 VPS |
| Cloudflare Tunnel | 免费+域名 | cloudflared tunnel → 隐藏真实 IP |
| 换 VPS 商家 | 同价位 | 不同商家的 IP 段不同 |

## RackNerd 换 IP 步骤
1. 登录 https://nerdvm.racknerd.com/
2. 选 VPS → Networking → Change IP Address
3. 付费 $3 → 新 IP 即时生效
4. 更新所有客户端配置

## 链式代理思路（sing-box）
```json
{
  "outbounds": [
    {
      "tag": "self-vps",
      "protocol": "hysteria",
      "detour": "available-proxy"
    },
    {
      "tag": "available-proxy",
      "protocol": "vmess"
    }
  ]
}
```
