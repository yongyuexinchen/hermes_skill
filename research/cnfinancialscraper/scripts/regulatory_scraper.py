# -*- coding: utf-8 -*-
"""
中国金融监管机构爬虫 v1.0 (regulatory_scraper.py)

覆盖三大中国金融监管机构：
  1. 中国人民银行 (PBOC) — pbc.gov.cn
  2. 中国证监会 (CSRC) — csrc.gov.cn
  3. 国家金融监督管理总局 (NFRA, 原 CBIRC) — cbirc.gov.cn

提取：政策公告、行政处罚、统计信息、新闻动态。

用法：
  from regulatory_scraper import RegulatoryScraper, get_regulatory_updates
  scraper = RegulatoryScraper()
  news = scraper.get_pboc_news(limit=10)
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from bs4 import BeautifulSoup  # type: ignore
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from .http_utils import get_session
    HAS_HTTP_UTILS = True
except ImportError:
    try:
        from http_utils import get_session
        HAS_HTTP_UTILS = True
    except ImportError:
        HAS_HTTP_UTILS = False

logger = logging.getLogger("regulatory_scraper")


class RegulatoryScraper:
    """中国金融监管机构爬虫 — PBOC/CSRC/NFRA"""

    def __init__(self):
        self.session = None
        self._init_session()

    def _init_session(self):
        """初始化请求会话"""
        if HAS_HTTP_UTILS:
            try:
                self.session = get_session()
            except Exception:
                pass
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            })

    def _fetch_html(self, url: str, timeout: int = 30) -> Optional[str]:
        """获取 HTML 页面内容，自动检测编码"""
        try:
            resp = self.session.get(url, timeout=timeout)
            # 兼容 requests 和 stdlib response 的编码处理
            if hasattr(resp, 'apparent_encoding'):
                resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
            elif hasattr(resp, 'encoding') and resp.encoding:
                try:
                    resp.encoding = resp.encoding
                except Exception:
                    pass  # stdlib response 可能不支持设置 encoding
            return resp.text if hasattr(resp, 'text') else resp.content.decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"获取页面失败: {url}, {e}")
            return None

    def _parse_html_links(self, html: str, base_url: str,
                          list_selector: str = "a") -> List[Dict[str, str]]:
        """从 HTML 中提取链接列表"""
        if not html or not HAS_BS4:
            return []
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for link in soup.select(list_selector):
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title or len(title) < 4:
                continue
            if href and not href.startswith("http"):
                if href.startswith("/"):
                    href = base_url.rstrip("/") + href
                elif href.startswith("./"):
                    href = base_url.rstrip("/") + href[1:]
                else:
                    href = base_url.rstrip("/") + "/" + href
            date_str = ""
            results.append({"title": title, "url": href, "date": date_str})
        return results

    # ==================== PBOC 中国人民银行 ====================

    def get_pboc_news(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取央行最新新闻/政策公告。
        抓取 pbc.gov.cn 沟通交流栏目。"""
        results = []
        url = "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html"
        html = self._fetch_html(url)
        if not html:
            return results
        if HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("td a, .newslist a, .list a"):
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if title and len(title) > 5:
                    full_url = href
                    if full_url and not full_url.startswith("http"):
                        full_url = "http://www.pbc.gov.cn" + href
                    results.append({
                        "title": title,
                        "url": full_url,
                        "source": "中国人民银行",
                        "date": "",
                    })
                    if len(results) >= limit:
                        break
        # 正则 fallback
        if not results:
            pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]{5,})</a>'
            for m in re.finditer(pattern, html):
                href = m.group(1)
                title = m.group(2).strip()
                full_url = href if href.startswith("http") else "http://www.pbc.gov.cn" + href
                results.append({"title": title, "url": full_url, "source": "中国人民银行", "date": ""})
                if len(results) >= limit:
                    break
        return results[:limit]

    def get_pboc_monetary_policy(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取央行货币政策（利率、存款准备金率、公开市场操作）。"""
        results = []
        url = "http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/index.html"
        html = self._fetch_html(url)
        if not html:
            return results
        if HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("td a, .list a"):
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if title and len(title) > 5:
                    full_url = href if href.startswith("http") else "http://www.pbc.gov.cn" + href
                    results.append({
                        "title": title, "url": full_url,
                        "source": "中国人民银行-货币政策", "date": "",
                    })
                    if len(results) >= limit:
                        break
        return results[:limit]

    def get_pboc_open_market(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取公开市场操作信息。"""
        results = []
        url = "http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/index.html"
        html = self._fetch_html(url)
        if not html:
            return results
        if HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("td a, .list a"):
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if title and len(title) > 5:
                    full_url = href if href.startswith("http") else "http://www.pbc.gov.cn" + href
                    results.append({
                        "title": title, "url": full_url,
                        "source": "中国人民银行-公开市场操作", "date": "",
                    })
                    if len(results) >= limit:
                        break
        return results[:limit]

    # ==================== CSRC 中国证监会 ====================

    def get_csrc_announcements(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取证监会公告（IPO审核、行政处罚、监管措施等）。"""
        results = []
        url = "http://www.csrc.gov.cn/csrc/c100028/common_list.shtml"
        html = self._fetch_html(url)
        if not html:
            return results
        if HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("ul li a, .list a, td a"):
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if title and len(title) > 5:
                    full_url = href
                    if full_url and not full_url.startswith("http"):
                        if href.startswith("/"):
                            full_url = "http://www.csrc.gov.cn" + href
                        else:
                            full_url = "http://www.csrc.gov.cn/csrc/c100028/" + href
                    results.append({
                        "title": title, "url": full_url,
                        "source": "中国证监会", "date": "",
                    })
                    if len(results) >= limit:
                        break
        return results[:limit]

    # ==================== NFRA 国家金融监督管理总局 ====================

    def get_nfra_news(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取国家金融监督管理总局最新新闻/政策。"""
        results = []
        url = "https://www.cbirc.gov.cn/cn/view/pages/index/index.html"
        html = self._fetch_html(url)
        if not html:
            return results
        if HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("a[href]"):
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if title and len(title) > 5 and "cbirc" in href.lower() or "nfra" in href.lower():
                    full_url = href if href.startswith("http") else "https://www.cbirc.gov.cn" + href
                    results.append({
                        "title": title, "url": full_url,
                        "source": "国家金融监督管理总局", "date": "",
                    })
                    if len(results) >= limit:
                        break
        # 正则 fallback
        if not results:
            for pattern in [
                r'<a[^>]*href="([^"]+)"[^>]*>([^<]{5,})</a>',
            ]:
                for m in re.finditer(pattern, html[:50000]):
                    results.append({
                        "title": m.group(2).strip(),
                        "url": m.group(1),
                        "source": "国家金融监督管理总局",
                        "date": "",
                    })
                    if len(results) >= limit:
                        break
        return results[:limit]

    # ==================== 跨机构搜索 ====================

    def search_all(self, keyword: str, limit: int = 30) -> List[Dict[str, str]]:
        """跨 PBOC / CSRC / NFRA 搜索关键词。"""
        results = []
        for source, func in [
            ("PBOC", self.get_pboc_news),
            ("CSRC", self.get_csrc_announcements),
            ("NFRA", self.get_nfra_news),
        ]:
            try:
                items = func(limit=limit)
                for item in items:
                    if keyword.lower() in item.get("title", "").lower():
                        item["source"] = f"{source} - {item.get('source', source)}"
                        results.append(item)
            except Exception as e:
                logger.warning(f"{source} 搜索失败: {e}")
        return results[:limit]


# ==================== 便捷函数 ====================

def get_regulatory_updates(agency: str = "all", limit: int = 20) -> List[Dict[str, str]]:
    """获取监管机构最新动态。

    Args:
        agency: all / pboc / csrc / nfra
        limit: 返回条数
    """
    scraper = RegulatoryScraper()
    if agency == "pboc":
        return scraper.get_pboc_news(limit)
    elif agency == "csrc":
        return scraper.get_csrc_announcements(limit)
    elif agency == "nfra":
        return scraper.get_nfra_news(limit)
    else:
        results = []
        results.extend(scraper.get_pboc_news(max(limit // 3, 5)))
        results.extend(scraper.get_csrc_announcements(max(limit // 3, 5)))
        results.extend(scraper.get_nfra_news(max(limit // 3, 5)))
        return results[:limit]


def get_monetary_policy() -> Dict[str, Any]:
    """获取最新货币政策摘要（LPR、RRR、公开市场操作）。"""
    scraper = RegulatoryScraper()
    policy_news = scraper.get_pboc_monetary_policy(limit=5)
    omo_news = scraper.get_pboc_open_market(limit=5)
    return {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "monetary_policy_count": len(policy_news),
        "monetary_policy": policy_news,
        "open_market_operations_count": len(omo_news),
        "open_market_operations": omo_news,
    }


# ==================== 自测入口 ====================

if __name__ == "__main__":
    print("=== 中国金融监管机构爬虫 v1.0 自测 ===\n")

    scraper = RegulatoryScraper()

    print("[PBOC] 央行最新新闻:")
    for i, item in enumerate(scraper.get_pboc_news(limit=5), 1):
        print(f"  {i}. {item['title'][:60]}")
        print(f"     {item['url']}")

    print("\n[CSRC] 证监会最新公告:")
    for i, item in enumerate(scraper.get_csrc_announcements(limit=5), 1):
        print(f"  {i}. {item['title'][:60]}")
        print(f"     {item['url']}")

    print("\n[NFRA] 金监总局最新新闻:")
    for i, item in enumerate(scraper.get_nfra_news(limit=5), 1):
        print(f"  {i}. {item['title'][:60]}")
        print(f"     {item['url']}")

    print("\n=== 自测完成 ===")
