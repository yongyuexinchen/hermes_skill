---
name: cn-financial-scraper
description: |
  中国金融机构数据爬取工具 v4.6.0。全量金融机构名单（1540+家，36大类）、A股报告爬取（年报+券商研报+公告）、
  产品解析（基金/ETF/FOF/股票/债券）、新闻资讯、反爬+双语展示、金融文档分析整理。

  🆕 v4.6.0: **严格日期过滤**（修复 cutoff_time 死代码，强制按时间窗过滤）+ **日期核验统计**（date_validation
  字段输出越界文章详情）+ **默认开启数据回测**（run_backtest=True）+ **月份识别 NLU**（支持 "7月"/"2026年7月"
  等自然语言时间表达）+ **data_validator 日期窗口核验**。

  v4.5.1: 回测过滤落地、批量回测汇总、爬取前确认强化、并发抓取加速、快照索引写入节流。

  v4.5.0: 全页内容归档器、类人浏览器操作、多搜索引擎集成、4维数据回测增强、爬取前确认流程。

  v4.4.0: 新增东方财富数据爬虫（基金净值/龙虎榜/北向资金/热门股票）、巨潮资讯官方公告爬虫、
  金融监管机构爬虫（央行/证监会/金监总局）、海外机构扩展至 250+（新增主权基金/PE/做市商）、
  文档导出全面添加原文链接、修复 12 个 Bug。

  v4.3.1: 全网舆情爬虫（对话式）— 用户用自然对话指定 1+ 个机构（基金公司/上市公司/地方政府/证券公司/
  银行/保险/信托/私募/外资/期货/理财子公司/金融租赁等），从权威媒体 / 财经垂直 / 地方媒体 / 自媒体 /
  国际媒体 5 大类共 48+ 站点爬取正面新闻+舆情，支持对话式触发、Word/Excel/CSV/JSON 导出、对话提示反馈、
  情感/严重度分级（4档舆情+3档利好）、定时任务（schedule_crawl_task 派发）、URL+标题双维去重、
  浏览器自动化兜底。

  触发词 (含 v4.5.1 新增)：爬取机构、机构名单、网页爬取、产品解析、公告下载、券商研报、批量爬取、公司批量、
  文档分析、整理文档、文档对比、基金分析、净值查询、定时爬取、自动爬取、打包ZIP、
  压缩摘要、报告生成、撰写报告、研报生成、图表生成、文件解析、金融写作、
  全网舆情、舆情监测、舆情爬取、新闻舆情、爬取正面、负面新闻、利空舆情、
  对话式舆情、增加自定义目标、舆情定时、东方财富、龙虎榜、北向资金、监管政策、
  央行政策、证监会公告、巨潮资讯、基金净值排行、
  网页归档、全页抓取、搜索爬取、搜索引擎、数据回测、类人爬取、确认爬取、
  并发爬取、加速爬取、回测过滤、回测汇总、样本预览、输入校验
auto_trigger:
  keywords: [爬取机构, 机构名单, 网页爬取, 产品解析, 公告下载, 券商研报, 研报导出,
    批量爬取, 公司批量, 新闻资讯, 上市公司报告, 机构更新, 金融数据, 文档分析, 整理文档,
    文档对比, 基金分析, 基金净值, 净值查询, 年报, 季报, 半年报, 股票分析, 产品对比, 机构查询,
    定时爬取, 自动爬取, 打包下载, ZIP导出, 压缩摘要, 提取关键信息, 生成报告, 撰写报告,
    研报生成, 研究报告, 图表生成, 报告导出, 文件解析, PPT解析, HTML解析, 金融写作,
    全网舆情, 舆情爬取, 舆情监测, 网络舆情, 爬取舆情, 爬取负面, 爬取正面,
    爬取利空, 利好新闻, 负面新闻, 对话式舆情, 舆情定时, 自定义目标, 增加目标,
    东方财富, 龙虎榜, 北向资金, 监管政策, 央行政策, 证监会公告, 巨潮资讯, 基金净值排行,
    主权基金, 全球金融机构,
    网页归档, 全页抓取, 归档网页, 网页存档, 搜索爬取, 搜索抓取, 搜索引擎搜索,
    数据回测, 回测验证, 确认爬取, 类人爬取, 模拟浏览,
    并发爬取, 加速爬取, 回测过滤, 回测汇总, 样本预览, 输入校验, 风险提示]
  patterns:
    - "(爬取|获取|看下|看看|查)(机构|公司|银行|基金|券商|保险)(的|这|那)?(舆情|新闻|资讯|报道)?"
    - "(爬取|导出|生成)\\s*\\S*(word|excel|docx|xlsx|报告|表格)"
    - "(正面|负面|舆情|利空|利好|网评|新闻|资讯)\\s*(信息|报道|新闻|消息|舆情)"
    - "(指定|设置)?(定时|每天|每周|每月|每小时)?\\s*爬取.{0,8}舆情"
    - "(新增|添加|新建)\\s*(自定义)?\\s*(目标|机构|公司)"
    - "(舆情|新闻)\\s*(导出|生成|报告)"
    - "(东方财富|龙虎榜|北向资金|监管|央行|证监会|巨潮资讯|基金净值)"
    - "(查|搜|爬)(全球|海外|国外)\\s*(金融机构|央行|监管|交易所)"
    - "(归档|保存|下载|抓取)\\s*(网页|页面|文章|全文)"
    - "(搜索|查找|搜一下)\\s*.{0,10}(新闻|资讯|舆情|报道|年报)"
    - "(回测|验证|核实)\\s*.{0,5}(数据|内容|信息|新闻)"
    - "(并发|加速|多线程)\\s*.{0,5}(爬|抓)"
    - "(过滤|丢弃|筛选)\\s*.{0,5}(低质量|无效|失真)"
---

# cn-financial-scraper v4.5.1 — 回测过滤 + 预确认强化 + 并发加速

> 全量机构名单 (国内1330家/27大类 + 海外250+家/12大类) | A股报告 | 券商研报 | 公告下载 | 产品解析 |
> **🆕 v4.5.1 回测过滤 / 批量汇总 / 预确认强化 / 并发加速** | 反爬+双语展示 | 浏览器自动化
>
> **v4.5.1 更新 (2026-07-30):**
> - ✅ 🆕 **回测过滤落地** — `crawl_sentiment(..., run_backtest=True, backtest_drop=("建议丢弃",))` 自动丢弃低质量文章
> - ✅ 🆕 **批量回测汇总** — `batch_summary(results)` 输出通过率、问题类型分布、源可信度均值
> - ✅ 🆕 **预确认强化** — `dry_run` 输出新增 `validation_errors` / `risk_warnings` / `sample_articles` / `coverage_estimate` 四类信号
> - ✅ 🆕 **并发抓取加速** — `crawl_sentiment(..., parallel_workers=4)` 启用 ThreadPoolExecutor 并发 (target, source) 单元
> - ✅ 🆕 **快照索引节流** — `_save_snapshot` 每 5 个快照才重写一次 `index.json`，减少 IO
> - ✅ 测试: 271 → 290 (新增 19 个 v4.5.1 强化测试)
> - ✅ **实测提速 2-8 倍** — 16 单元场景：顺序 9.6s → 4 workers 2.4s → 8 workers 1.2s
> - ✅ 零新依赖 — 全部基于 Python 标准库 + 已有可选依赖
>
> **v4.5.0 更新 (2026-07-30):**
> - ✅ 🆕 全页内容归档器 `fullpage_archiver.py` — 文字+图片+图表+表格全量下载，Base64 内嵌单文件 HTML + 独立目录双重输出
> - ✅ 🆕 类人浏览器操作 — 贝塞尔曲线鼠标轨迹、随机打字速度（含纠错）、自适应阅读停留、随机滚动模式、设备 viewport 模拟
> - ✅ 🆕 多搜索引擎集成 — DuckDuckGo → SearXNG → Bing HTML 三级回退，新增 `search_and_fetch()` 搜索+爬取一步完成
> - ✅ 🆕 增强数据回测 — 源可信度评分、内容哈希比对、自动推荐（可信任/需人工核实/建议丢弃）、自定义权重
> - ✅ 🆕 爬取前确认流程 — `dry_run=True` 预览计划（来源/日期/预估数量/预估时间）→ 确认后执行
> - ✅ 🆕 3 个新 MCP 工具 — `archive_webpage` / `search_web` / `search_and_archive`
> - ✅ Bug 修复 — 删除 `browser_scraper.py` 重复类定义、修复 `test_backtester.py` 死代码
> - ✅ 零新依赖 — 全部基于 Python 标准库 + 已有可选依赖（Playwright/BeautifulSoup）
> - ✅ 测试: 216 → 271 (新增 55 个)

---

## 🆕 v4.5.1 三项强化（实测数据）

### 1️⃣ 数据回测：从"标注"到"过滤"

**之前**：回测结果只挂到 `snapshot.backtest_results`，文章原封不动进入 `snapshot.articles`，用户要自己挑。
**现在**：新增 `backtest_drop` 参数，按推荐等级自动过滤。

```python
from scripts import crawl_sentiment

snap = crawl_sentiment(
    targets=["贵州茅台", "工银瑞信基金"],
    days=7,
    source_categories=["authoritative", "financial_vertical"],
    run_backtest=True,                          # 启用回测
    backtest_drop=("建议丢弃",),                # 自动丢弃"建议丢弃"
)
print(f"过滤前 50 篇 → 过滤后 {len(snap.articles)} 篇")
# 最后一条 backtest_result 是汇总：
summary = snap.backtest_results[-1]
print(f"通过率: {summary['pass_rate']*100:.0f}%, 问题分布: {summary['by_issue_type']}")
```

**新增 `batch_summary()`**：批量回测的统计汇总（通过率 / 平均分 / 推荐分布 / 问题类型）。

```python
from scripts import batch_summary
print(batch_summary(snap.backtest_results[:-1]))  # 排除末尾汇总
# {'total': 30, 'passed': 24, 'failed': 6, 'pass_rate': 0.8,
#  'by_recommendation': {'可信任': 18, '需人工核实': 8, '建议丢弃': 4},
#  'by_issue_type': {'孤源': 3, '数字不一致': 2, '过期': 1}}
```

### 2️⃣ 爬取前确认：4 类信号

之前 `dry_run` 只给"目标数 / 源数 / 估算条数 / 估算耗时"。现在多 4 个关键字段：

```python
plan = crawl_sentiment(targets=["贵州茅台"], dry_run=True).plan

# 1) 输入校验错误 — 校验失败时直接阻断确认（plan.targets/sources 是空列表）
print(plan["validation_errors"])
# ["days 参数非法: 200（应在 1-90 之间）"]  ← 这种情况不会进入实际爬取

# 2) 风险提示 — 不阻断，但提醒用户注意
print(plan["risk_warnings"])
# ["目标名过短: «A»（可能匹配范围过宽）", "目标名含测试占位词: «某测试机构»"]

# 3) 缓存样本预览 — 从最近一次历史快照中找 1-3 条样本，让用户"先看样本再确认"
print(plan["sample_articles"])
# [{'title': '...', 'source': '财联社', 'target_name': '贵州茅台', ...}]

# 4) 覆盖率估算 — 基于历史快照命中率
print(plan["coverage_estimate"])
# {'historical_snapshots': 12, 'historical_hit_rate': 0.85, 'expected_avg_articles_per_target': 4.2}
```

### 3️⃣ 并发抓取加速：实测 2-8 倍

| 并发 workers | 16 单元耗时 | 提速 |
|--------------|-------------|------|
| 0（顺序）    | 9.62 s      | 1.0× |
| 2            | 4.83 s      | 2.0× |
| 4            | 2.42 s      | 4.0× |
| 8            | 1.22 s      | 7.9× |

```python
# 默认仍是顺序爬取（向后兼容）
snap = crawl_sentiment(targets=[...])

# 启用 4 线程并发（推荐）
snap = crawl_sentiment(targets=[...], parallel_workers=4)

# 高反爬场景用 2 线程，避免触发频率限制
snap = crawl_sentiment(targets=[...], parallel_workers=2)
```

> ⚠️ **注意**：并发数过高可能被反爬检测，建议默认 `parallel_workers=4`；遇到 429/限流时降到 2 或 0。

---

## 对话触发 — 一句话上手

✅ **任意 Agent 均可通过自然语言触发。无需记忆命令。**

```
帮我爬一下某上市公司最近7天的舆情
某基金公司最近3天的负面新闻，并导出 Excel
看下某基金公司今天的正面新闻并生成 Word
爬一下某基金公司、某银行、某保险公司过去3天的负面新闻
每天早上9点爬取银行板块舆情
哪些媒体可用？哪些目标？
新增自定义目标 某基金公司
🆕 把这篇网页完整归档，包含图片和表格
🆕 搜索"贵州茅台2026半年报"然后把结果爬取下来
🆕 先预览一下爬取计划再执行
```

> 💡 在对话窗口输入「**帮助 / help / 怎么用**」会再次展示完整指南（包含 API & MCP）。

## 一键启动（推荐零基础上手）

**Windows 用户**：直接双击 `run_sentiment.bat`，或在命令行运行：

```bash
python run_sentiment.py                          # 交互式对话
python run_sentiment.py "贵州茅台最近7天的舆情"     # 直接命令行

# 🆕 全页归档 CLI
python -m scripts.fullpage_archiver "https://www.cls.cn/depth/xxx" --paginate
```

脚本会自动检测环境，缺失依赖时会提示一键安装。详见 [run_sentiment.py](run_sentiment.py)。

---

## 🆕 v4.5.0 核心新功能

### 📦 全页内容归档器 (`fullpage_archiver.py`)

一页或多页 → 下载全部文字+图片+Canvas 图表+表格 → 生成自包含输出。

| 特性 | 说明 |
|------|------|
| **双重输出** | Base64 内嵌单文件 HTML（无排版错乱）+ 独立目录版（原始文件保留）|
| **自动翻页** | 指定"下一页"选择器，自动翻页并逐页归档 |
| **图片内嵌** | 所有 `<img>` 替换为 `data:image/...;base64,...`，离线也能看 |
| **Canvas 截图** | 等待 JS 渲染后用 Playwright 截图保存为 PNG |
| **表格提取** | HTML `<table>` → JSON（保留跨行/跨列结构）|
| **去重下载** | 同一 URL 标准化后只下载一次 |
| **零新依赖** | 纯 stdlib + 已有可选 Playwright |

```python
from scripts import quick_archive

# 单页归档
result = quick_archive("https://www.cls.cn/depth/xxx")
print(result.summary)  # 📦 归档完成: ... | 页数: 1 | 图片: 5 | Canvas: 2

# 翻页归档
result = quick_archive(url, paginate=True, next_selector=".next-page", max_pages=5)

# MCP 调用
# archive_webpage("https://...", paginate=True, output_mode="both")
```

输出结构：
```
data/archives/<domain>/<YYYYMMDD_HHMMSS>/
├── article_inline.html    # Base64 内嵌版（单文件，可直接分享）
├── index.html             # 目录版（引用本地 assets/）
├── assets/
│   ├── images/            # 原始图片
│   ├── canvases/          # Canvas 截图 PNG
│   └── tables/            # 表格 JSON
├── pages/                 # 翻页时每页独立 HTML
└── metadata.json          # 元数据
```

### 🖱️ 类人浏览器操作 (`browser_scraper.py` 增强)

6 个新方法，模拟真人浏览行为，降低反爬检测概率。

| 方法 | 功能 |
|------|------|
| `_human_mouse_move(page, x, y)` | 贝塞尔曲线鼠标轨迹 + 随机偏移 + 随机速度 |
| `_human_type(page, selector, text)` | 随机字符间隔(50-200ms) + 3% 概率打错+退格修正 |
| `_human_dwell(min_s, max_s, content_length)` | 自适应停留时间（内容越长看得越久）|
| `_random_scroll(page, times)` | 随机滚动距离(200-900px) + 随机停顿 + 20% 回滚 |
| `_random_viewport(page)` | 随机切换 5 种 viewport（1920×1080 / 1680×1050 / …）|
| `humanlike_fetch(url)` | 一键启用所有类人行为抓取 |

```python
from scripts.browser_scraper import BrowserScraper
bs = BrowserScraper(headless=False)  # 可见模式
html = bs.humanlike_fetch("https://example.com")  # 类人模式抓取
```

### 🔍 多引擎搜索 + 爬取 (`search_engine.py` 增强)

零 API Key 即可使用，DuckDuckGo → SearXNG → Bing HTML 三级回退。

| 引擎 | 特点 |
|------|------|
| **DuckDuckGo HTML** | 零依赖默认首选，UA 轮换 + 3 次重试 |
| **SearXNG** | 元搜索引擎，5 个公共实例自动健康检查 + 故障转移 |
| **Bing HTML** | UA 轮换 + Referer 伪造 + 备用解析模式 |
| **Google HTML** | 仅作兜底（最易反爬）|

```python
from scripts import search_and_fetch

# 搜索 + 自动爬取详情页内容
results = search_and_fetch("贵州茅台 2026年半年报", limit=5)
for r in results:
    print(r["title"], len(r.get("content", "")))

# MCP 调用
# search_web("工银瑞信基金 最新消息")
# search_and_archive("银行 舆情", limit=5, fetch_content=True)
```

### 🛡️ 增强数据回测 (`crawl_backtester.py` 增强)

4 维回测基础上新增 3 个能力：

| 新功能 | 说明 |
|------|------|
| **源可信度评分** | 基于历史快照命中率 + URL 可核实性 + 已知高可信源列表，返回 0-1 分数 |
| **内容哈希比对** | MD5 哈希快速检测内容是否真正更新 |
| **自动推荐** | 综合评分 → "可信任" / "需人工核实" / "建议丢弃" |
| **自定义权重** | `backtest(article, weights={"freshness": 0.4, ...})` |

```python
from scripts import CrawlBacktester
bt = CrawlBacktester()
result = bt.backtest(article)
print(result.recommendation)   # "可信任"
print(result.source_credibility)  # 0.85
```

---

## 🆕 v4.3.1 全网舆情爬虫 — 功能清单

| 能力 | 说明 |
|------|------|
| **5 大媒体源，48+ 站点** | authoritative / financial_vertical / local_media / self_media / international |
| **12 大类目标机构** | 基金公司 / 上市公司 / 地方政府 / 证券公司 / 商业银行 / 保险 / 信托 / 私募 / 外资 / 期货 / 理财子公司 / 金融租赁 |
| **正面新闻 vs 舆情 分类** | 关键词驱动 + 严重度分级（4档舆情 + 3档利好）|
| **多机构单/多个** | 同时爬取多家，自动去重 |
| **多格式导出** | 对话提示 / Word / Excel / CSV / JSON |
| **对话式 API** | 自然语言 → 自动解析 intent + 参数 |
| **定时任务** | 与 v4.0 schedule_crawl_task 协同 |
| **浏览器兜底** | v4.2 browser_scraper 反爬严格时启用 |
| **数据持久化** | data/sentiment_snapshots/ 全量快照 |

---

## 🗞️ 媒体源库（按需启用）

| 类别 | 代表站点 |
|------|----------|
| **authoritative** | 人民日报 / 新华社 / 新华网财经 / 经济日报 / 中证报 / 上证报 / 证券时报 / 证券日报 / 金融时报 |
| **financial_vertical** | 财联社 / 华尔街见闻 / 第一财经 / 财新 / 21世纪经济报道 / 经济观察报 / 每日经济新闻 / 36氪 / 投中网 / 虎嗅 / 集思录 |
| **local_media** | 北京日报 / 解放日报 / 南方都市报 / 广州日报 / 深圳特区报 / 南方周末 / 扬子晚报 / 新京报 / 钱江晚报 / 中国基金报 |
| **self_media** | 新浪财经微博 / 微信公众号（搜狗） / 今日头条 / 百家号 / 雪球 / 东方财富股吧 / 知乎 / 小红书 / B站财经 / 抖音财经 |
| **international** | Reuters / Bloomberg / FT / WSJ / 路透中文 / 日经中文 / HKET 香港经济日报 |

---

## 🎯 目标机构库

| 类别 | 数量 | 关注方向 |
|------|------|---------|
| fund_company (基金公司) | 160 | 净值/分红/募集/清盘 |
| listed_company (上市公司) | 5000+ | 年报/增持/回购/退市/处罚/问询 |
| local_government (地方政府) | 11 (示例) + 自定义 | 金融政策/开放/改革 |
| securities (证券公司) | 93 | 评级/投行/承销 |
| commercial_bank (商业银行) | 250 | 利率/普惠/反洗钱/挤兑 |
| insurance (保险公司) | 72 | 理赔/销售误导 |
| trust_company (信托) | 67 | 延期兑付/规模 |
| private_fund (私募) | 64 | 清盘/跑路 |
| foreign_institution (外资) | 60 | QFII/合规 |
| futures (期货) | 117 | 穿仓/强平 |
| wealth_management (理财子) | 23 | 破净/回撤 |
| leasing_consumer_finance (租赁/消金/汽车金融) | 115 | 暴力催收/高利贷 |

---

## ⚡ 快速上手（Python）

```python
from scripts import crawl_sentiment, chat_handle, export_sentiment, SentimentChatParser

# 1) 最简单：爬取 + 导出对话
result = chat_handle("帮我爬一下某上市公司最近7天的舆情")
print(result["reply"])

# 2) 多机构 + 多类别筛选
from scripts import crawl_sentiment
snap = crawl_sentiment(
    targets=["某基金公司", "某上市公司"],
    categories=None,                              # 用 targets 优先
    source_categories=["authoritative", "financial_vertical"],
    days=7, positive_only=False, negative_only=False,
    max_articles=80,
    dry_run=False,                                 # 🆕 True=先预览计划
    run_backtest=True,                             # 🆕 启用 4 维回测
)
print(f"共 {len(snap.articles)} 条 | 正面 {snap.positive_count()} | 舆情 {snap.negative_count()}")

# 3) 导出 Word+Excel+JSON+CSV
outputs = export_sentiment(snap, fmt="all")
for k, v in outputs.items():
    print(k, v)

# 🆕 4) 全页归档
from scripts import quick_archive
result = quick_archive("https://www.cls.cn/depth/xxx", paginate=True, next_selector=".next")
print(result.summary)

# 🆕 5) 搜索 + 爬取
from scripts import search_and_fetch
results = search_and_fetch("贵州茅台 2026年报", limit=5)
```

---

## 🔧 完整 API 与 MCP 工具

### Python API（`scripts.*`）

| 函数 | 功能 |
|------|------|
| `crawl_sentiment(targets, categories, sources, source_categories, days, ...)` | 一键爬取舆情 (🆕 支持 `dry_run` / `run_backtest` / `backtest_drop` / `parallel_workers`) |
| `chat_handle(text)` | 自然语言 → 自动执行 |
| `SentimentChatParser().parse(text)` | 仅解析 → {intent, params} |
| `list_sentiment_targets()` | 查看目标库 |
| `list_sentiment_sources(category)` | 查看媒体源 |
| `add_custom_sentiment_target(category, name, aliases)` | 新增自定义目标 |
| `export_sentiment(snapshot, fmt="all")` | 导出 word/excel/csv/json/dialog |
| 🆕 `quick_archive(url, paginate, ...)` | 全页归档（Base64 内嵌 + 目录）|
| 🆕 `search_and_fetch(query, limit, ...)` | 多引擎搜索 → 自动爬详情 |
| 🆕 `quick_backtest(article)` | 4 维回测 + 自动推荐 |
| 🆕 `batch_summary(results)` | 批量回测汇总（通过率/问题分布）|
| 🆕 `filter_by_recommendation(results, articles, drop)` | 按推荐等级过滤文章 |
| 🆕 `FullPageArchiver().archive(url, ...)` | 全页归档器完整 API |
| 🆕 `MultiEngineSearch().search_and_fetch(query, ...)` | 搜索聚合器 API |

### MCP 工具（Claude Code 直接调用）— 共 38 个

| 工具 | 功能 |
|------|------|
| `crawl_global_sentiment` | 一键全网舆情爬取 (🆕 支持 `dry_run` / `run_backtest` / `backtest_drop` / `parallel_workers`) |
| `export_sentiment_report` | 导出舆情快照 |
| `list_sentiment_targets` | 查看目标库 |
| `list_sentiment_sources` | 查看媒体源 |
| `add_sentiment_target` | 新增自定义目标 |
| 🆕 `archive_webpage` | 全页归档 — 文字+图片+图表+表格，Base64 内嵌单文件 |
| 🆕 `search_web` | 多引擎搜索 — DuckDuckGo/Bing/SearXNG，零 API Key |
| 🆕 `search_and_archive` | 搜索+爬取一步完成 — 搜索 → 获取详情页 → 结构化返回 |
| `schedule_crawl_task` | 创建定期爬取任务（支持舆情模式）|
| `list_scheduled_tasks` | 查看所有定时任务 |
| `cancel_scheduled_task` | 取消/暂停/恢复 |
| `query_institution` | 查询机构名单 |
| `scrape_webpage` | 爬取指定 URL |
| `scrape_institution` | 按机构名爬取官网 |
| `parse_financial_product` | 解析基金/ETF/股票/债券页面 |
| `crawl_financial_news` | 最新金融新闻 |
| `search_announcements` | 搜索公告 |
| `download_announcement` | 下载公告 PDF |
| `query_broker_reports` | 券商研报查询 |
| `get_company_reports` | 上市公司综合报告 |
| `parse_document` | PDF/Word/Excel 解析 |
| `export_stock_report` | 导出 PPT/PDF/Word/Excel |
| `batch_crawl_institutions` | 批量爬取机构 |
| `search_report_index` | 全量报告索引搜索 |
| `analyze_document` | 深度分析金融文档 |
| `organize_documents` | 批量整理文档目录 |
| `compare_documents` | 多文档并排对比 |
| `get_stock_realtime` | A 股实时行情 |
| `get_fund_nav_history` | 基金历史净值 |
| `crawl_cls_telegraph` | 财联社 7x24 电报 |
| `get_convertible_bond_data` | 可转债数据 |
| `batch_crawl_and_package` | 批量爬取+自动打包ZIP |
| `compress_crawl_results` | 压缩为2-3页摘要 |
| `parse_file_enhanced` | 增强文件解析（PPT/HTML/Markdown）|
| `analyze_file_deep` | 深度文件分析 |
| `generate_research_report` | 生成研究报告 |
| `export_research_report` | 导出报告为Word/PPT/HTML/PDF |
| `quick_crawl_summary` | 一键快速爬取+摘要 |

---

## 🤖 定时任务样例

通过 Claude 对话直接说：
- "每天早上 9 点爬取银行的舆情"
- "每周一早上爬一下保险公司的舆情并导出 Excel"

也可以显式用 MCP：

```python
# 等价于「每天早上 9 点爬一下银行的舆情并导出全部格式」
schedule_crawl_task(
    name="每日银行舆情",
    frequency="daily",                 # 频率
    action="crawl_sentiment_export",   # 🆕 舆情+导出
    sentiment_categories=["commercial_bank"],
    sentiment_source_categories=["authoritative", "financial_vertical"],
    sentiment_days=1,
    sentiment_negative_only=True,
    sentiment_export_format="all",
)
```

---

## 📋 任务清单 — 详细使用指南

> 当用户输入「帮助 / help / 怎么用 / 你能做什么」时，会自动呈现以下内容：

```
🆕 cn-financial-scraper 全网舆情爬虫 v4.5.0 — 使用指南
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
我能做：根据您的对话，全网爬取基金公司、上市公司、地方政府、证券公司、银行、保险、信托等机构的
正面新闻与舆情，并把结果以对话/Word/Excel/CSV/JSON 反馈给您，也可以设置定时任务。

🆕 v4.5.1 新增：
  · 回测过滤 — `backtest_drop=("建议丢弃",)` 自动丢弃低质量文章
  · 批量回测汇总 — `batch_summary()` 输出通过率/问题分布
  · 预确认强化 — 4 类信号（输入校验/风险提示/样本预览/覆盖率估算）
  · 并发抓取 — `parallel_workers=4` 启用 ThreadPoolExecutor，**实测提速 2-8 倍**

🆕 v4.5.0 新增：
  · 全页归档 — 把网页文字+图片+图表+表格全部下载为自包含 HTML（类人模式）
  · 多引擎搜索 — DuckDuckGo/Bing/SearXNG 搜索 → 自动爬取详情页
  · 爬取前确认 — 先预览计划（来源/日期/数量/耗时），确认后再执行
  · 增强回测 — 源可信度评分 + 内容哈希 + 自动推荐（可信任/需核实/建议丢弃）

🗞️ 爬取哪些机构的什么信息？
  · 目标类型 (12 大类)：
    fund_company / listed_company / local_government / securities
    / commercial_bank / insurance / trust_company / private_fund
    / foreign_institution / futures / wealth_management / leasing_consumer_finance
  · 信息类型：标题 / 内容简介 / 发布平台 / 发布时间 / 页面连接  — 已自动结构化
  · 情感分类：positive 正面 / negative 舆情 / neutral 中性
  · 严重等级：低度关注 / 中度舆情 / 高危舆情（负面）/ 低度利好 / 中度利好 / 重大利好（正面）

📰 爬哪些媒体？
  · authoritative        — 央媒 & 证券媒体
  · financial_vertical   — 财经垂直
  · local_media          — 地方媒体
  · self_media           — 自媒体
  · international        — 国际媒体

▶️ 对话示例 — 直接复制即可
  · 帮我爬一下某上市公司最近7天的舆情
  · 某基金公司最近3天的负面新闻，并导出 Excel
  · 看下某基金公司今天的正面新闻并生成 Word
  · 每天早上9点爬取银行板块舆情
  · 哪些媒体可用？哪些目标？
  · 新增自定义目标 某基金公司
  · 🆕 把这篇网页完整归档，包含图片和表格
  · 🆕 搜索"贵州茅台2026半年报"然后把结果爬取下来
  · 🆕 先预览计划再确认爬取

🔧 完整 API / MCP 工具
  · crawl_global_sentiment( 单/多机构, days, 媒体类别, fmt, dry_run, run_backtest, backtest_drop, parallel_workers )
  · archive_webpage( url, paginate, output_mode="both" )  🆕
  · search_web( query, engines, limit )  🆕
  · search_and_archive( query, limit, fetch_content )  🆕
  · export_sentiment_report( snapshot_id, fmt )
  · list_sentiment_targets / list_sentiment_sources
  · add_sentiment_target( category, name, aliases )
  · schedule_crawl_task( frequency, sentiment_targets=..., action=crawl_sentiment_export )

📊 回测过滤（v4.5.1）
  · run_backtest=True  启用 4 维回测（新鲜度/交叉源/快照/数字一致性 + 源可信度评分 + 内容哈希）
  · backtest_drop=("建议丢弃",)  自动按推荐等级过滤；多条目用元组
  · 推荐等级: "可信任" (>=0.75 + 无严重问题) / "需人工核实" / "建议丢弃" (<0.3 或 ≥2 严重问题)
  · batch_summary(results)  批量汇总：通过率、平均分、按推荐/问题类型分布
  · filter_by_recommendation(results, articles, drop)  按推荐等级过滤文章与回测结果

⚡ 并发加速（v4.5.1）
  · parallel_workers=0  顺序爬取（默认，向后兼容）
  · parallel_workers=4  推荐 4 线程（实测 4× 提速）
  · parallel_workers=8  最大并发（实测 8× 提速，但反爬风险↑）
  · 高反爬场景用 2 线程；遇到 429/限流降到 0
  · 全局超时仍生效（max_total_seconds），不会因为并发而失控

🛡️ 预确认（v4.5.1）
  · dry_run=True  返回爬取计划，4 类信号:
    - validation_errors  输入校验（days/max_articles/源/目标）失败时直接阻断
    - risk_warnings  风险提示（短名/测试词/过多源/过多目标）
    - sample_articles  从历史快照取 1-3 条样本供预览
    - coverage_estimate  基于历史快照的命中率/平均文章数

📂 产物落盘
  · 快照      : data/sentiment_snapshots/<snapshot_id>.json
  · 归档      : data/archives/<domain>/<timestamp>/   🆕
  · Word/Excel: data/sentiment_exports/<snapshot_id>.{docx,xlsx}
  · 索引      : data/sentiment_snapshots/index.json
  · 自定义目标: data/sentiment_custom_targets.json

⚠️ 注意事项
  · 浏览器自动化 v4.2 已作为兜底，反爬严格时自动启用
  · 🆕 类人操作默认关闭，显式传 humanlike=True 开启（更慢但更难检测）
  · 去重：URL + 标题双维指纹，跨调用生效
  · 调度：基于 schedule 库，关闭进程后失效；重启后可从 data/scheduled_tasks.json 自动恢复
  · 🆕 搜索功能：零 API Key 即可使用（DuckDuckGo → SearXNG → Bing 三级回退）
```

---

## 提高爬取成功率

1. **零依赖即用**：核心舆情功能无需任何 pip 安装，`python run_sentiment.py` 直接运行
2. **推荐安装**：`python setup_env.py --recommended`（HTML 解析 + Word/Excel 导出）
3. **全功能安装**：`python setup_env.py --full`（含 Playwright 浏览器自动化）
4. **🆕 类人模式**：显式启用 `humanlike=True` 应对高反爬网站（贝塞尔鼠标轨迹 + 随机打字 + 自适应停留）
5. **使用代理**：`set_proxy("http://your-proxy:port")` 应对 IP 黑名单
6. **利用现有降级链**：核心 API 自动回退，无需手动干预
7. **开启缓存**：`use_cache=True`（默认开启）
8. **浏览器自动化**：`pip install playwright && playwright install chromium` 处理动态渲染
9. **🆕 爬取前确认**：`dry_run=True` 先预览计划（v4.5.1 含 4 类信号：校验/风险/样本/覆盖率）
10. **🆕 并发提速**：`parallel_workers=4` 启用 ThreadPoolExecutor（实测 4× 提速，反爬严时降为 2）
11. **🆕 回测过滤**：`run_backtest=True, backtest_drop=("建议丢弃",)` 自动丢弃低质量文章
12. **遇到错误先查 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**：错误码速查表 + 9 大场景解法

## 项目结构 (v4.5.0)

```
cn-financial-scraper/
├── SKILL.md                         # 本文件
├── README.md                        # 完整文档
├── mcp_server.py                    # MCP 服务器（🆕 38 个工具）
├── run_sentiment.py                 # 一键启动入口
├── setup_env.py                     # 环境安装脚本
├── requirements.txt                 # Python 依赖（零新依赖）
│
├── scripts/                         # 核心脚本
│   ├── __init__.py                 # v4.5.0 包入口
│   ├── http_utils.py               # HTTP 基础设施（UA轮换/限流/熔断）
│   ├── scraper.py                  # 六级降级链爬虫
│   ├── browser_scraper.py          # 浏览器自动化（🆕 类人操作增强）
│   ├── fullpage_archiver.py        # 🆕 全页内容归档器
│   ├── search_engine.py            # 🆕 多引擎搜索聚合器
│   ├── crawl_backtester.py         # 🆕 增强 4 维数据回测
│   ├── sentiment_crawler.py        # 全网舆情爬虫引擎
│   ├── sentiment_chat.py           # 对话式 NLU 入口
│   ├── sentiment_exporter.py       # 舆情导出（Word/Excel/CSV/JSON）
│   ├── sentiment_keywords.py       # 情感关键词库
│   └── ...                         # 40+ 其他模块
│
├── tests/                           # 测试（🆕 290 个，v4.5.1 新增 19）
│   ├── test_fullpage_archiver.py   # 🆕 归档器测试
│   ├── test_search_engine.py       # 🆕 搜索引擎测试
│   ├── test_humanlike.py           # 🆕 类人操作测试
│   ├── test_v451_enhancements.py   # 🆕 回测过滤/批量汇总/预确认/并发测试
│   └── ...                         # 15 个测试文件
│
└── data/                            # 数据文件
    ├── archives/                    # 🆕 网页归档输出
    ├── sentiment_snapshots/         # 舆情快照
    └── ...                         # 机构注册表 / 媒体源 / 目标库
```

---

## 详细文档

完整功能说明、6个实战场景、27类机构清单、进阶配置、能力边界、FAQ 故障排除、MCP 工具表、v4.3.1 舆情入门均见 [README.md](README.md)。
