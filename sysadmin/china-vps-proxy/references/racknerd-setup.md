# RackNerd 购买与初始配置

## 购买

1. https://www.racknerd.com/specials/
2. 选 1 GB KVM VPS ($21.99/年)
3. Location: Los Angeles DC-02
4. OS: Debian 12
5. 支付：支付宝（Stripe 中转），偶尔抽风就换 PayPal
6. 账单地址填香港或美国

## 初始设置

```bash
ssh root@<IP>
# 密码见邮件

# 更新系统
apt update && apt upgrade -y

# 设时区
timedatectl set-timezone Asia/Shanghai
```

## BBR 加速

```bash
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

## 管理面板

- NerdVM: https://nerdvm.racknerd.com/
- 用来重装系统、重启 VPS

## 已知限制

- 延迟 ~174ms（中国→洛杉矶）
- 带宽够用但不快（~10-30 Mbps）
- Google/YouTube 能访问但数据中心 IP 可能被部分站点限速
- 无 IPv6（或需手动开启）
