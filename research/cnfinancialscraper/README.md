# cn-financial-scraper v4.3.1

> 中国大陆金融数据爬取与分析综合工具 v4.3.0

## 🆕 v4.3 新功能 — 全网舆情爬虫（对话式）

| 特性 | 说明 | 模块 |
|------|------|------|
| **对话式 NLU 入口** | 自然语言 → 自动解析 intent + 参数（爬取/导出/定时/查询/新增） | `sentiment_chat.py` |
| **5 类媒体源** | authoritative (9) + financial_vertical (11) + local_media (11) + self_media (10) + international (7)，共 48+ 站点 | `data/sentiment_sources.json` |
| **12 类目标机构** | 基金公司/上市公司/地方政府/证券公司/商业银行/保险公司/信托/私募/外资/期货/理财子/金融租赁；支持自定义扩展 | `data/sentiment_targets.json` |
| **情感分类（关键词驱动）** | positive (139 关键词) / negative (174 关键词) / neutral (35 关键词)；严重度 4 档舆情+3 档利好 | `sentiment_keywords.py` |
| **多机构单/多源组合** | 同时爬取多家，自动去重（URL + 标题双维指纹） | `sentiment_crawler.py` |
| **多格式导出** | 对话提示 / Word / Excel / CSV / JSON | `sentiment_exporter.py` |
| **定时任务集成** | 复用 v4.0 crawl_scheduler，新 action=crawl_sentiment / crawl_sentiment_export | `crawl_scheduler.py` |
| **MCP 工具新增 5 个** | `crawl_global_sentiment` / `export_sentiment_report` / `list_sentiment_targets` / `list_sentiment_sources` / `add_sentiment_target` | `mcp_server.py` |
| **浏览器自动化兜底** | v4.2 browser_scraper 反爬严格时自动启用 | `browser_scraper.py` |

## 🆕 v4.2 新功能

## 🆕 v4.1 新功能

| 特性 | 说明 | 模块 |
|------|------|------|
| **海外机构爬取** | 9大类210家全球金融机构（央行/投行/资管/对冲基金/评级/交易所/监管/数据平台/国际组织） | `overseas_scraper.py` |
| **国内全机构URL** | 16大类300+机构官网URL映射（银行/券商/基金/私募/保险/信托/期货/城商行/农商行/财经媒体/金融基础设施） | `domestic_institution_urls.json` |
| **金融术语翻译** | 600+专业术语词典 + 腾讯云TMT API自动翻译，爬取海外内容即时中英对照 | `translate_utils.py` |

## 🆕 v4.0 新功能

| 特性 | 说明 | 模块 |
|------|------|------|
| **定期自动爬取** | 定时任务调度引擎，守护线程，任务持久化，支持分钟/小时/天/周/月/cron | `crawl_scheduler.py` |
| **批量打包ZIP** | 爬取结果自动分目录→生成索引→打包ZIP（>50MB分卷） | `crawl_packager.py` |
| **内容智能压缩** | 多维度提取关键信息，压缩为2-3页精华摘要 | `content_compressor.py` |
| **增强文件解析** | PPT/PPTX、HTML网页、Markdown、CSV 解析 | `enhanced_parser.py` |
| **金融写作引擎** | 6套专业模板+matplotlib图表（趋势/柱状/饼图/雷达图） | `financial_writer.py` |
| **6套报告模板** | 个股研报/行业分析/基金评价/机构调研/市场周报/公告解读 | `report_templates.py` |
| **研究报告生成** | 全流程：采集→压缩→写作→图表→多格式导出 | `research_report_generator.py` |
| **MCP扩展** | 工具数 20→30，新增定时调度/打包/压缩/报告生成等 | `mcp_server.py` |

## 功能特性

- **1330+ 家金融机构覆盖**：基金公司、券商、银行、保险、信托、私募、外资等 27 类
- **7 大数据源**：东方财富 + 新浪财经 + 财联社 + 集思录 + 华尔街见闻 + 沪深交易所 + 天天基金
- **多类型产品解析**：基金、ETF、FOF、股票、债券、可转债、投顾组合
- **实时行情**：A 股实时价格、涨跌幅、成交量（新浪财经）
- **券商研报**：评级、分析师、目标价，支持按股票/券商查询
- **公告爬取**：搜索 + PDF 下载，覆盖沪深两市
- **新闻资讯**：东方财富/同花顺/财联社/华尔街见闻多源聚合
- **文档解析**：PDF、Word、Excel、PPT、HTML、Markdown 内容提取 🆕
- **文档分析整理**：结构化深度分析（分类/元数据/章节/财务指标/风险）、批量整理目录、多文档对比
- **报告导出**：PPT、PDF、Word、Excel、HTML 多格式导出 🆕
- **金融写作**：模板驱动+数据注入+图表生成，6套专业模板 🆕
- **研究报告生成**：全流程自动化，图文并茂、有理有据 🆕
- **定期自动爬取**：定时任务+守护线程+持久化，支持自定义cron 🆕
- **批量ZIP打包**：爬取结果自动分类目录+索引+打包 🆕
- **内容智能压缩**：2-3页精华摘要（财务/风险/行业/政策/事件多维度）🆕
- **反爬机制**：六级降级，UA轮换，自适应限流，域名熔断
- **MCP 集成**：35 个 MCP 工具，可在 Claude Code 中直接调用 🆕

## 安装

### 方式1：一键安装（推荐，自动使用国内镜像加速）

```bash
python setup_env.py
```

自动完成：
- 检测 Python 版本
- pip install 所有依赖
- 验证核心模块可导入

### 方式2：手动安装

```bash
pip install -r requirements.txt
# 可选：浏览器自动化
playwright install chromium
```

### 安装验证

```bash
python -c "from scripts import search_institution; print('安装成功！')"
```



## 一键启动（推荐零基础上手）

**Windows 用户**：直接双击 `run_sentiment.bat`，或在命令行运行：

```bash
# 交互式对话模式
python run_sentiment.py

# 直接命令行模式
python run_sentiment.py "贵州茅台最近7天的舆情"
python run_sentiment.py "工银瑞信基金最近3天的负面新闻" --export excel
```

脚本会自动检测环境，缺失依赖时会提示一键安装。

## 快速开始

```python
from scripts import parse_financial_product

# 解析基金
result = parse_financial_product("https://fund.eastmoney.com/000001.html", "fund")
print(f"基金名称: {result['product_name']}")

# 解析FOF
result = parse_financial_product(url, "fof")

# 解析投资顾问组合
result = parse_financial_product(url, "advisor")
```

## MCP 工具

通过 MCP 协议暴露 **35 个工具**，可直接在 Claude Code 中调用：

| 工具 | 功能 |
|------|------|
| `query_institution` | 查询机构名单（按类型/关键词） |
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
| 🆕 `schedule_crawl_task` | 创建定期自动爬取任务 (v4.3 扩展支持 `crawl_sentiment` / `crawl_sentiment_export`) |
| 🆕 `list_scheduled_tasks` | 查看所有定时任务及状态 |
| 🆕 `cancel_scheduled_task` | 取消/暂停/恢复定时任务 |
| 🆕 `batch_crawl_and_package` | 批量爬取+自动打包 ZIP |
| 🆕 `compress_crawl_results` | 分析压缩爬取结果为 2-3 页摘要 |
| 🆕 `parse_file_enhanced` | 增强文件解析（PPT/HTML/Markdown） |
| 🆕 `analyze_file_deep` | 深度文件分析（主题/财务/风险） |
| 🆕 `generate_research_report` | 生成图文并茂的研究报告 |
| 🆕 `export_research_report` | 导出报告为 Word/PPT/HTML/PDF |
| 🆕 `quick_crawl_summary` | 一键快速爬取+压缩摘要 |
| 🆕 `crawl_global_sentiment` | **v4.3** 一键全网舆情爬取（单/多机构 + 多媒体 + 情感筛选） |
| 🆕 `export_sentiment_report` | **v4.3** 导出舆情快照为 Word/Excel/CSV/JSON |
| 🆕 `list_sentiment_targets` | **v4.3** 查看 12 大类目标机构库 |
| 🆕 `list_sentiment_sources` | **v4.3** 查看 5 类媒体源 |
| 🆕 `add_sentiment_target` | **v4.3** 新增自定义舆情目标 |

## 项目结构

### 核心模块（必装）

```
cn-financial-scraper/
├── SKILL.md                      # Skill 完整说明（含FAQ和场景演示）
├── README.md                     # 本文件
├── setup_env.py                  # 一键安装脚本
├── mcp_server.py                 # MCP 服务器（30 个工具）
├── requirements.txt              # Python 依赖
├── _meta.json                    # 元数据
│
├── scripts/                      # 核心脚本
│   ├── __init__.py              # 包初始化
│   ├── http_utils.py            # HTTP 公共基础设施（限流/重试/缓存）
│   ├── scraper.py               # 基础爬虫（三级降级+自动重试）
│   ├── web_parser.py            # 网页解析（基金/ETF/FOF/股票）
│   ├── institution_scraper.py   # 机构爬虫
│   ├── announcement_scraper.py  # 公告爬取
│   └── data_validator.py        # 数据完整性验证
│
└── data/                         # 数据文件
    ├── institution_registry.json # 1330 家机构注册表
    └── *_list.json              # 各类机构名单（27类）
```

### 扩展模块（按需使用）

```
scripts/
├── research_report_scraper.py    # 券商研报（评级/分析师/目标价）
├── comprehensive_report_scraper.py # 综合报告统一入口
├── company_report_scraper.py     # 上市公司年报/半年报/季报
├── news_scraper.py               # 新闻爬取（东方财富/同花顺）
├── document_parser.py            # 文档解析（PDF/Word/Excel）
├── document_analyzer.py          # 文档分析整理（深度分析+批量整理+对比）
├── report_exporter.py            # 报告导出（PPT/PDF/Word/Excel）
├── batch_institution_crawler.py  # 批量爬取（并发+断点续爬）
├── report_indexer.py             # 全量报告索引（SQLite+断点续扫）
├── analyzer.py                   # 产品分析（风险指标+投资风格）
├── visualization_reporter.py     # 可视化报告（ASCII图表）
├── realtime_monitor.py           # 实时监控（动态页面检测）
├── full_institution_crawler.py   # 全量爬虫（从监管机构获取）
├── institution_updater.py        # 季度自动更新
├── scrapable_registry.py         # 可爬取机构注册表

# 🆕 v4.0 新增模块
├── crawl_scheduler.py            # 定期自动爬取调度引擎
├── crawl_packager.py             # 批量爬取结果 ZIP 打包
├── content_compressor.py         # 内容智能压缩（2-3页精华摘要）
├── enhanced_parser.py            # 增强文件解析（PPT/HTML/Markdown/CSV）
├── financial_writer.py           # 金融分析写作引擎 + ChartBuilder
├── report_templates.py           # 6套金融报告模板库
└── research_report_generator.py  # 研究报告全流程生成器
```

### 模块功能速查

| 需求 | 使用模块 | 示例 |
|------|----------|------|
| 查询机构名单 | `institution_scraper.py` | `search_institution("华夏基金")` |
| 解析基金/股票 | `web_parser.py` | `parse_financial_product(url, "fund")` |
| 下载公告 | `announcement_scraper.py` | `AnnouncementManager().search("贵州茅台")` |
| 查询研报 | `research_report_scraper.py` | `BrokerReportManager().query("600519")` |
| 批量爬取 | `batch_institution_crawler.py` | `BatchInstitutionCrawler().crawl_by_type("基金")` |
| 生成报告 | `report_exporter.py` | `ReportExporter().export_to_ppt(data)` |
| 文档分析 | `document_analyzer.py` | `DocumentAnalyzer().analyze("report.pdf")` |
| 数据验证 | `data_validator.py` | `python scripts/data_validator.py` |
| 🆕 定期自动爬取 | `crawl_scheduler.py` | `create_scheduled_task("每日新闻", "daily")` |
| 🆕 批量打包ZIP | `crawl_packager.py` | `batch_crawl_and_package(names="华夏基金")` |
| 🆕 内容压缩摘要 | `content_compressor.py` | `compress_content(source, focus="财务")` |
| 🆕 增强文件解析 | `enhanced_parser.py` | `parse_file_enhanced("slides.pptx")` |
| 🆕 金融写作 | `financial_writer.py` | `generate_report(data, template_id="stock_research")` |
| 🆕 报告模板 | `report_templates.py` | `render_template("fund_evaluation", data)` |
| 🆕 研究报告生成 | `research_report_generator.py` | `generate_research_report("600519", "stock_research")` |

## 全量金融机构名单（1330 家 / 27 大类）

| 文件 | 内容 | 数量 |
|------|------|------|
| `data/institution_registry.json` | 统一注册表（含 URL） | 1330 家 |
| `data/state_owned_bank_list.json` | 国有大型商业银行 | 6 家 |
| `data/joint_stock_bank_list.json` | 股份制商业银行 | 12 家 |
| `data/policy_bank_list.json` | 政策性银行 | 3 家 |
| `data/city_commercial_bank_list.json` | 城市商业银行 | 122 家 |
| `data/rural_commercial_bank_list.json` | 农村商业银行 | 107 家 |
| `data/fund_company_list.json` | 基金管理公司 | 160 家 |
| `data/securities_list.json` | 证券公司 | 93 家 |
| `data/insurance_list.json` | 保险公司 | 72 家 |
| `data/trust_company_list.json` | 信托公司 | 67 家 |
| `data/private_fund_list.json` | 私募基金管理公司 | 64 家 |
| `data/foreign_institution_list.json` | 外资金融机构 | 60 家 |
| `data/futures_list.json` | 期货公司 | 117 家 |
| `data/futures_risk_mgmt_list.json` | 期货风险管理子公司 | 94 家 |
| `data/finance_company_list.json` | 企业集团财务公司 | 50 家 |
| `data/insurance_asset_list.json` | 保险资产管理公司 | 34 家 |
| `data/consumer_finance_list.json` | 消费金融公司 | 30 家 |
| `data/financing_guarantee_list.json` | 融资担保公司 | 30 家 |
| `data/financial_lease_list.json` | 金融租赁公司 | 60 家 |
| `data/auto_finance_list.json` | 汽车金融公司 | 25 家 |
| `data/wealth_management_list.json` | 银行理财子公司 | 23 家 |
| `data/fund_subsidiary_list.json` | 基金子公司 | 15 家 |
| `data/financial_holding_list.json` | 金融控股公司 | 15 家 |
| `data/third_party_list.json` | 第三方销售机构 | 35 家 |
| `data/reinsurance_list.json` | 再保险公司 | 6 家 |
| `data/money_broker_list.json` | 货币经纪公司 | 6 家 |
| `data/aic_list.json` | 金融资产投资公司(AIC) | 5 家 |
| `data/city_investment_list.json` | 城投机构 | 102 家 |

```bash
python -m scripts.scrapable_registry stat          # 统计
python -m scripts.scrapable_registry list 基金管理公司  # 按类列出
python -m scripts.scrapable_registry search 华夏     # 关键词搜索
```


## 🆕 v4.3 全网舆情爬虫 — 实战场景

### 场景 A — 单机构 + 单一情感（对话式）

> "帮我爬一下贵州茅台最近7天的舆情"

```python
from scripts import chat_handle
print(chat_handle("帮我爬一下贵州茅台最近7天的舆情")["reply"])
```

对话式触发后，引擎自动完成：
1. 抽取目标：贵州茅台（listed_company）
2. 媒体默认：authoritative + financial_vertical
3. 时间窗：7 天
4. 情感：负面优先（用户用了"舆情" 一词）
5. 输出：对话提示 + data/sentiment_snapshots/<id>.json

### 场景 B — 多机构 + 负面新闻 + 多格式导出

> "看下华夏基金、招商银行、中国人寿过去3天的负面新闻，并导出 Excel/Word"

```python
from scripts import crawl_sentiment, export_sentiment
snap = crawl_sentiment(
    targets=["华夏基金", "招商银行", "中国人寿"],
    days=3, negative_only=True,
    source_categories=["authoritative", "financial_vertical"],
)
outputs = export_sentiment(snap, fmt="all")
for k, v in outputs.items():
    print(k, v)
```

### 场景 C — 定时任务

> "每天早上 9 点爬一下银行的舆情并导出全部格式"

```python
schedule_crawl_task(
    name="每日银行舆情",
    frequency="daily",
    action="crawl_sentiment_export",
    sentiment_categories=["commercial_bank"],
    sentiment_source_categories=["authoritative", "financial_vertical"],
    sentiment_negative_only=True,
    sentiment_export_format="all",
)
```

### 场景 D — 类别查看 / 自定义目标

```python
from scripts import list_sentiment_targets, add_custom_sentiment_target
print(list_sentiment_targets())
add_custom_sentiment_target("custom", "恒生电子")
```

### CLI 调试

```bash
python -m scripts.sentiment_crawler --stats
python -m scripts.sentiment_crawler --list-sources
python -m scripts.sentiment_crawler --list-targets
python -m scripts.sentiment_crawler     --categories fund_company,listed_company     --source-categories authoritative,financial_vertical     --days 7 --negative-only --max 30
```

### 严重度阈值

| 严重度（正面） | 阈值（情感分数） |
|----------------|------------------|
| 低度利好 | 6 – 14 |
| 中度利好 | 15 – 29 |
| 重大利好 | ≥ 30 |

| 严重度（负面） | 阈值 |
|----------------|------|
| 低度关注 | 6 – 11 |
| 中度舆情 | 12 – 24 |
| 高危舆情 | ≥ 25 |

## 能力边界

| 类别 | 说明 |
|------|------|
| ✅ 支持 | 机构名单查询、基金/ETF/FOF/股票产品解析、公告搜索下载、券商研报、新闻资讯、批量爬取（断点续爬）、文档解析（PDF/Word/Excel/PPT/HTML/Markdown）、报告导出（PPT/PDF/Word/Excel/HTML）、文档深度分析/整理/对比、🆕定期自动爬取、🆕批量打包ZIP、🆕内容智能压缩、🆕金融写作、🆕6套报告模板、🆕研究报告全流程生成 |
| ❌ 不支持 | 需登录页面、付费数据、历史数据全量导出 |
| ⚠️ 部分支持 | 动态渲染页面（需 Playwright，用 `mode="realtime"`）、大批量爬取（需控并发+断点续爬）、验证码页面 |

**预期成功率**：天天基金 95%+ / 东方财富 90%+ / 同花顺 85%+ / 基金公司官网 70-90%。

## 数据验证

```bash
# 验证数据完整性
python scripts/data_validator.py

# 验证结果示例
# ✅ institution_registry.json: 验证通过，共 1330 家机构
# ✅ fund_company_list.json: 验证通过，共 160 家机构
# ...
# 📈 汇总: 28/28 通过
```

## 常见问题

> 📘 **想看更详细的故障排查？** 见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)（9 个章节 / 30+ 个解法 / 错误码速查表）。
> 🔒 **安全审计与漏洞披露**：见 [SECURITY.md](SECURITY.md)。

### 安装问题

| 问题 | 解决方案 |
|------|----------|
| pip 安装慢 | 使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| playwright 安装失败 | 运行 `playwright install --with-deps chromium` |
| 模块找不到 | 运行 `pip install -r requirements.txt` |
| 多 Python 环境冲突 | 详见 [TROUBLESHOOTING.md §1.4](TROUBLESHOOTING.md#14-不同-python-解释器混乱) |

### 爬取问题

| 问题 | 解决方案 |
|------|----------|
| 返回空数据 | 使用动态渲染：`mode="realtime"` |
| 频繁超时 | 增加超时时间：`timeout=60` |
| 验证码拦截 | 降低爬取频率，稍后重试 |
| 爬取中断 | 使用断点续爬功能 |
| IP 被封 403 | [TROUBLESHOOTING.md §3.1](TROUBLESHOOTING.md#31-ip-被封--一直-403) |
| 中文乱码 / UnicodeDecodeError | [TROUBLESHOOTING.md §4.1](TROUBLESHOOTING.md#41-中文乱码--unicodedecodeerror) |
| PDF 解析乱码 | [TROUBLESHOOTING.md §4.2](TROUBLESHOOTING.md#42-pdf-解析出乱码文字) |

### 数据问题

| 问题 | 解决方案 |
|------|----------|
| 机构名单为空 | 运行 `python scripts/data_validator.py` 检查 |
| 数据格式异常 | 使用 `parse_financial_product` 自动解析 |
| JSON 损坏 | [TROUBLESHOOTING.md §6.1](TROUBLESHOOTING.md#61-data_validatorpy-报错-json-解析失败) |

## 支持的数据源

| 类型 | 平台 |
|------|------|
| 实时行情 | 🆕 新浪财经 (hq.sinajs.cn) |
| 快讯电报 | 🆕 财联社 (cls.cn) |
| 深度分析 | 🆕 华尔街见闻 (wallstreetcn.com) |
| 可转债 | 🆕 集思录 (jisilu.cn) |
| 官方公告 | 🆕 上交所/深交所 (sse.com.cn/szse.cn) |
| 基金 | 天天基金、东方财富、各基金公司官网 |
| ETF | 各大交易所、天天基金 |
| 公告 | 天天基金、巨潮资讯 |
| 研报 | 东方财富研报中心 |
| 新闻 | 东方财富、同花顺、财联社 |
| 行情 | 雪球 (xueqiu.com) |
| 组合 | 且慢、蛋卷基金、雪球 |
| 宏观 | 国家统计局、人民银行（待上线） |

## 许可证

MIT License
