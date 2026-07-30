#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cn-financial-scraper MCP Server — 中国金融数据爬取与研究工具
通过 MCP 协议暴露机构查询、网页爬取、产品解析、公告下载、新闻资讯等工具，
让 Claude Code 可以直接调用中国金融数据爬虫的核心功能。

使用方式（Claude Code 配置 mcpServers）:
{
  "mcpServers": {
    "cn-financial-scraper": {
      "command": "python",
      "args": ["./mcp_server.py"],
      "env": {
        "PYTHONDONTWRITEBYTECODE": "1"
      }
    }
  }
}
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import json
import os
import logging
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    print(f"❌ MCP SDK 不可用: {e}", file=sys.stderr)
    print("请运行: pip install mcp", file=sys.stderr)
    sys.exit(1)

# 顶层导入核心模块（避免每次工具调用重复 import）
try:
    from scrapable_registry import ScrapableRegistry
except ImportError:
    ScrapableRegistry = None

try:
    from scraper import FinancialPageScraper
except ImportError:
    FinancialPageScraper = None

try:
    from institution_scraper import InstitutionScraper
except ImportError:
    InstitutionScraper = None

try:
    from news_scraper import EastMoneyNewsAPI
except ImportError:
    EastMoneyNewsAPI = None

try:
    from announcement_scraper import AnnouncementManager, PDFDownloader
except ImportError:
    AnnouncementManager = PDFDownloader = None

try:
    from research_report_scraper import BrokerReportManager
except ImportError:
    BrokerReportManager = None

try:
    from comprehensive_report_scraper import ComprehensiveReportManager
except ImportError:
    ComprehensiveReportManager = None

try:
    from document_parser import parse_document as doc_parse
except ImportError:
    doc_parse = None

try:
    from report_exporter import ComprehensiveExporter
except ImportError:
    ComprehensiveExporter = None

try:
    from batch_institution_crawler import BatchInstitutionCrawler
except ImportError:
    BatchInstitutionCrawler = None

try:
    from report_indexer import StockIndexer
except ImportError:
    StockIndexer = None

try:
    from document_analyzer import DocumentAnalyzer
except ImportError:
    DocumentAnalyzer = None

# v3.0 新增数据源
try:
    from sina_scraper import get_realtime_quote as sina_quote, get_stock_brief
except ImportError:
    sina_quote = get_stock_brief = None

try:
    from cls_scraper import get_telegraph as cls_telegraph, get_hot_articles as cls_articles
except ImportError:
    cls_telegraph = cls_articles = None

try:
    from jisilu_scraper import get_convertible_bonds as jisilu_bonds, search_bonds as jisilu_search
except ImportError:
    jisilu_bonds = jisilu_search = None

try:
    from stock_list_updater import get_stock_list
except ImportError:
    get_stock_list = None

# v4.0 新增模块
try:
    from crawl_scheduler import CrawlScheduler, get_scheduler, create_scheduled_task, list_all_tasks
except ImportError:
    CrawlScheduler = get_scheduler = create_scheduled_task = list_all_tasks = None

try:
    from crawl_packager import CrawlPackager, batch_crawl_and_package as _batch_crawl_and_package, package_crawl_results
except ImportError:
    CrawlPackager = batch_crawl_and_package = package_crawl_results = None

try:
    from content_compressor import ContentCompressor, compress_content, compress_multiple, CompressConfig
except ImportError:
    ContentCompressor = compress_content = compress_multiple = CompressConfig = None

try:
    from enhanced_parser import MultiFormatParser, parse_file_enhanced as _parse_file_enhanced, PPTXParser, HTMLParser
except ImportError:
    MultiFormatParser = parse_file_enhanced = PPTXParser = HTMLParser = None

try:
    from report_templates import list_templates as list_report_templates, get_template, render_template, get_template_outline
except ImportError:
    list_report_templates = get_template = render_template = get_template_outline = None

try:
    from financial_writer import FinancialWriter, ChartBuilder, generate_report, generate_report_from_raw, WriterConfig
except ImportError:
    FinancialWriter = ChartBuilder = generate_report = generate_report_from_raw = WriterConfig = None

try:
    from research_report_generator import ResearchReportGenerator, generate_research_report as _generate_research_report, quick_report, ReportConfig, ReportTheme
except ImportError:
    ResearchReportGenerator = generate_research_report = quick_report = ReportConfig = ReportTheme = None

# v4.3 全网舆情爬虫
try:
    from sentiment_crawler import (
        SentimentCrawler, SentimentSourceLoader, SentimentTargetLoader,
        crawl_sentiment as _crawl_sentiment,
        list_sentiment_targets as _list_sentiment_targets,
        list_sentiment_sources as _list_sentiment_sources,
        add_custom_sentiment_target as _add_custom_target,
    )
except ImportError:
    SentimentCrawler = SentimentSourceLoader = SentimentTargetLoader = None
    _crawl_sentiment = _list_sentiment_targets = _list_sentiment_sources = _add_custom_target = None

try:
    from sentiment_exporter import export as _export_sentiment
except ImportError:
    _export_sentiment = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mcp_server")

server = FastMCP("cn-financial-scraper")


def _module_error(module_name: str, install_hint: str = "") -> str:
    """生成模块缺失的错误信息（含安装指引）"""
    hint = install_hint or f"pip install -r requirements.txt"
    return f"❌ {module_name} 模块未安装，请运行: {hint}"


# ==================== 机构名单查询 ====================

@server.tool()
async def query_institution(institution_type: str = "", keyword: str = "") -> str:
    """查询中国金融机构名单。支持按类型筛选和关键词搜索。
    机构类型（27大类）: 基金管理公司, 证券公司, 保险公司, 信托公司, 商业银行, 
    私募基金, 外资金融机构, 金融租赁, 第三方销售, 理财公司, 期货公司,
    消费金融公司, 保险资产管理公司, 再保险公司, 汽车金融公司, 金融控股公司,
    货币经纪公司, 金融资产投资公司, 企业集团财务公司, 融资担保公司,
    期货风险管理子公司, 城投机构等。

    Args:
        institution_type: 机构类型（留空查询全部）
        keyword: 搜索关键词，如"华夏"、"招商"（可选）
    """
    try:
        if ScrapableRegistry is None:
            return _module_error("scrapable_registry")
        registry = ScrapableRegistry()

        if keyword:
            results = registry.search(keyword)
            if not results:
                return f"未找到包含「{keyword}」的机构。"
            lines = [f"🔍 搜索「{keyword}」结果 ({len(results)}条):", ""]
            for r in results[:30]:
                scrapable = r.get('scrapable', False)
                website = r.get('website', '') or ''
                lines.append(
                    f"  {r['name']}  [{r['type']}]  "
                    f"{'✅ ' + website if scrapable and website else '❌ 无URL'}"
                )
            return '\n'.join(lines)

        stats = registry.get_statistics()
        lines = [
            f"📊 全量金融机构统计 ({stats['total']}家)",
            f"可爬取: {stats['scrapable']}家",
            "",
            "按类型统计:",
        ]
        for t, info in sorted(stats.get('by_type', {}).items(), key=lambda x: -x[1]['total']):
            lines.append(f"  {t}: {info['total']}家 ({info['scrapable']}可爬取)")

        if institution_type:
            insts = registry.list_by_type(institution_type)
            lines.extend(["", f"「{institution_type}」列表 ({len(insts)}家):"])
            for i in insts[:20]:
                website = i.get('website', '') or ''
                scrapable = i.get('scrapable', False)
                lines.append(
                    f"  {i['name']}  {'✅ ' + website if scrapable and website else ''}"
                )
            if len(insts) > 20:
                lines.append(f"  ... 还有 {len(insts)-20} 家")

        return '\n'.join(lines)
    except Exception as e:
        return f"查询失败: {str(e)}"


# ==================== 网页爬取 ====================

@server.tool()
async def scrape_webpage(url: str, use_dynamic: bool = False) -> str:
    """爬取指定URL的网页内容，返回文字摘要。
    支持静态页面和动态渲染（JavaScript）两种模式。
    适用场景：爬取金融机构官网、新闻页面、产品页面等。

    Args:
        url: 完整网页URL
        use_dynamic: 是否使用动态渲染（处理JS加载的页面），默认False
    """
    try:
        if FinancialPageScraper is None:
            return _module_error("scraper")
        scraper = FinancialPageScraper()
        content = scraper.scrape_url(url, use_dynamic=use_dynamic)
        if content:
            text = str(content)[:3000]
            return f"✅ 成功获取 {len(text)} 字符\n\n{text}"
        return f"❌ 爬取失败，目标网站可能有限流或需要登录。"
    except Exception as e:
        return f"爬取失败: {str(e)}"


@server.tool()
async def scrape_institution(name: str) -> str:
    """按机构名称爬取其官网内容。自动从注册表中查找URL并爬取。
    适用场景：需要快速获取某金融机构的官网最新信息。

    Args:
        name: 机构名称关键词，如"华夏基金"、"招商证券"
    """
    try:
        if InstitutionScraper is None:
            return _module_error("institution_scraper")
        scraper = InstitutionScraper()
        result = scraper.scrape_by_name(name)
        if result and result.get('content'):
            text = result['content'][:2000]
            return (
                f"✅ {result.get('name', name)} 爬取成功\n"
                f"来源: {result.get('url', '未知')}\n"
                f"内容:\n{text}"
            )
        return f"❌ 未找到机构「{name}」或爬取失败。"
    except Exception as e:
        return f"爬取失败: {str(e)}"


# ==================== 金融产品解析 ====================

@server.tool()
async def parse_financial_product(url: str, product_type: str = "fund") -> str:
    """解析金融产品页面信息。支持基金、ETF、FOF、股票、债券等。
    适用场景：需要提取某只基金/股票/债券的详细产品信息。

    Args:
        url: 产品页面URL，如天天基金、东方财富产品页
        product_type: 产品类型 — fund(基金) / etf(ETF) / fof(FOF) / stock(股票) / bond(债券)
    """
    try:
        # 动态导入 web_parser
        import importlib
        web_parser = importlib.import_module("web_parser")
        result = web_parser.parse_financial_product(url, product_type)
        if result:
            text = json.dumps(result, ensure_ascii=False, indent=2)[:2500]
            return f"✅ {product_type.upper()} 解析成功\n\n{text}"
        return f"❌ 解析失败，请检查URL或产品类型。"
    except Exception as e:
        return f"解析失败: {str(e)}"


# ==================== 新闻资讯 ====================

@server.tool()
async def crawl_financial_news(limit: int = 10) -> str:
    """爬取最新金融新闻资讯。来源：东方财富、同花顺。
    适用场景：了解最新金融动态、市场热点、政策变化。

    Args:
        limit: 返回条数，默认10，最多30
    """
    try:
        if EastMoneyNewsAPI is None:
            return _module_error("news_scraper")
        scraper = EastMoneyNewsAPI()
        # v4.4.0 修复：fetch_latest() 不存在，改用 get_market_news()
        try:
            news = scraper.get_market_news(limit=min(limit, 30))
        except Exception:
            news = scraper.get_stock_news(limit=min(limit, 30))
        if not news:
            return "暂无新闻数据。"
        lines = [f"📰 最新金融新闻 ({len(news)}条)", ""]
        for i, item in enumerate(news, 1):
            title = item.get('title', '无标题')
            source = item.get('source', '')
            date = item.get('date', '')
            lines.append(f"  {i:>2}. [{source}] {title}  ({date})")
        return '\n'.join(lines)
    except Exception as e:
        return f"新闻爬取失败: {str(e)}"


# ==================== 公告搜索与下载 ====================

@server.tool()
async def search_announcements(keyword: str, limit: int = 10) -> str:
    """搜索上市公司公告。覆盖沪深两市上市公司公告。
    适用场景：查询某公司或某关键词的最新公告。

    Args:
        keyword: 搜索关键词，如"华夏基金"、"分红"、"业绩预告"
        limit: 返回条数，默认10
    """
    try:
        if AnnouncementManager is None:
            return _module_error("announcement_scraper")
        scraper = AnnouncementManager()
        announcements = scraper.search(keyword, limit=min(limit, 20))
        if not announcements:
            return f"未找到包含「{keyword}」的公告。"
        lines = [f"📋 公告搜索结果「{keyword}」({len(announcements)}条)", ""]
        for i, ann in enumerate(announcements, 1):
            lines.append(
                f"  {i:>2}. {ann.get('title', '无标题')}  "
                f"{ann.get('date', '')}  {ann.get('code', '')}"
            )
        lines.append("")
        lines.append("提示: 需要下载PDF可使用 download_announcement 工具")
        return '\n'.join(lines)
    except Exception as e:
        return f"公告搜索失败: {str(e)}"


@server.tool()
async def download_announcement(url: str, save_dir: str = "") -> str:
    """下载公告PDF文件到本地。
    需先通过 search_announcements 获取公告URL。

    Args:
        url: 公告PDF的下载链接
        save_dir: 保存目录（可选，默认保存到 data/announcements/）
    """
    try:
        if PDFDownloader is None:
            return _module_error("announcement_scraper")
        scraper = PDFDownloader()
        output_dir = save_dir or str(SCRIPT_DIR / "data" / "announcements")
        os.makedirs(output_dir, exist_ok=True)
        path = scraper.download(url, save_dir=output_dir)
        return f"✅ PDF已下载到: {path}"
    except Exception as e:
        return f"下载失败: {str(e)}"


# ==================== 券商研报查询 ====================

@server.tool()
async def query_broker_reports(stock_code: str = "", broker_name: str = "") -> str:
    """查询券商研究报告。支持按股票代码或券商名称筛选。
    适用场景：查询个股的最新券商研报评级、目标价、分析观点。

    Args:
        stock_code: 6位股票代码，如 600519（可选）
        broker_name: 券商名称，如"中金公司"、"中信证券"（可选）
    """
    try:
        if BrokerReportManager is None:
            return _module_error("research_report_scraper")
        manager = BrokerReportManager()

        if stock_code:
            result = manager.generate_report_summary(stock_code)
            if result:
                return f"【{stock_code} 券商研报】\n\n{result[:3000]}"
            return f"未找到 {stock_code} 的券商研报。"

        if broker_name:
            reports = manager.get_reports_by_broker(broker_name)
            if reports:
                lines = [f"📊 {broker_name} 研报 ({len(reports)}条)", ""]
                for r in reports[:15]:
                    lines.append(
                        f"  {r.get('stock_code', '')} {r.get('stock_name', '')}  "
                        f"评级:{r.get('rating', '')}  目标价:{r.get('target_price', '?')}"
                    )
                return '\n'.join(lines)
            return f"未找到 {broker_name} 的研报。"

        return "请提供 stock_code 或 broker_name 参数。"
    except Exception as e:
        return f"查询失败: {str(e)}"


# ==================== 综合报告查询 ====================

@server.tool()
async def get_company_reports(stock_code: str) -> str:
    """获取上市公司综合报告（年报/半年报/季报+券商研报）。
    适用场景：一站式查询某只股票的定期报告和最新研报。

    Args:
        stock_code: 6位股票代码
    """
    try:
        if ComprehensiveReportManager is None:
            return _module_error("comprehensive_report_scraper")
        manager = ComprehensiveReportManager()
        data = manager.get_all_reports(stock_code)
        if not data:
            return f"未获取到 {stock_code} 的报告数据。"
        summary = manager.generate_report_summary(stock_code)
        return f"【{stock_code} 综合报告】\n\n{summary[:3000]}"
    except Exception as e:
        return f"查询失败: {str(e)}"


# ==================== 文档解析 ====================

@server.tool()
async def parse_document(file_path: str) -> str:
    """解析金融文档内容（PDF/Word/Excel）。
    适用场景：读取金融PDF研报、Word报告、Excel数据表格。

    Args:
        file_path: 文档完整路径
    """
    try:
        if doc_parse is None:
            return _module_error("document_parser")
        ext = Path(file_path).suffix.lower()
        supported = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.md', '.csv'}
        if ext not in supported:
            return f"不支持的文件格式: {ext}。支持: {', '.join(sorted(supported))}"

        result = doc_parse(file_path)
        if isinstance(result, dict) and result.get("error"):
            return f"❌ {result['error']}"

        text = result.get("text_content", "") if isinstance(result, dict) else str(result)
        if text:
            content = text[:3000]
            return f"✅ 解析成功 ({len(text)}字符)\n\n{content}"
        return "❌ 解析失败，文件可能已损坏或加密。"
    except Exception as e:
        return f"解析失败: {str(e)}"


# ==================== 研报导出 ====================

@server.tool()
async def export_stock_report(stock_code: str, formats: str = "xlsx") -> str:
    """导出上市公司研究报告。支持PPT/PDF/Word/Excel多种格式。
    适用场景：将股票研究数据导出为可打印或可编辑的文档。

    Args:
        stock_code: 6位股票代码
        formats: 导出格式，逗号分隔，如"ppt,docx,xlsx"（默认xlsx）
    """
    try:
        if ComprehensiveExporter is None or ComprehensiveReportManager is None:
            return _module_error("report_exporter 或 comprehensive_report_scraper")

        manager = ComprehensiveReportManager()
        data = manager.get_all_reports(stock_code)

        if not data:
            return f"未获取到 {stock_code} 的报告数据。"

        exporter = ComprehensiveExporter()
        fmt_list = [f.strip() for f in formats.split(",")]
        output = str(SCRIPT_DIR / "data" / "reports")
        os.makedirs(output, exist_ok=True)

        lines = [f"📁 导出 {stock_code} 报告", ""]
        for fmt in fmt_list:
            try:
                if fmt == 'ppt':
                    from report_exporter import PPTExporter
                    path = PPTExporter().export_comprehensive_report(data, stock_code, output)
                elif fmt == 'docx':
                    from report_exporter import WordExporter
                    path = WordExporter().export_comprehensive_report(data, stock_code, output)
                elif fmt == 'xlsx':
                    from report_exporter import ExcelExporter
                    path = ExcelExporter().export_comprehensive_report(data, stock_code, output)
                elif fmt == 'pdf':
                    from report_exporter import PDFExporter
                    path = PDFExporter().export_comprehensive_report(data, stock_code, output)
                else:
                    lines.append(f"  ❌ 不支持格式: {fmt}，支持: ppt, docx, xlsx, pdf")
                    continue
                lines.append(f"  ✅ .{fmt} -> {path}")
            except Exception as e:
                lines.append(f"  ❌ .{fmt} 导出失败: {str(e)}")

        return '\n'.join(lines)
    except ImportError as e:
        return f"缺少导出依赖库: {e}。请安装: python-pptx / reportlab / openpyxl"
    except Exception as e:
        return f"导出失败: {str(e)}"


# ==================== 批量爬取 ====================

@server.tool()
async def batch_crawl_institutions(names: str = "",
                                   institution_type: str = "") -> str:
    """批量爬取金融机构信息。支持按名称列表或机构类型批量操作。
    适用场景：需要同时获取多家机构的官网最新信息。

    Args:
        names: 机构名称列表，逗号分隔，如"易方达基金,华夏基金,广发基金"
        institution_type: 机构类型，如"基金管理公司"、"证券公司"（与names二选一）
    """
    try:
        if BatchInstitutionCrawler is None:
            return _module_error("batch_institution_crawler")
        crawler = BatchInstitutionCrawler()

        if names:
            inst_list = [{"name": n.strip()} for n in names.split(",")]
            results = crawler.crawl_by_names(inst_list)
        elif institution_type:
            results = crawler.crawl_by_type(institution_type)
        else:
            return "请提供 names 或 institution_type 参数。"

        lines = [f"📊 批量爬取完成 ({len(results)}家)", ""]
        for r in results[:20]:
            name = r.get('name', '?')
            status = '✅' if r.get('success') else '❌'
            lines.append(f"  {status} {name}")
        if len(results) > 20:
            lines.append(f"  ... 还有 {len(results)-20} 家")

        return '\n'.join(lines)
    except Exception as e:
        return f"批量爬取失败: {str(e)}"


# ==================== 全量索引查询 ====================

@server.tool()
async def search_report_index(keyword: str, report_type: str = "") -> str:
    """在全量报告索引中搜索，支持按类型筛选。
    适用场景：搜索全市场股票报告中包含某关键词的条目。

    Args:
        keyword: 搜索关键词，如"分红"、"回购"、"业绩预增"
        report_type: 报告类型 — periodic(定期报告) / broker(券商研报)（可选）
    """
    try:
        if StockIndexer is None:
            return _module_error("report_indexer")
        indexer = StockIndexer()
        results = indexer.search_reports(
            keyword,
            report_type=report_type if report_type else None
        )
        if not results:
            return f"索引中未找到包含「{keyword}」的报告。"
        lines = [f"🔍 索引搜索「{keyword}」({len(results)}条)", ""]
        for r in results[:15]:
            lines.append(
                f"  {r.get('code', '')} {r.get('name', '')}  "
                f"{r.get('title', '')}  {r.get('date', '')}"
            )
        if len(results) > 15:
            lines.append(f"  ... 还有 {len(results)-15} 条")
        lines.append("")
        lines.append("提示: 使用 get_company_reports 查看具体报告内容")
        return '\n'.join(lines)
    except Exception as e:
        return f"搜索失败: {str(e)}"


# ==================== 文档分析整理 ====================

@server.tool()
async def analyze_document(file_path: str, focus: str = "") -> str:
    """深度分析金融文档。自动分类（年报/研报/公告等），提取元数据（标题/机构/日期/股票代码）、
    章节结构、财务指标、风险因素、术语表，生成结构化 Markdown 报告。
    适用场景：分析单份 PDF/Word/Excel 金融文档，提取关键信息。

    Args:
        file_path: 文档完整路径
        focus: 重点关注维度（可选）：财务指标 / 风险 / 章节 / all（默认全部）
    """
    try:
        if DocumentAnalyzer is None:
            return _module_error("document_analyzer")
        analyzer = DocumentAnalyzer()
        result = analyzer.analyze(file_path)
        if result.get("error"):
            return f"❌ 分析失败: {result['error']}"

        # 根据 focus 剪裁输出
        if focus == "财务指标" or focus == "指标":
            indicators = result.get("financial_indicators", {})
            if not indicators:
                return "未提取到财务指标。"
            lines = [f"【{Path(file_path).name} 财务指标】", ""]
            for k, v in indicators.items():
                if k not in ("amounts_yi", "total_yi", "percentages"):
                    lines.append(f"  {k}: {v}")
            return '\n'.join(lines)
        elif focus == "风险":
            risks = result.get("risk_factors", [])
            if not risks:
                return "未提取到风险因素。"
            lines = [f"【{Path(file_path).name} 风险因素】({len(risks)}条)", ""]
            for i, r in enumerate(risks, 1):
                lines.append(f"  {i}. {r}")
            return '\n'.join(lines)
        elif focus == "章节":
            sections = result.get("sections", [])
            if not sections:
                return "未识别到章节结构。"
            lines = [f"【{Path(file_path).name} 章节结构】({len(sections)}个)", ""]
            for sec in sections[:25]:
                indent = "  " * (sec.get("level", 1) - 1)
                lines.append(f"{indent}{'#' * sec.get('level', 1)} {sec['title']}")
            return '\n'.join(lines)

        # 默认输出完整 Markdown
        return analyzer.to_markdown(result)
    except Exception as e:
        return f"分析失败: {str(e)}"


@server.tool()
async def organize_documents(dir_path: str) -> str:
    """批量整理文档目录。扫描指定目录下所有 PDF/Word/Excel 文件，
    逐份分析分类后按类别聚合，生成索引文件（JSON）和汇总报告（Markdown）。
    适用场景：整理一个文件夹中的研报、财报、公告等金融文档。

    Args:
        dir_path: 文档目录路径
    """
    try:
        if DocumentAnalyzer is None:
            return _module_error("document_analyzer")
        analyzer = DocumentAnalyzer()
        result = analyzer.organize_directory(dir_path)

        if result.get("error"):
            return f"❌ 整理失败: {result['error']}"

        lines = [
            f"📁 文档目录整理完成",
            f"  来源: {dir_path}",
            f"  文档总数: {result['total']}",
            f"  类别数: {len(result.get('categories', {}))}",
            "",
            "【按类别统计】",
        ]
        for cat, count in sorted(result.get("categories", {}).items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {count}份")

        lines.append("")
        lines.append(f"📄 索引文件: {result.get('index_file', '')}")
        lines.append(f"📝 汇总报告: {result.get('summary_file', '')}")

        return '\n'.join(lines)
    except Exception as e:
        return f"整理失败: {str(e)}"


@server.tool()
async def compare_documents(file_paths: str) -> str:
    """并排对比多份金融文档。提取相同维度（类型/日期/机构/关键指标等），
    高亮差异，适合对比多家公司的年报或不同券商的研报。

    Args:
        file_paths: 文档路径列表，逗号分隔，如 "report_a.pdf,report_b.pdf"
    """
    try:
        if DocumentAnalyzer is None:
            return _module_error("document_analyzer")
        paths = [p.strip() for p in file_paths.split(",") if p.strip()]
        if len(paths) < 2:
            return "请提供至少2份文档路径（逗号分隔）。"

        analyzer = DocumentAnalyzer()
        result = analyzer.compare(paths)

        lines = [
            f"📊 文档对比 ({result['compared']}份)",
            "",
            "【各文档概览】",
        ]
        for f in result.get("files", []):
            lines.append(f"  📄 {f['name']} — {f['category']} | {f['summary'][:80]}...")

        lines.append("\n【维度对比】")
        for dim, values in result.get("dimensions", {}).items():
            if dim == "关键指标":
                continue
            lines.append(f"  {dim}: {'  |  '.join(str(v) for v in values)}")

        differences = result.get("differences", [])
        if differences:
            lines.append(f"\n【⚠️ 发现 {len(differences)} 处差异】")
            for diff in differences:
                lines.append(f"  • {diff}")
        else:
            lines.append(f"\n✅ 未发现明显差异")

        # 关键指标对比
        indicators = result.get("dimensions", {}).get("关键指标", [])
        if indicators and len(indicators) >= 2:
            lines.append("\n【关键财务指标对比】")
            all_keys = set()
            for ind in indicators:
                all_keys.update(k for k in ind.keys() if k not in ("amounts_yi", "total_yi", "percentages"))
            if all_keys:
                for key in sorted(all_keys):
                    vals = [str(ind.get(key, "-")) for ind in indicators]
                    lines.append(f"  {key}: {'  |  '.join(vals)}")

        return '\n'.join(lines)
    except Exception as e:
        return f"对比失败: {str(e)}"


# ==================== 实时行情 (v3.0 新增) ====================

@server.tool()
async def get_stock_realtime(stock_codes: str) -> str:
    """获取A股实时行情。数据来源：新浪财经。
    适用场景：查询个股实时价格、涨跌幅、成交量、成交额等。

    Args:
        stock_codes: 股票代码，多个用逗号分隔，如 "600519,000858,300750"
    """
    try:
        if sina_quote is None:
            return _module_error("sina_scraper")
        codes = [c.strip() for c in stock_codes.split(",") if c.strip()]
        if not codes:
            return "请提供至少一个股票代码。"
        data = sina_quote(codes)
        if not data:
            return "未获取到行情数据，请检查股票代码是否正确。"
        lines = [f"📊 实时行情 ({len(data)}只)", ""]
        for code, info in data.items():
            lines.append(
                f"  {info.get('name', '?')} ({code})  "
                f"价格:{info.get('price', '?')}  "
                f"涨跌:{info.get('change_pct', 0):+.2f}%  "
                f"成交:{info.get('amount', 0):.0f}万"
            )
        return '\n'.join(lines)
    except Exception as e:
        return f"行情查询失败: {str(e)}"


# ==================== 基金净值历史 (v3.0 新增) ====================

@server.tool()
async def get_fund_nav_history(fund_code: str, days: int = 30) -> str:
    """获取基金历史净值数据。数据来源：天天基金。
    适用场景：查看基金近期净值走势、计算收益率。

    Args:
        fund_code: 6位基金代码，如 000001
        days: 查询天数，默认30天
    """
    try:
        url = f"https://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={fund_code}&page=1&per={min(days, 60)}"
        from http_utils import fetch_text
        text = fetch_text(url)
        if not text:
            return f"未获取到基金 {fund_code} 的净值数据。"
        import re
        records = re.findall(r'<tr[^>]*>.*?<td[^>]*>(\d{4}-\d{2}-\d{2})</td>.*?<td[^>]*class="tor[^"]*">([\d.]+)</td>.*?<td[^>]*class="tor[^"]*">([\d.]+)</td>', text, re.DOTALL)
        if not records:
            return f"未获取到基金 {fund_code} 的净值历史。"
        lines = [f"📈 基金 {fund_code} 历史净值 (近{days}天, 共{len(records)}条)", ""]
        for date, nav, acc_nav in records[:20]:
            lines.append(f"  {date}  单位净值:{nav}  累计净值:{acc_nav}")
        if len(records) > 20:
            lines.append(f"  ... 还有 {len(records)-20} 条")
        return '\n'.join(lines)
    except Exception as e:
        return f"净值查询失败: {str(e)}"


# ==================== 财联社电报 (v3.0 新增) ====================

@server.tool()
async def crawl_cls_telegraph(limit: int = 20) -> str:
    """获取财联社7x24小时电报快讯。数据来源：财联社(cls.cn)。
    适用场景：获取最新市场快讯、政策消息、公司公告速递。

    Args:
        limit: 返回条数，默认20，最多50
    """
    try:
        if cls_telegraph is None:
            return _module_error("cls_scraper")
        items = cls_telegraph(limit=min(limit, 50))
        if not items:
            return "暂无财联社电报数据。"
        lines = [f"📡 财联社7x24电报 ({len(items)}条)", ""]
        for i, item in enumerate(items, 1):
            level_icon = {"A": "🔴", "B": "🟡", "C": "🟢"}.get(item.get("level", "C"), "⚪")
            title = (item.get("title", "") or "")[:100]
            lines.append(f"  {i:>2}. {level_icon} {title}")
        return '\n'.join(lines)
    except Exception as e:
        return f"电报获取失败: {str(e)}"


# ==================== 可转债数据 (v3.0 新增) ====================

@server.tool()
async def get_convertible_bond_data(bond_code: str = "") -> str:
    """获取可转债数据（转股价/溢价率/到期收益率/评级等）。
    数据来源：集思录(jisilu.cn)。
    适用场景：可转债投资分析，筛选低溢价率标的。

    Args:
        bond_code: 可转债代码（可选，留空返回全量列表）
    """
    try:
        if jisilu_bonds is None:
            return _module_error("jisilu_scraper")
        if bond_code:
            bonds = jisilu_search(bond_code)
        else:
            bonds = jisilu_bonds(listed_only=True)
        if not bonds:
            return "未获取到可转债数据，请检查集思录是否可访问。"
        lines = [f"📊 可转债数据 ({len(bonds)}只)", ""]
        lines.append(f"  {'代码':<8} {'名称':<12} {'现价':>6} {'转股价':>6} {'溢价率':>6}")
        lines.append("  " + "-" * 50)
        for b in bonds[:20]:
            lines.append(
                f"  {b.get('bond_id', '?'):<8} {str(b.get('bond_nm', '?'))[:12]:<12} "
                f"{float(b.get('price', 0)):>6.2f} {float(b.get('convert_price', 0)):>6.2f} "
                f"{float(b.get('premium_rt', 0)):>5.1f}%"
            )
        if len(bonds) > 20:
            lines.append(f"  ... 还有 {len(bonds)-20} 只")
        return '\n'.join(lines)
    except Exception as e:
        return f"可转债查询失败: {str(e)}"


# ==================== v4.0 定期自动爬取 ====================

@server.tool()
async def schedule_crawl_task(name: str, frequency: str = "daily",
                               urls: str = "", keywords: str = "",
                               institution_type: str = "",
                               action: str = "crawl_and_compress",
                               focus: str = "全面",
                               max_runs: int = 0,
                               sentiment_targets: str = "",
                               sentiment_categories: str = "",
                               sentiment_source_categories: str = "",
                               sentiment_days: int = 7,
                               sentiment_positive_only: bool = False,
                               sentiment_negative_only: bool = False,
                               sentiment_export_format: str = "all") -> str:
    """创建定期自动爬取任务。任务将在后台按指定频率自动执行。

    支持两种模式：
      A. 常规爬取（默认值 action="crawl_and_compress"）— 同 v4.0
      B. 全网舆情爬虫 — action 传 "crawl_sentiment" 或 "crawl_sentiment_export"

    模式 B 额外参数：
        sentiment_targets: 单/多个机构（逗号分隔），如"贵州茅台,工银瑞信基金"
        sentiment_categories: 目标类别（fund_company/listed_company/...）
        sentiment_source_categories: 媒体类别（authoritative/self_media/...）
        sentiment_days: 时间窗口（天，默认7）
        sentiment_positive_only: 仅保留正面
        sentiment_negative_only: 仅保留舆情
        sentiment_export_format: 导出格式 dialog/word/excel/csv/json/all/auto

    Args:
        name: 任务名称，如"每日茅台舆情"
        frequency: 执行频率 — every_5_minutes / hourly / every_6_hours / daily / weekly / monthly / custom_cron
        urls: 目标URL列表，逗号分隔（可选）
        keywords: 搜索关键词，逗号分隔（可选）
        institution_type: 机构类型（可选）
        action: 执行动作 — crawl_only / crawl_and_compress / crawl_and_package / crawl_compress_package / crawl_sentiment / crawl_sentiment_export
        focus: 压缩关注维度 — 财务/风险/行业/政策/事件/全面
        max_runs: 最大执行次数，0表示无限
    """
    try:
        if get_scheduler is None:
            return _module_error("crawl_scheduler")
        scheduler = get_scheduler()

        url_list = [u.strip() for u in urls.split(",") if u.strip()] if urls else []
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
        inst_types = [institution_type] if institution_type else []
        st_list = [t.strip() for t in sentiment_targets.split(",") if t.strip()] if sentiment_targets else []
        sc_list = [c.strip() for c in sentiment_categories.split(",") if c.strip()] if sentiment_categories else []
        ssc_list = [c.strip() for c in sentiment_source_categories.split(",") if c.strip()] if sentiment_source_categories else []

        task = scheduler.create_task(
            name=name, frequency=frequency,
            target_urls=url_list, target_keywords=kw_list,
            target_institution_types=inst_types,
            action=action, focus_dimension=focus,
            max_runs=max_runs,
            sentiment_targets=st_list,
            sentiment_categories=sc_list,
            sentiment_source_categories=ssc_list,
            sentiment_days=sentiment_days,
            sentiment_positive_only=sentiment_positive_only,
            sentiment_negative_only=sentiment_negative_only,
            sentiment_export_format=sentiment_export_format,
        )

        if not scheduler.is_running():
            scheduler.start()

        mode_hint = ""
        if action in ("crawl_sentiment", "crawl_sentiment_export"):
            mode_hint = (f"   🆕 全网舆情模式: targets={st_list or '默认'} 类别={sc_list or '默认'} "
                         f"媒类别={ssc_list or '全部'} days={sentiment_days}\n")

        return (
            f"✅ 定时任务已创建\n"
            f"   ID: {task.task_id}\n"
            f"   名称: {task.name}\n"
            f"   频率: {task.frequency.value}\n"
            f"   动作: {task.action.value}\n"
            f"   下次执行: {task.next_run_at}\n"
            f"{mode_hint}"
            f"   \n💡 使用 list_scheduled_tasks 查看所有任务"
        )
    except Exception as e:
        return f"创建任务失败: {str(e)}"


@server.tool()
async def list_scheduled_tasks(status: str = "") -> str:
    """查看所有定期爬取任务及执行状态。

    Args:
        status: 按状态筛选 — active / paused / completed / error（留空查看全部）
    """
    try:
        if get_scheduler is None:
            return _module_error("crawl_scheduler")
        scheduler = get_scheduler()
        tasks = scheduler.list_tasks(status=status if status else None)

        if not tasks:
            return "📋 暂无定时任务。使用 schedule_crawl_task 创建新任务。"

        lines = [f"📋 定时任务列表 ({len(tasks)} 个):", ""]
        for t in tasks:
            freq_map = {
                "every_minute": "每分钟", "every_5_minutes": "每5分钟",
                "every_10_minutes": "每10分钟", "every_30_minutes": "每30分钟",
                "hourly": "每小时", "every_6_hours": "每6小时",
                "every_12_hours": "每12小时", "daily": "每天",
                "weekly": "每周", "monthly": "每月",
            }
            freq_label = freq_map.get(t.frequency.value, t.frequency.value)
            status_icon = {"active": "🟢", "paused": "🟡", "completed": "✅", "error": "🔴"}.get(t.status.value, "⚪")
            lines.append(f"  {status_icon} [{t.task_id}] {t.name}")
            lines.append(f"     频率: {freq_label} | 动作: {t.action.value} | 已执行: {t.run_count}次")
            if t.last_run_at:
                lines.append(f"     上次: {t.last_run_at}")
            if t.next_run_at:
                lines.append(f"     下次: {t.next_run_at}")
            if t.last_error:
                lines.append(f"     错误: {t.last_error[:100]}")
            lines.append("")

        lines.append(f"调度器状态: {'▶️ 运行中' if scheduler.is_running() else '⏸️ 已停止'}")
        return '\n'.join(lines)
    except Exception as e:
        return f"查询失败: {str(e)}"


@server.tool()
async def cancel_scheduled_task(task_id: str, action: str = "delete") -> str:
    """取消或暂停定期爬取任务。

    Args:
        task_id: 任务ID（从 list_scheduled_tasks 获取）
        action: 操作 — delete(删除) / pause(暂停) / resume(恢复)
    """
    try:
        if get_scheduler is None:
            return _module_error("crawl_scheduler")
        scheduler = get_scheduler()

        if action == "pause":
            ok = scheduler.pause_task(task_id)
            return f"⏸️ 任务 {task_id} 已暂停" if ok else f"❌ 未找到任务 {task_id}"
        elif action == "resume":
            ok = scheduler.resume_task(task_id)
            return f"▶️ 任务 {task_id} 已恢复" if ok else f"❌ 未找到任务 {task_id}"
        else:
            ok = scheduler.delete_task(task_id)
            return f"🗑️ 任务 {task_id} 已删除" if ok else f"❌ 未找到任务 {task_id}"
    except Exception as e:
        return f"操作失败: {str(e)}"


# ==================== v4.0 批量爬取打包 ZIP ====================

@server.tool()
async def batch_crawl_and_package(names: str = "",
                                   institution_type: str = "",
                                   zip_name: str = "") -> str:
    """批量爬取机构信息并自动打包为 ZIP 文件。

    Args:
        names: 机构名称列表，逗号分隔，如"易方达基金,华夏基金"
        institution_type: 机构类型，如"基金管理公司"（与names二选一）
        zip_name: 自定义ZIP文件名（可选）
    """
    try:
        if _batch_crawl_and_package is None:
            return _module_error("crawl_packager")
        if not names and not institution_type:
            return "请提供 names 或 institution_type 参数。"

        path = _batch_crawl_and_package(
            names=names, institution_type=institution_type, zip_name=zip_name
        )
        size_mb = os.path.getsize(path) / (1024 * 1024) if os.path.exists(path) else 0
        return f"📦 ZIP 打包完成\n   文件: {path}\n   大小: {size_mb:.2f} MB"
    except Exception as e:
        return f"打包失败: {str(e)}"


# ==================== v4.0 内容压缩 ====================

@server.tool()
async def compress_crawl_results(source: str = "",
                                  file_path: str = "",
                                  focus: str = "全面",
                                  max_pages: int = 3) -> str:
    """分析爬取内容或文件，提取关键信息并压缩为 2-3 页结构化摘要。

    适用场景：一大段爬取内容/一份PDF/一份研报 → 2-3页精华摘要。

    Args:
        source: 文本内容（直接输入）
        file_path: 文件路径（与source二选一）
        focus: 关注维度 — 财务 / 风险 / 行业 / 政策 / 事件 / 全面
        max_pages: 目标页数（默认3）
    """
    try:
        if compress_content is None:
            return _module_error("content_compressor")

        target = file_path if file_path else source
        if not target:
            return "请提供 source（文本）或 file_path（文件路径）。"

        config = CompressConfig(focus=focus, max_pages=max_pages,
                               max_chars=max_pages * 1000)
        result = compress_content(target, focus=focus)

        lines = [
            f"📄 内容压缩报告",
            f"标题: {result.title}",
            f"摘要: {result.summary[:200]}",
            f"",
            f"--- 压缩报告 ---",
            result.structured_report,
            f"",
            f"📊 压缩统计: 原文 {result.stats['source_chars']:,} 字 → "
            f"压缩后 {result.stats['output_chars']:,} 字 "
            f"({result.stats['compression_ratio']})",
        ]
        return '\n'.join(lines)
    except Exception as e:
        return f"压缩失败: {str(e)}"


# ==================== v4.0 增强文件解析 ====================

@server.tool()
async def parse_file_enhanced(file_path: str, fmt: str = "auto") -> str:
    """增强文件解析器。支持 PPT/PPTX、HTML网页、Markdown、CSV、JSON 等格式。
    自动检测文件类型，提取文本、表格、元数据等。

    适用场景：解析 PPT 演示文稿、网页内容、Markdown 文档等。

    Args:
        file_path: 文件路径或URL
        fmt: 格式 — auto(自动检测) / pptx / html / markdown / csv / json
    """
    try:
        if _parse_file_enhanced is None:
            return _module_error("enhanced_parser")
        result = _parse_file_enhanced(file_path, fmt)
        if result.get("error"):
            return f"❌ {result['error']}"

        lines = [f"✅ 解析成功: {result.get('file_type', '?').upper()}"]
        if result.get("title"):
            lines.append(f"标题: {result['title']}")
        if result.get("slide_count"):
            lines.append(f"幻灯片: {result['slide_count']} 页")
        if result.get("tables"):
            lines.append(f"表格: {len(result['tables'])} 个")
        if result.get("sections"):
            lines.append(f"章节: {len(result.get('sections', result.get('headings', [])))} 个")
        if result.get("char_count"):
            lines.append(f"字符: {result['char_count']:,}")

        text = result.get("text_content", "")[:2000]
        lines.append(f"\n--- 前2000字符 ---\n{text}")
        return '\n'.join(lines)
    except Exception as e:
        return f"解析失败: {str(e)}"


# ==================== v4.0 深度文件分析 ====================

@server.tool()
async def analyze_file_deep(file_path: str, analysis_type: str = "full") -> str:
    """深度分析文件内容。提取主题、情感倾向、趋势信号等。

    Args:
        file_path: 文件路径
        analysis_type: 分析类型 — full(全面) / topics(主题) / financial(财务) / risk(风险)
    """
    try:
        # 先解析
        if parse_file_enhanced is None:
            return _module_error("enhanced_parser")
        parsed = _parse_file_enhanced(file_path)
        if parsed.get("error"):
            return f"❌ 解析失败: {parsed['error']}"

        # 再压缩分析
        if compress_content is None:
            return _module_error("content_compressor")

        text = parsed.get("text_content", "")[:10000]
        if not text:
            return "❌ 文件内容为空"

        focus_map = {"full": "全面", "topics": "行业", "financial": "财务", "risk": "风险"}
        focus = focus_map.get(analysis_type, "全面")

        result = compress_content(text, focus=focus)

        lines = [f"🔍 深度文件分析: {Path(file_path).name}", ""]
        lines.append(f"## 文档分类")
        try:
            from document_analyzer import classify_document
            cat, conf = classify_document(text, file_path)
            lines.append(f"  {cat} (置信度: {conf}%)")
        except ImportError:
            pass

        lines.append(f"\n## 关键发现\n")
        for i, pt in enumerate(result.key_points, 1):
            lines.append(f"  {i}. {pt}")

        lines.append(f"\n## 财务指标 ({len(result.financial_highlights)} 项)")
        for k, v in list(result.financial_highlights.items())[:8]:
            lines.append(f"  {k}: {v}")

        if result.risk_summary:
            lines.append(f"\n## 风险因素 ({len(result.risk_summary)} 条)")
            for r in result.risk_summary[:5]:
                lines.append(f"  ⚠️ {r}")

        lines.append(f"\n📊 原文 {result.stats['source_chars']:,} 字 | "
                     f"压缩比 {result.stats['compression_ratio']}")
        return '\n'.join(lines)
    except Exception as e:
        return f"分析失败: {str(e)}"


# ==================== v4.0 研究报告生成 ====================

@server.tool()
async def generate_research_report(source: str = "",
                                    theme: str = "stock_research",
                                    title: str = "",
                                    focus: str = "全面",
                                    file_path: str = "",
                                    stock_code: str = "",
                                    output_formats: str = "markdown") -> str:
    """生成图文并茂的金融研究报告。支持从URL/文件/股票代码一键生成。
    自动采集数据 → 分析压缩 → 报告写作 → 图表生成 → 多格式导出。

    适用场景：生成个股研报、行业分析、基金评价、市场周报等。

    Args:
        source: 文本内容或URL（可选）
        theme: 报告主题 — stock_research(个股研报) / industry_analysis(行业分析) / fund_evaluation(基金评价) / institution_survey(机构调研) / market_weekly(市场周报) / announcement_brief(公告解读)
        title: 报告标题（可选，自动生成）
        focus: 关注维度 — 财务/风险/行业/政策/事件/全面
        file_path: 文件路径（可选，作为数据源）
        stock_code: 6位股票代码（可选，自动获取报告数据）
        output_formats: 输出格式，逗号分隔 — markdown/docx/pptx/html/pdf
    """
    try:
        if ResearchReportGenerator is None:
            return _module_error("research_report_generator")

        # 构建配置
        from research_report_generator import ReportConfig, ReportTheme, OutputFormat

        config = ReportConfig(
            theme=ReportTheme(theme),
            title=title,
            focus_dimension=focus,
        )

        if source and source.startswith(('http://', 'https://')):
            config.urls = [source]
        elif file_path and os.path.isfile(file_path):
            config.files = [file_path]
        elif stock_code:
            config.stock_codes = [stock_code]
        elif source:
            config.custom_data = {"raw_text": source}

        # 设置输出格式
        fmt_map = {"markdown": OutputFormat.MARKDOWN, "docx": OutputFormat.DOCX,
                    "pptx": OutputFormat.PPTX, "html": OutputFormat.HTML,
                    "pdf": OutputFormat.PDF}
        config.output_formats = [
            fmt_map[f.strip()] for f in output_formats.split(",")
            if f.strip() in fmt_map and f.strip() != "markdown"
        ]

        gen = ResearchReportGenerator()
        result = gen.generate(config)

        lines = [result.to_summary()]
        lines.append(f"\n--- 报告预览 (前500字) ---")
        lines.append(result.markdown_content[:500])
        if len(result.markdown_content) > 500:
            lines.append(f"\n... 全文共 {len(result.markdown_content):,} 字")
        lines.append(f"\n📊 图表: {len(result.chart_paths)} 张")

        return '\n'.join(lines)
    except Exception as e:
        return f"报告生成失败: {str(e)}"


@server.tool()
async def export_research_report(markdown_content: str = "",
                                  file_path: str = "",
                                  output_formats: str = "docx",
                                  title: str = "研究报告") -> str:
    """将 Markdown 报告内容导出为 Word/PPT/HTML/PDF 格式。

    Args:
        markdown_content: Markdown 文本内容（与file_path二选一）
        file_path: Markdown 文件路径（与markdown_content二选一）
        output_formats: 导出格式，逗号分隔 — docx/pptx/html/pdf
        title: 报告标题
    """
    try:
        if file_path and os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif markdown_content:
            content = markdown_content
        else:
            return "请提供 markdown_content 或 file_path。"

        from research_report_generator import ReportResult, ReportConfig, OutputFormat
        from datetime import datetime

        # 构造 ReportResult
        result = ReportResult(
            config=ReportConfig(),
            title=title,
            template_id="custom",
            markdown_content=content,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # 导出
        gen = ResearchReportGenerator()
        fmt_map = {"markdown": OutputFormat.MARKDOWN, "docx": OutputFormat.DOCX,
                    "pptx": OutputFormat.PPTX, "html": OutputFormat.HTML,
                    "pdf": OutputFormat.PDF}

        config = ReportConfig()
        config.output_formats = [
            fmt_map[f.strip()] for f in output_formats.split(",")
            if f.strip() in fmt_map
        ]

        output_files = gen._export(result, config)

        lines = [f"📦 报告导出结果", ""]
        for fmt, path in output_files.items():
            size = os.path.getsize(path) if os.path.exists(path) else 0
            lines.append(f"  ✅ [{fmt.upper()}] {path} ({size/1024:.1f} KB)")

        return '\n'.join(lines)
    except Exception as e:
        return f"导出失败: {str(e)}"


# ==================== v4.0 快速摘要 ====================

@server.tool()
async def quick_crawl_summary(url_or_file: str,
                               focus: str = "全面") -> str:
    """一键快速爬取+压缩。输入 URL 或文件路径，自动爬取/解析并输出 2-3 页精华摘要。

    Args:
        url_or_file: URL 或文件路径
        focus: 关注维度 — 财务/风险/行业/政策/事件/全面
    """
    try:
        if compress_content is None:
            return _module_error("content_compressor")

        # 判断是URL还是文件
        if url_or_file.startswith(('http://', 'https://')):
            # 爬取
            if FinancialPageScraper is None:
                return _module_error("scraper")
            scraper = FinancialPageScraper()
            content = scraper.scrape_url(url_or_file)
            if not content:
                return f"❌ 爬取失败: {url_or_file}"
            text = str(content)[:15000]
        elif os.path.isfile(url_or_file):
            # 解析
            if parse_file_enhanced:
                parsed = parse_file_enhanced(url_or_file)
                text = parsed.get("text_content", "")[:15000]
            else:
                with open(url_or_file, 'r', encoding='utf-8') as f:
                    text = f.read()[:15000]
        else:
            return f"❌ 无法识别来源: {url_or_file}"

        if not text:
            return "❌ 内容为空"

        result = compress_content(text, focus=focus)

        lines = [
            f"⚡ 快速摘要",
            f"来源: {url_or_file}",
            f"标题: {result.title}",
            f"",
            result.structured_report,
            f"",
            f"📊 {result.stats['source_chars']:,} 字 → "
            f"{result.stats['output_chars']:,} 字 ({result.stats['compression_ratio']})",
        ]
        return '\n'.join(lines)
    except Exception as e:
        return f"快速摘要失败: {str(e)}"


# ==================== 主入口 ====================


# ==================== v4.3 全网舆情爬虫 ====================

@server.tool()
async def crawl_global_sentiment(
    targets: str = "",
    target_categories: str = "",
    sources: str = "",
    source_categories: str = "",
    days: int = 7,
    positive_only: bool = False,
    negative_only: bool = False,
    max_articles: int = 80,
    fmt: str = "dialog",
    run_backtest: bool = True,
    dry_run: bool = False,
    strict_date: bool = True) -> str:
    """🆕 v4.6 全网舆情爬虫（正面新闻+舆情）+ 强制日期过滤 + 数据回测。

    根据用户对话要求，从权威媒体/财经垂直/地方媒体/自媒体/国际媒体
    采集基金公司/上市公司/地方政府/证券公司/银行/保险/信托等机构的
    正面新闻与舆情。

    🛡️ v4.6 增强：
      - 严格日期过滤：仅返回请求时间窗内的文章（默认启用）
      - 默认开启数据回测（4维验证：新鲜度/交叉源/历史快照/数字一致性）
      - 爬取后日期核验统计（date_validation 字段）
      - 不延展爬取范围：严格按用户指定的目标/媒体/时间窗执行

    支持：
      - 指定单个或多个机构（targets，逗号分隔），仅看正面或仅看舆情
      - 限定目标类别（fund_company / listed_company / securities 等）
      - 限定媒体类别（authoritative / financial_vertical / local_media / self_media / international）
      - 时间窗口（默认 7 天，严格过滤）
      - 多种输出方式（dialog/word/excel/csv/json/all/auto）
      - 数据回测（默认开启，对每条结果做 4 维验证）
      - 预览模式（dry_run=True 时仅展示爬取计划，不发 HTTP 请求）

    Args:
        targets: 目标名列表，逗号分隔（如"贵州茅台,工银瑞信基金,上海市金融服务办公室"）
        target_categories: 目标类别，逗号分隔（fund_company/listed_company/local_government/securities/commercial_bank/insurance/trust_company/private_fund/foreign_institution/futures/wealth_management/leasing_consumer_finance，留空=选 top 类）
        sources: 媒体名称列表（精确匹配，可选）
        source_categories: 媒体类别，逗号分隔（authoritative/financial_vertical/local_media/self_media/international）
        days: 时间窗口，默认7（严格过滤，不返回时间窗外文章）
        positive_only: 仅保留正面新闻
        negative_only: 仅保留舆情
        max_articles: 最大文章数
        fmt: 输出格式 dialog/word/excel/csv/json/all/auto
        run_backtest: 是否对每条结果做 4 维数据回测（默认开启）
        dry_run: 是否仅预览爬取计划（不发 HTTP 请求，用于爬取前确认）
        strict_date: 是否严格日期过滤（默认True，丢弃时间窗外文章）
    """
    try:
        if _crawl_sentiment is None:
            return _module_error("sentiment_crawler")
        # 解析参数
        target_list = [t.strip() for t in targets.split(",") if t.strip()] or None
        cat_list = [c.strip() for c in target_categories.split(",") if c.strip()] or None
        src_list = [s.strip() for s in sources.split(",") if s.strip()] or None
        sc_list = [c.strip() for c in source_categories.split(",") if c.strip()] or None

        snapshot = _crawl_sentiment(
            targets=target_list,
            categories=cat_list,
            sources=src_list,
            source_categories=sc_list,
            days=days,
            positive_only=positive_only,
            negative_only=negative_only,
            max_articles=max_articles,
            dry_run=dry_run,
            confirmed=not dry_run,
            run_backtest=run_backtest,
        )

        if not snapshot or not snapshot.articles:
            return (
                "📭 本次未获取到结果，建议：\n"
                "  · 放宽时间窗 days=30\n"
                "  · 添加更多 media source / target\n"
                "  · 重试或检查网络"
            )

        # 输出
        if fmt == "dialog":
            from sentiment_exporter import to_dialog
            return to_dialog(snapshot)

        if _export_sentiment is None:
            return _module_error("sentiment_exporter")
        outputs = _export_sentiment(snapshot, fmt=fmt)
        lines = [
            f"✅ 全网舆情快照 {snapshot.snapshot_id}",
            f"   共 {snapshot.stats.get('total', 0)} 条 | 正面 {snapshot.positive_count()} | "
            f"舆情 {snapshot.negative_count()} | 中性 {snapshot.neutral_count()}",
            "",
        ]
        for k, v in outputs.items():
            if k == "dialog":
                lines.append(f"--- 对话提示 ---\n{v}")
            else:
                lines.append(f"📦 [{k.upper()}] {v}")
        lines.append(f"\n💡 提示：可继续运行 export_sentiment_report 重新导出，或查看 data/sentiment_snapshots/")
        return '\n'.join(lines)
    except Exception as e:
        return f"❌ 舆情爬取失败: {str(e)}"


@server.tool()
async def export_sentiment_report(snapshot_id: str = "",
                                  file_path: str = "",
                                  fmt: str = "all") -> str:
    """🆕 v4.3 导出已有舆情快照。可直接传入快照ID或快照JSON文件路径。

    Args:
        snapshot_id: 快照ID（snapshot_id 形如 sn_xxxx），自动从 data/sentiment_snapshots/ 找到
        file_path: 快照JSON文件路径（与snapshot_id二选一）
        fmt: 输出格式 dialog/word/excel/csv/json/all/auto
    """
    try:
        if _export_sentiment is None:
            return _module_error("sentiment_exporter")

        snap_file: Optional[Path] = None
        if file_path and Path(file_path).is_file():
            snap_file = Path(file_path)
        elif snapshot_id:
            base = SCRIPT_DIR / "data" / "sentiment_snapshots"
            candidate = base / f"{snapshot_id}.json"
            if candidate.exists():
                snap_file = candidate
            else:
                index_file = base / "index.json"
                if index_file.exists():
                    for item in json.loads(index_file.read_text(encoding="utf-8")):
                        if item.get("snapshot_id") == snapshot_id:
                            snap_file = Path(item["path"])
                            break
        if not snap_file:
            return f"❌ 未找到快照: {snapshot_id or file_path}"

        # 加载快照
        from sentiment_crawler import SentimentSnapshot, SentimentArticle  # type: ignore
        raw = json.loads(snap_file.read_text(encoding="utf-8"))
        arts = [SentimentArticle(**a) for a in raw.get("articles", [])]
        snap = SentimentSnapshot(
            snapshot_id=raw["snapshot_id"], created_at=raw["created_at"],
            target_filter=raw.get("target_filter", {}),
            source_filter=raw.get("source_filter", []),
            articles=arts,
            stats=raw.get("stats", {}),
        )
        snap.extra_path = str(snap_file)  # type: ignore[attr-defined]

        outputs = _export_sentiment(snap, fmt=fmt)
        lines = []
        for k, v in outputs.items():
            if k == "dialog":
                lines.append(v)
            else:
                lines.append(f"📦 [{k.upper()}] {v}")
        return '\n'.join(lines) if lines else "无输出"
    except Exception as e:
        return f"❌ 导出失败: {str(e)}"


@server.tool()
async def list_sentiment_targets() -> str:
    """🆕 v4.3 查看全网舆情爬虫的目标库。
    返回的分类：fund_company / listed_company / local_government / securities /
                commercial_bank / insurance / trust_company / private_fund /
                foreign_institution / futures / wealth_management / leasing_consumer_finance
    """
    try:
        if _list_sentiment_targets is None:
            return _module_error("sentiment_crawler")
        items = _list_sentiment_targets()
        lines = ["🎯 全网舆情目标库", ""]
        for it in items:
            lines.append(f"  · {it.get('category','')} — {it.get('label','')} ({it.get('count',0)} 个)")
        lines.append("")
        lines.append("💡 用法：\n  · crawl_global_sentiment(targets='工银瑞信基金,贵州茅台')\n"
                     "  · crawl_global_sentiment(target_categories='fund_company,listed_company')")
        return '\n'.join(lines)
    except Exception as e:
        return f"查询失败: {str(e)}"


@server.tool()
async def list_sentiment_sources(category: str = "") -> str:
    """🆕 v4.3 查看全网舆情爬虫的媒体源库。

    Args:
        category: 媒体类别（authoritative/financial_vertical/local_media/self_media/international），留空=全部
    """
    try:
        if SentimentSourceLoader is None:
            return _module_error("sentiment_crawler")
        loader = SentimentSourceLoader()
        if category:
            items = loader.sources_by_category(category)
            items = [(category, x) for x in items]
        else:
            items = [(loader._data[k][0].get('category', k) if loader._data.get(k) else k, x)
                     for k in loader.list_categories()
                     for x in loader.sources_by_category(k)]
        lines = [f"📰 全网舆情媒体源 (类别: {category or '全部'})", ""]
        for cat, item in items:
            tags = ",".join(item.get("tags", []) or [])
            lines.append(f"  · [{cat}] {item.get('name','')} — {tags}")
        return '\n'.join(lines)
    except Exception as e:
        return f"查询失败: {str(e)}"


@server.tool()
async def add_sentiment_target(category: str, name: str, aliases: str = "") -> str:
    """🆕 v4.3 新增自定义舆情目标。

    Args:
        category: 目标类别（fund_company / listed_company / local_government / securities / commercial_bank / insurance / trust_company / private_fund / foreign_institution / futures / wealth_management / leasing_consumer_finance / custom）
        name: 目标名称
        aliases: 别名列表（逗号分隔，可选）
    """
    try:
        if _add_custom_target is None:
            return _module_error("sentiment_crawler")
        alias_list = [a.strip() for a in aliases.split(",") if a.strip()] or None
        result = _add_custom_target(category, name, alias_list)
        if result.get("ok"):
            return f"✅ 已新增 {category} - {name}（含 {len(alias_list or [])} 个别名）"
        return f"⚠️ {result.get('msg', '未知错误')}"
    except Exception as e:
        return f"❌ 新增失败: {str(e)}"


# ==================== v4.5 全页归档 + 搜索工具 ====================

try:
    from scripts.fullpage_archiver import FullPageArchiver as _FullPageArchiver, \
        quick_archive as _quick_archive
    _HAS_ARCHIVER = True
except ImportError:
    _HAS_ARCHIVER = False

try:
    from scripts.search_engine import MultiEngineSearch as _MultiEngineSearch, \
        search_and_fetch as _search_and_fetch
    _HAS_SEARCH = True
except ImportError:
    _HAS_SEARCH = False


@server.tool()
async def archive_webpage(url: str, paginate: bool = False,
                          next_selector: str = "",
                          max_pages: int = 5,
                          output_mode: str = "both") -> str:
    """v4.5 全页归档：下载网页全部内容（文字+图片+图表+表格），生成自包含 HTML。

    支持翻页抓取、图片 base64 内嵌、Canvas 截图、表格提取。
    输出模式: "inline"(单文件内嵌) / "directory"(独立目录) / "both"(两者都要，默认)

    Args:
        url: 目标网页 URL
        paginate: 是否自动翻页
        next_selector: 下一页按钮 CSS 选择器（翻页时必填，如 ".next,a[rel=next]"）
        max_pages: 最大翻页数（默认 5）
        output_mode: 输出模式（默认 both）
    """
    if not _HAS_ARCHIVER:
        return _module_error("fullpage_archiver")
    try:
        result = _quick_archive(
            url, paginate=paginate,
            next_selector=next_selector or None,
            max_pages=max_pages,
            inline_images=output_mode in ("inline", "both"),
            save_assets=output_mode in ("directory", "both"),
        )
        return result.summary
    except Exception as e:
        return f"❌ 归档失败: {str(e)}"


@server.tool()
async def search_web(query: str, engines: str = "",
                     limit: int = 10) -> str:
    """v4.5 多引擎搜索：跨 DuckDuckGo/Bing/SearXNG 搜索，返回结构化结果。

    零 API Key 即可使用（优先 DuckDuckGo + SearXNG，Bing HTML 兜底）。

    Args:
        query: 搜索关键词（如 "贵州茅台 2026年报"）
        engines: 指定引擎（逗号分隔，如 "duckduckgo,bing_html"），空=自动选择
        limit: 返回条数（默认 10）
    """
    if not _HAS_SEARCH:
        return _module_error("search_engine")
    try:
        engine_list = [e.strip() for e in engines.split(",") if e.strip()] or None
        s = _MultiEngineSearch(engines=engine_list)
        results = s.search(query, limit=limit)
        if not results:
            return "🔍 未找到相关结果。可尝试换关键词或稍后重试。"
        lines = [f"🔍 搜索: {query} | 共 {len(results)} 条"]
        for i, r in enumerate(results, 1):
            lines.append(
                f"{i}. [{r.source_engine}] {r.title[:80]}\n"
                f"   {r.url[:100]}\n"
                f"   {r.snippet[:120]}"
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


@server.tool()
async def search_and_archive(query: str, engines: str = "",
                             limit: int = 5,
                             fetch_content: bool = True) -> str:
    """v4.5 搜索+归档一步完成：搜索 → 获取 URL → 爬取详情 → 返回结构化内容。

    Args:
        query: 搜索关键词
        engines: 指定引擎（逗号分隔），空=自动选择
        limit: 结果条数（默认 5）
        fetch_content: 是否自动爬取详情页文本（默认 True）
    """
    if not _HAS_SEARCH:
        return _module_error("search_engine")
    try:
        results = _search_and_fetch(query, limit=limit, fetch_content=fetch_content)
        if not results:
            return "🔍 未找到相关结果。"
        lines = [f"🔍 搜索+归档: {query} | 共 {len(results)} 条"]
        for i, r in enumerate(results, 1):
            content_preview = (r.get("content", "") or "")[:200]
            lines.append(
                f"{i}. {r['title'][:80]}\n"
                f"   来源: {r.get('source_engine', '?')} | "
                f"可信度: {r.get('credibility', '?')}/10\n"
                f"   URL: {r['url'][:100]}\n"
                f"   摘要: {r.get('snippet', '')[:120]}\n"
                f"   正文: {content_preview}..."
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"❌ 搜索归档失败: {str(e)}"


# ==================== 主入口 ====================

def main():
    """MCP Server 入口 — 走 stdio 协议"""
    server.run(transport="stdio")


if __name__ == '__main__':
    main()
