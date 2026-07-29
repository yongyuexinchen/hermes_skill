# RackNerd 注册细节（中国用户）

## 购买流程

1. 访问 `racknerd.com/specials/`
2. 选 $21.99/年 套餐（1G RAM / 20G SSD / 3TB / 1Gbps）
3. 机房选 **Los Angeles DC-02** 或 **San Jose**（西海岸到中国延迟最低）
4. 系统选 **Debian 12**

## 填表注意事项

| 字段 | 填法 |
|------|------|
| First/Last Name | 拼音 |
| Email | 真实邮箱（QQ邮箱可收） |
| Phone | 留空 |
| Street | `123 Mission Street` |
| City | `San Francisco` |
| State | `California` |
| Postcode | `94105` |
| Country | `United States` |

## 支付

- 选 **Stripe 支付宝**
- **关掉本地代理**再付（挂着代理访问 Stripe 支付宝网关易超时崩）
- 若支付宝失败换 PayPal

## 拿到 VPS 后

邮件标题 "Your RackNerd VPS is Ready"，含：
- IP Address
- root 密码
- SolusVM 面板登录（重装/重启用）

等待 10 分钟内安装完成再 SSH。
