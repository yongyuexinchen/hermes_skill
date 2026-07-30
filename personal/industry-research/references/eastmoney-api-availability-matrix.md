# 东方财富 API 可用性矩阵（中国境内网络）

> 最后验证：2026-07-30
> 网络环境：中国境内 + Clash 代理

## 已验证端点

### ✅ 稳定可用

| 端点 | 用途 | 调用方式 | 备注 |
|------|------|---------|------|
| `push2his.eastmoney.com/api/qt/stock/kline/get` | 个股/ETF K线数据 | curl/urllib | 日线/周线/月线均可用，前复权用 `fqt=1` |
| `push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.BK0467` | 板块指数K线 | curl/urllib | secid=90.板块代码 |
| `qt.gtimg.cn/q=...` | 腾讯行情（实时PE/价格/市值） | urllib | **最稳定**，编码为 gbk |

### ❌ 不可用（404/503/代理断连）

| 端点 | 用途 | 错误 | 验证日期 |
|------|------|------|---------|
| `datainterface.eastmoney.com/EM_DataCenter/JS.aspx?type=SR` | 龙虎榜日榜 | HTTP 404 | 2026-07-30 |
| `datainterface3.eastmoney.com/EM_DataCenter/JS.aspx?type=GDR` | 龙虎榜个股 | HTTP 404 | 2026-07-30 |
| `push2.eastmoney.com/api/qt/clist/get?fs=m:90+t2` | 行业板块估值 | HTTP 503 | 2026-07-30 |
| `push2.eastmoney.com/api/qt/ulist.np/get` | 批量个股行情 | RemoteDisconnected (代理断连) | 2026-07-30 |

### ⚠️ 不稳定

| 端点 | 用途 | 问题 |
|------|------|------|
| `push2.eastmoney.com/api/qt/stock/get` | 单股查询 | 偶发 RemoteDisconnected |
| `push2his.eastmoney.com/api/qt/kamt.kline/get` | 北向资金 | 需验证 |

## 回退策略

当东方财富 API 大面积不可用时：

1. **K线数据** → `push2his` 仍然可用，优先使用
2. **实时行情** → 腾讯 `qt.gtimg.cn` 始终可用
3. **龙虎榜** → **放弃**，基于K线量价关系反推主力行为
4. **北向资金** → 如不可用，标注"待补"，用K线成交额分析替代
5. **板块估值** → 从腾讯API逐只拉PE后手工计算中位数
6. **新闻/政策** → 搜狗 curl 搜索（陷阱11方法）

## 脚本编写指南

编写批量数据采集脚本时：
- **先测再跑**：对每个端点先发 1 个请求验证 HTTP 状态码
- **遇到 404 立即跳过**：不要循环重试（如本 session 的 fetch_data.py 对 31 天龙虎榜全 404）
- **优先用腾讯 API**：`qt.gtimg.cn` 直连无需代理，无速率限制
- **K线用 push2his**：`push2his.eastmoney.com` 比 `push2.eastmoney.com` 更稳定
