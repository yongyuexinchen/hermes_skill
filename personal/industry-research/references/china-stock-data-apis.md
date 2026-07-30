# 中国股市数据 API 速查

> 在中国大陆网络环境下的实测可用性记录

## API 可用性总览

| API | 域名 | 协议 | 无需代理？ | 速率限制 | 推荐用途 |
|-----|------|------|:---:|:---:|------|
| **腾讯行情** | `qt.gtimg.cn` | HTTP | ✅ 是 | 低 | 个股实时行情（最快、最稳定） |
| 东方财富 ulist.np | `push2.eastmoney.com` | HTTPS | ⚠️ 不稳定 | 高 | 批量 A 股（一次 20+ 只） |
| 东方财富 stock/get | `push2.eastmoney.com` | HTTPS | ⚠️ 不稳定 | 极高 | 港股单股查询 |
| 东方财富 push2his | `push2his.eastmoney.com` | HTTPS | ⚠️ 不稳定 | 高 | 历史 K 线（日线/周线），行情复盘 |
| 蛋卷基金估值 | `danjuanfunds.com` | HTTPS | ⚠️ 可能需要 | 中 | PE/PB 历史分位 |
| 新浪行情 | `hq.sinajs.cn` | HTTP | ✅ 是 | 低 | 备用方案 |

---

## 1. 腾讯行情 API（推荐首选）

**端点**：`http://qt.gtimg.cn/q={code}`

**特点**：
- HTTP 纯文本，无需代理直接访问
- 响应速度快（<200ms）
- 编码为 GBK，需 `.decode('gbk')`
- 字段以 `~` 分隔

**常用代码格式**：
```
sh600588  → 用友网络
sh688111  → 金山办公
sz002415  → 海康威视
sz300033  → 同花顺
```

**Python 示例**：
```python
import urllib.request

url = 'http://qt.gtimg.cn/q=sz002415,sh688111,sz300033'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=5).read().decode('gbk')

for line in data.strip().split('\n'):
    parts = line.split('~')
    if len(parts) > 40:
        name = parts[1]      # 股票名称
        price = parts[3]     # 现价
        pe = parts[39]       # PE(TTM)
        print(f'{name}: {price} PE{pe}')
```

**关键字段索引**：
| 索引 | 含义 | 备注 |
|------|------|------|
| 1 | 股票名称 | |
| 3 | 现价 | |
| 39 | PE(TTM) | |
| 44 | 总市值 | 需÷1e4 得亿元 |
| 45 | 流通市值 | 需÷1e4 得亿元 |

---

## 2. 东方财富 API（备选，功能最全）

### 端点对比速查

| 端点 | URL | 适用 | 字段 ID 体系 |
|------|-----|------|------------|
| ulist.np（批量） | `push2.eastmoney.com/api/qt/ulist.np/get` | A 股批量拉取 | f20=市值, f23=PB, f48=营收增速%, f49=利润增速%, f115=PE(TTM) |
| stock/get（单股） | `push2.eastmoney.com/api/qt/stock/get` | 港股/单股详情 | f43=现价(÷100), f164=PE(TTM)(÷100), f167=PB(÷100), f45=利润增速(÷100), f46=营收增速(÷100) |

### 批量拉取示例
```bash
curl -s --compressed \
  "https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.688111,1.600588,0.002410&fields=f2,f12,f14,f20,f23,f48,f49,f115"
```

### 速率限制陷阱
- 连续请求 >3 次/秒 → 触发封禁（`ProxyError` / `RemoteDisconnected`）
- **解决方案**：优先用 ulist.np 一次拉所有股票；单股拉取间隔 ≥1.5s
- 港股用 stock/get 单独拉（ulist.np 的 `116.` 前缀不稳定）

---

## 3. 东方财富 K 线 API（历史行情）

**端点**：`push2his.eastmoney.com/api/qt/stock/kline/get`

**用途**：拉取个股/ETF 日线/周线历史数据，复盘行情走势。

**参数说明**：

| 参数 | 含义 | 常用值 |
|------|------|--------|
| `secid` | 证券代码 | A股: `0.002371`, 科创板: `1.688981`, ETF: `0.159995` |
| `klt` | K线周期 | `101`=日线, `102`=周线, `103`=月线 |
| `fqt` | 复权方式 | `0`=不复权, `1`=前复权 |
| `beg` | 起始日期 | `20260601` |
| `end` | 结束日期 | `20260730` |
| `fields1` | 基础字段 | `f1,f2,f3,f4,f5,f6` |
| `fields2` | K线字段 | `f51,f52,f53,f54,f55,f56,f57` |

**secid 格式速查**：

| 市场 | secid 前缀 | 示例 |
|------|:---:|------|
| 深交所 A 股 | `0.` | `0.002371` (北方华创) |
| 上交所 A 股 | `1.` | `1.688981` (中芯国际) |
| 深交所 ETF | `0.` | `0.159995` (芯片ETF) |
| 上交所 ETF | `1.` | `1.512480` (半导体ETF) |

**Python 示例**：

```python
import urllib.request, json

secid = '0.159995'  # 芯片ETF
url = (
    f'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    f'?secid={secid}'
    f'&klt=101&fqt=1'
    f'&beg=20260601&end=20260730'
    f'&fields1=f1,f2,f3,f4,f5,f6'
    f'&fields2=f51,f52,f53,f54,f55,f56,f57'
    f'&ut=fa5fd1943c7b386f172d6893dbbdf45b'
)
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://quote.eastmoney.com/',
})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode())
klines = data['data']['klines']

# 每条 K 线格式: "日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率"
for line in klines:
    date, open_p, close_p, high, low, vol, amt, *_ = line.split(',')
    print(f'{date}  O={open_p}  C={close_p}  H={high}  L={low}')
```

**速率限制**：与 push2 同源，连续请求需间隔 ≥1.5 秒。优先用 ETF 作为板块代理（一次拉取覆盖整个板块趋势）。

**行情复盘技巧**：用 `execute_code` 拉取日线后，计算每日涨跌幅、标注异常日（单日涨跌 >5%），自动识别行情阶段（拉升/诱多/主跌）。

---

## 4. 蛋卷基金估值 API

**端点**：`https://danjuanfunds.com/djapi/index_eva/dj?index_code={code}`

**注意**：`index_code` 参数实际无效——API 始终返回全部 63 个指数，需从全量中查找。

---

## 5. 代理策略

| 场景 | 用代理？ | 说明 |
|------|:---:|------|
| 腾讯行情 API | ❌ 不需要 | HTTP 直连最快 |
| 新浪行情 API | ❌ 不需要 | HTTP 直连 |
| 东方财富 push2 | ⚠️ 视情况 | 有时直连通、有时需代理；不稳定的根本原因是速率限制 |
| 蛋卷基金 | ⚠️ 视情况 | 可能需要代理 |

**关键教训**：不要假设「代理一定更好」——有时关掉代理反而通。东方财富 API 失败时先检查是否触发了速率限制，再检查网络。
