# 蛋卷基金估值 API 使用指南

## 端点

```
https://danjuanfunds.com/djapi/index_eva/dj?index_code=<CODE>&day=1
```

## ⚠️ 关键陷阱：index_code 过滤参数无效

蛋卷 API 的 `index_code` 查询参数**不生效**——无论传什么值，API 始终返回全部约 63 个指数的估值数据。必须在客户端解析全量 JSON 后查找目标指数。

**正确用法**：拉取全量数据，然后按 `index_code` 字段筛选：
```bash
curl -s --compressed \
  "https://danjuanfunds.com/djapi/index_eva/dj?index_code=SH000991&day=1" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['data']['items']:
    if item['index_code'] == 'SH000991':
        print(json.dumps(item, indent=2))
"
```

## 返回字段说明

| 字段 | 含义 | 说明 |
|------|------|------|
| index_code | 指数代码 | 如 SH000991（全指医药）、SZ399989（中证医疗） |
| name | 指数名称 | 中文全称 |
| pe | 当前 PE(TTM) | |
| pb | 当前 PB | |
| pe_percentile | **PE 历史分位** | 0~1，值越小越便宜。如 0.1 = 仅10%时间PE更低 |
| pb_percentile | **PB 历史分位** | 0~1，值越小越便宜 |
| pe_over_history | PE 超过历史的比例 | = 1 - pe_percentile（如 0.9 = PE 高于90%历史值） |
| pb_over_history | PB 超过历史的比例 | = 1 - pb_percentile |
| roe | ROE | 小数（如 0.094 = 9.4%） |
| yeild | 股息率 | 小数 |
| eva_type | 估值评价 | "low"=偏低, "mid"=适中, "high"=偏高 |
| eva_type_int | 估值评价码 | 0=low, 1=mid, 2=high |
| peg | PEG | （如有） |
| date | 数据日期 | MM-DD |

## 分位值解读

对于一个典型的指数：

```
pe_percentile = 0.10   → 说明 PE 仅比历史 10% 的时间高（当前 PE 处于历史低位，便宜）
pe_percentile = 0.90   → 说明 PE 比历史 90% 的时间高（当前 PE 处于历史高位，贵）
pe_over_history = 0.90 → 与上面等价：当前 PE 超过了 90% 的历史 PE 值

底层关系：pe_percentile + pe_over_history = 1.0
```

**实战口诀**：
- pe_percentile < 0.2 → 🟢 估值低位，可积极定投
- 0.2 ≤ pe_percentile < 0.5 → 🟡 估值适中
- 0.5 ≤ pe_percentile < 0.8 → 🟡 估值偏高，定投减速
- pe_percentile > 0.8 → 🔴 估值高位，暂停定投或减仓

## ⚠️ 指数代码前缀匹配技巧

实际 API 返回的 `index_code` 可能带有前缀（如 `SZ`、`CSI`、`CSIH`），与我们使用的速查代码不一定完全一致。例如：
- 查询 `930713`（中证人工智能），API 可能返回 `CSI930713`
- 查询 `H30590`（中证机器人），API 可能返回 `CSIH30590`

**正确筛选方式**：用**后缀匹配**而非精确匹配，兼容前缀变化：
```python
for item in data['data']['items']:
    code = item['index_code']  # 实际返回如 "CSI930713"
    for our_code in INDEX_CODES:
        if code.endswith(our_code) or code == our_code:
            # 找到了目标指数
```

## 常用指数代码速查

| 代码 | 名称 | 覆盖方向 |
|------|------|---------|
| SH000991 | 全指医药 | 医药整体 |
| SZ399989 | 中证医疗 | 医疗器械+服务 |
| SH000978 | 医药100 | 医药100只 |
| SZ399417 | 新能源车 | 新能源车产业链 |
| SH000827 | 中证环保 | 环保+新能源 |
| CSI930652 | 中证电子 | 电子元件+半导体 |
| CSI931079 | 5G通讯 | 5G产业链 |
| CSI931087 | 科技龙头 | 科技龙头 |
| SH000688 | 科创50 | 科创板50 |
| SH000300 | 沪深300 | 大盘基准 |
| SH000905 | 中证500 | 中盘基准 |
| SZ399006 | 创业板 | 创业板基准 |
| HKHSTECH | 恒生科技 | 港股科技 |
| SP500 | 标普500 | 美股基准 |
| NDX | 纳指100 | 美股科技 |

## 与东方财富 API 配合使用

一个完整的 A 股估值分析流程：

1. **拉取指数估值分位** → 蛋卷 API（得到板块整体的便宜/贵判断）
2. **拉取个股实时数据** → 东方财富 API（得到具体标的的价格、PE、增速）
3. **交叉验证**：板块低估 + 个股估值合理 = 定投窗口
