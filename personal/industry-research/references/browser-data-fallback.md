# 浏览器数据回退方案（API 不可用时）

> 在中国网络下，蛋卷 API（403）、东方财富 push2（速率限制）、百度搜索（CAPTCHA）频繁不可用时的回退方案。

## 可用路径速查

| 目标 | 路径 | 方式 | 可靠性 |
|------|------|------|:---:|
| 实时行情 + PE/PB | `http://qt.gtimg.cn/q=sh600845` | `curl` 终端 | ✅ 最高 |
| 个股 PE(动) + F10 | `quote.eastmoney.com/sh600845.html` | `browser_navigate` | ✅ 高 |
| 市场情绪 + 讨论热点 | `guba.eastmoney.com/list,600845.html` | `browser_navigate` | ✅ 高 |
| PE/PB 历史分位 | 用户提供 或 标注暂缺 | — | 🟡 中 |
| 行业新闻/政策 | 直接 browser_navigate 到目标页面 | `browser_navigate` | 🟡 中 |
| 百度搜索 | ❌ 不可用（CAPTCHA） | — | 🔴 低 |

## 1. 腾讯行情 API（首选，最稳定）

```bash
curl -s "http://qt.gtimg.cn/q=sh600845,sz159992" | iconv -f gbk -t utf-8
# 字段以 ~ 分隔：索引3=现价, 39=PE, 45=总市值, 46=PB, 41=52周高, 42=52周低
```

## 2. 东方财富个股页（补充 PE(动) + 盘口数据）

```bash
browser_navigate("https://quote.eastmoney.com/sh600845.html")
# 页面包含：PE(动)、PE(TTM)、成交量、换手率、振幅
# snapshot 中直接可见这些数据，不需要 JS 交互
```

## 3. 东方财富股吧（市场情绪 + 讨论热点）

```bash
browser_navigate("https://guba.eastmoney.com/list,600845.html")
# 用途：抓取最近讨论帖标题，判断市场情绪和近期催化剂
# 例如："6月以来为何宝信巨跌" → 确认近期下跌趋势和市场恐慌
# 例如："供需缺口持续放大！AIDC五大硬核玩家" → 识别当前热门叙事
```

## 4. 数据不可用时的标注规范

当 API 均不可用时，在报告中按以下格式标注：

```markdown
> ⚠️ **数据质量问题**：蛋卷 API 被 403 拦截，东方财富 push2 速率限制。
> PE/PB 历史分位数据暂缺，以下为基于训练知识的趋势性估计 [待交叉验证]。
```

或如果用户提供了数据：

```markdown
| 编号 | 来源名称 | URL/渠道 | 优先级 | 最后访问 | 引用内容 |
|------|---------|----------|--------|---------|---------|
| — | 用户提供 | PB分位 9.12% | — | 2026-07-29 | 创新药ETF PB历史分位 |
```

## 5. 常见失败路径及回避

| 失败路径 | 表现 | 回避方式 |
|---------|------|---------|
| 百度搜索 | wappass.baidu.com CAPTCHA | 跳过搜索，直连目标 URL |
| 雪球个股页 | 空页面（xueqiu.com/S/SH600845） | 用东方财富替代 |
| 蛋卷 API | 403 Forbidden | 不重试，用腾讯 API + 用户数据 |
| 东方财富 push2 | exit code 56 / RemoteDisconnected | 降级到浏览器页面抓取 |
