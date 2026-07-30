# -*- coding: utf-8 -*-
"""
东方财富数据爬虫 v1.0

提供基金净值、股票实时行情、热门股票排行、北向资金流向、龙虎榜、板块资金流向等。
数据源: eastmoney.com（中国最大的金融数据平台）

API 一览:
    - 基金净值:  https://api.fund.eastmoney.com/f10/lsjz
    - 股票行情:  https://push2.eastmoney.com/api/qt/stock/get
    - 热门排行:  https://push2.eastmoney.com/api/qt/clist/get
    - 北向资金:  https://push2.eastmoney.com/api/qt/kamt.kline/get
    - 龙虎榜:    https://push2.eastmoney.com/api/qt/clist/get (龙虎榜筛选)
    - 板块资金:  https://push2.eastmoney.com/api/qt/slist/get

注意:
    - 东方财富有频率限制，建议请求间隔 >= 1 秒（http_utils 自动按域名限流）
    - 部分接口返回 JSONP 格式，模块内部自动剥离回调包装
    - 股票代码自动转换 secid 格式（SH→1, SZ→0, BJ→0）
"""

import json
import re
import logging
import time
from typing import Dict, List, Optional, Any

# ── 优先使用 requests，不可用时回退到 http_utils ────────────────────────────
try:
    import requests as _requests

    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    try:
        from .http_utils import http_get, http_get_json, rate_limit, get_session
    except ImportError:
        from http_utils import http_get, http_get_json, rate_limit, get_session  # type: ignore

log = logging.getLogger(__name__)

# ==================== 常量 ====================

EASTMONEY_PUSH_API = "https://push2.eastmoney.com/api/qt"
EASTMONEY_FUND_API = "https://api.fund.eastmoney.com/f10"
EASTMONEY_DATA_URL = "https://data.eastmoney.com"

# ── 默认请求头（模拟浏览器访问东方财富页面） ──
EM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# ── Referer 映射（不同页面来源对应不同 Referer） ──
EM_REFERERS = {
    "fund": "https://fund.eastmoney.com/",
    "stock": "https://quote.eastmoney.com/",
    "data": "https://data.eastmoney.com/",
    "default": "https://www.eastmoney.com/",
}

# ── 股票行情字段（fields 参数，覆盖常用数据点） ──
STOCK_QUOTE_FIELDS = ",".join([
    "f2",   # 最新价
    "f3",   # 涨跌幅
    "f4",   # 涨跌额
    "f5",   # 成交量(手)
    "f6",   # 成交额
    "f7",   # 振幅
    "f8",   # 换手率
    "f9",   # 市盈率(动态)
    "f10",  # 量比
    "f11",  # 5分钟涨跌
    "f12",  # 股票代码
    "f14",  # 股票名称
    "f15",  # 最高
    "f16",  # 最低
    "f17",  # 今开
    "f18",  # 昨收
    "f20",  # 总市值
    "f21",  # 流通市值
    "f22",  # 涨速
    "f23",  # 市净率
    "f24",  # 60日涨跌幅
    "f25",  # 5日涨跌幅
    "f26",  # 上市日期
    "f37",  # 加权量
    "f38",  # 总股本
    "f39",  # 流通股
    "f40",  # 主营业务
    "f41",  # 所属行业
    "f43",  # 振幅
    "f45",  # 动态市盈率(动)
    "f46",  # 静态市盈率
    "f47",  # 涨停
    "f48",  # 跌停
    "f49",  # 流通市值(亿元)
    "f50",  # 量比
    "f51",  # 涨停
    "f52",  # 跌停
    "f57",  # 代码
    "f58",  # 名称
    "f60",  # 年初至今涨跌幅
    "f100", # 所属行业
    "f115", # 市盈率(静态)
    "f116", # 总市值(亿元)
    "f117", # 流通市值(亿元)
    "f162", # 市盈率(动态)
    "f167", # 市净率
    "f168", # 换手率
    "f169", # 涨跌幅
    "f170", # 涨跌额
    "f171", # 涨速
    "f269", # 板块代码
    "f270", # 板块名称
])

# ── 热门排行字段 ──
RANK_FIELDS = ",".join([
    "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10",
    "f12", "f14", "f15", "f16", "f17", "f18", "f20", "f21",
    "f23", "f37", "f62", "f124", "f184",
])

# ── 龙虎榜字段 ──
DRAGON_TIGER_FIELDS = ",".join([
    "f12",  # 股票代码
    "f14",  # 股票名称
    "f2",   # 收盘价
    "f3",   # 涨跌幅
    "f62",  # 主力净流入
    "f184", # 主力净流入占比
    "f66",  # 超大单净流入
    "f69",  # 超大单净流入占比
    "f72",  # 大单净流入
    "f75",  # 大单净流入占比
    "f78",  # 中单净流入
    "f81",  # 中单净流入占比
    "f84",  # 小单净流入
    "f87",  # 小单净流入占比
    "f124", # 更新时间
    "f3",   # 涨跌幅
])

# ==================== 工具函数 ====================


def _safe_float(val, default=0.0):
    """安全转换为浮点数，处理 None 和 "-" 等非数字值"""
    if val is None:
        return default
    if isinstance(val, str) and val.strip() in ("-", "--", "", "—"):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    """安全转换为整数"""
    if val is None:
        return default
    if isinstance(val, str) and val.strip() in ("-", "--", "", "—"):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    """安全转换为字符串"""
    if val is None:
        return default
    return str(val)


def _strip_jsonp(text: str) -> str:
    """剥离 JSONP 回调包装，提取纯 JSON 字符串。

    东方财富部分接口（如基金净值）返回格式:
        jQuery1234567890_1234567890123({"Data":...})
    本函数去除外层函数调用，返回花括号内的纯 JSON。
    """
    if not text:
        return text
    text = text.strip()
    # 移除外层函数调用: funcName(json)
    m = re.match(r'^\s*[\w$.]+\s*\(\s*(\{.*\})\s*\)\s*;?\s*$', text, re.DOTALL)
    if m:
        return m.group(1)
    # 另一种格式: funcName({...});
    m = re.match(r'^\s*[\w$.]+\s*\(\s*(\[.*\])\s*\)\s*;?\s*$', text, re.DOTALL)
    if m:
        return m.group(1)
    return text


def _to_secid(stock_code: str) -> str:
    """将 A 股代码转换为东方财富 secid 格式。

    规则:
        - 6 开头 → 上海主板 → 1.{code}
        - 3 开头 → 深圳创业板 → 0.{code}
        - 0 开头 → 深圳主板 → 0.{code}
        - 8 开头 → 北交所 → 0.{code}
        - 4 开头 → 北交所 → 0.{code}
        - 5 开头 → 上海(基金等) → 1.{code}
        - 9 开头 → 上海 B 股 → 1.{code}
        - 2 开头 → 深圳 B 股 → 0.{code}

    如果已包含 "." 分隔符则直接返回。
    """
    code = str(stock_code).strip().replace(" ", "")
    if "." in code:
        return code

    first = code[0] if code else ""

    if first == "6":
        return f"1.{code}"
    elif first == "5":
        return f"1.{code}"  # 上海基金/ETF
    elif first == "9":
        return f"1.{code}"  # 上海B股
    elif first == "4":
        return f"0.{code}"  # 北交所
    elif first == "8":
        return f"0.{code}"  # 北交所
    else:
        # 0/2/3 开头 → 深圳
        return f"0.{code}"


# ==================== 底层请求封装 ====================


def _em_json_get(url: str,
                 params: Optional[Dict[str, str]] = None,
                 referer: str = "",
                 timeout: int = 20,
                 raw_text: bool = False) -> Optional[Dict]:
    """东方财富通用 JSON GET 请求。

    自动设置 Referer，处理 JSONP 回调格式。
    优先使用 requests 库，不可用时回退到 http_utils。

    Args:
        url: API 地址
        params: 查询参数
        referer: Referer 键名（对应 EM_REFERERS 中的 key）或完整 Referer URL
        timeout: 超时秒数
        raw_text: 返回原始文本而非解析后的 dict

    Returns:
        解析后的 dict，失败返回 None
    """
    # 确定 Referer header
    ref_url = EM_REFERERS.get(referer, referer) if referer else EM_REFERERS["default"]
    if not ref_url.startswith("http"):
        ref_url = EM_REFERERS.get("default")

    headers = {
        **EM_HEADERS,
        "Referer": ref_url,
    }

    if _HAS_REQUESTS:
        try:
            resp = _requests.get(url, params=params, headers=headers,
                                timeout=timeout)
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            log.error(f"东方财富 API 请求失败: {url[:100]} — {e}")
            return None
    else:
        # 回退到 http_utils（标准库）
        try:
            from .http_utils import http_get, rate_limit
        except ImportError:
            from http_utils import http_get, rate_limit  # type: ignore
        rate_limit(url=url)
        resp = http_get(url, headers=headers, timeout=timeout)
        if resp is None:
            log.error(f"东方财富 API 请求失败: {url[:100]}")
            return None
        text = resp.text

    if raw_text:
        return {"_raw": text}  # 返回原始文本的包装

    # 尝试解析 JSON（处理可能的 JSONP 包装）
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # JSONP 格式: jQuery...({...});
    cleaned = _strip_jsonp(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning(f"东方财富 API JSON 解析失败: {text[:200]}")
        return None


# ==================== 基金净值 ====================


def get_fund_nav(fund_code: str, limit: int = 30) -> List[Dict]:
    """获取基金历史净值（单位净值 & 累计净值）。

    数据来源:
        https://api.fund.eastmoney.com/f10/lsjz
        对应页面: https://fund.eastmoney.com/f10/jjjz_{fund_code}.html

    Args:
        fund_code: 基金代码，6 位数字，如 "000001"（华夏成长混合）
        limit: 返回最近 N 条记录，默认 30，最大 100

    Returns:
        [
            {
                "date": "2024-01-15",        # 净值日期
                "nav": 1.2345,                # 单位净值
                "acc_nav": 2.4567,            # 累计净值
                "daily_return": 0.56,         # 日涨跌幅(%)
                "subscribe_status": "开放",   # 申购状态
                "redeem_status": "开放",      # 赎回状态
                "dividend": "",               # 分红方案
            },
            ...
        ]
        网络错误或基金不存在时返回空列表。
    """
    url = f"{EASTMONEY_FUND_API}/lsjz"
    params = {
        "fundCode": str(fund_code).zfill(6),
        "pageIndex": "1",
        "pageSize": str(min(limit, 100)),
        "startDate": "",
        "endDate": "",
    }

    data = _em_json_get(url, params=params, referer="fund")
    if data is None:
        return []

    # 东方财富基金 API 返回结构: { Data: { LSJZList: [...], ... }, ... }
    records = []
    try:
        data_block = data.get("Data", {})
        lsjz_list = data_block.get("LSJZList", []) if isinstance(data_block, dict) else []

        for item in lsjz_list:
            records.append({
                "date": _safe_str(item.get("FSRQ", ""), ""),
                "nav": _safe_float(item.get("DWJZ", ""), 0.0),
                "acc_nav": _safe_float(item.get("LJJZ", ""), 0.0),
                "daily_return": _safe_float(item.get("JZZZL", ""), 0.0),
                "subscribe_status": _safe_str(item.get("SGBZ", ""), ""),
                "redeem_status": _safe_str(item.get("SHBZ", ""), ""),
                "dividend": _safe_str(item.get("FHFCBZ", ""), ""),
            })
    except Exception as e:
        log.error(f"解析基金净值数据失败: {e}")
        return []

    log.info(f"获取基金 {fund_code} 最近 {len(records)} 条净值记录")
    return records


# ==================== 股票实时行情 ====================


def get_stock_quote(stock_code: str) -> Dict:
    """获取股票实时行情。

    数据来源:
        https://push2.eastmoney.com/api/qt/stock/get
        对应页面: https://quote.eastmoney.com/{code}.html

    Args:
        stock_code: 股票代码，6 位数字，如 "600519"（贵州茅台）
                    支持格式: "sh600519", "600519", "1.600519"

    Returns:
        {
            "code": "600519",               # 股票代码
            "name": "贵州茅台",              # 股票名称
            "price": 1650.00,               # 最新价
            "change": 15.50,                # 涨跌额
            "change_pct": 0.95,             # 涨跌幅(%)
            "open": 1640.00,                # 今开
            "high": 1660.00,                # 最高
            "low": 1635.00,                 # 最低
            "pre_close": 1634.50,           # 昨收
            "volume": 2345600,              # 成交量(手)
            "amount": 38.7,                 # 成交额(亿元)
            "turnover": 0.42,               # 换手率(%)
            "pe": 32.5,                     # 市盈率(动态)
            "pb": 8.2,                      # 市净率
            "total_mv": 20800,              # 总市值(亿元)
            "circ_mv": 20800,               # 流通市值(亿元)
            "amplitude": 1.53,              # 振幅(%)
            "volume_ratio": 1.05,           # 量比
            "limit_up": 1797.95,            # 涨停价
            "limit_down": 1471.05,          # 跌停价
            "update_time": "2024-01-15 11:30:00",
        }
        请求失败或股票不存在时返回包含 "error" 键的 dict。
    """
    # 处理 "sh600519" 格式
    stock_code = str(stock_code).strip()
    if stock_code.lower().startswith("sh"):
        stock_code = "1." + stock_code[2:]
    elif stock_code.lower().startswith("sz"):
        stock_code = "0." + stock_code[2:]
    elif stock_code.lower().startswith("bj"):
        stock_code = "0." + stock_code[2:]

    secid = _to_secid(stock_code)

    url = f"{EASTMONEY_PUSH_API}/stock/get"
    params = {
        "secid": secid,
        "fields": STOCK_QUOTE_FIELDS,
    }

    data = _em_json_get(url, params=params, referer="stock")
    if data is None:
        return {"error": "请求失败", "code": stock_code}

    try:
        item = data.get("data", {}) if isinstance(data, dict) else {}
        if not item:
            return {"error": "股票不存在或无数据", "code": stock_code}

        return {
            "code": _safe_str(item.get("f57", item.get("f12", ""))),
            "name": _safe_str(item.get("f58", item.get("f14", ""))),
            "price": _safe_float(item.get("f2", 0)),
            "change": _safe_float(item.get("f4", 0)),
            "change_pct": _safe_float(item.get("f3", 0)),
            "open": _safe_float(item.get("f17", 0)),
            "high": _safe_float(item.get("f15", 0)),
            "low": _safe_float(item.get("f16", 0)),
            "pre_close": _safe_float(item.get("f18", 0)),
            "volume": _safe_int(item.get("f5", 0)),
            "amount": round(_safe_float(item.get("f6", 0)) / 1e8, 2),  # 元→亿元
            "turnover": _safe_float(item.get("f168", item.get("f8", 0))),
            "pe": _safe_float(item.get("f162", item.get("f9", 0))),
            "pb": _safe_float(item.get("f167", item.get("f23", 0))),
            "total_mv": round(_safe_float(item.get("f20", 0)) / 1e8, 2),
            "circ_mv": round(_safe_float(item.get("f21", 0)) / 1e8, 2),
            "amplitude": _safe_float(item.get("f7", 0)),
            "volume_ratio": _safe_float(item.get("f50", item.get("f10", 0))),
            "limit_up": _safe_float(item.get("f47", item.get("f51", 0))),
            "limit_down": _safe_float(item.get("f48", item.get("f52", 0))),
            "industry": _safe_str(item.get("f100", "")),
            "update_time": str(item.get("f124", "")),
        }
    except Exception as e:
        log.error(f"解析股票行情数据失败: {e}")
        return {"error": f"解析失败: {e}", "code": stock_code}


# ==================== 热门股票排行 ====================


def get_hot_stocks(rank_type: str = "volume", limit: int = 20) -> List[Dict]:
    """获取热门股票排行。

    数据来源:
        https://push2.eastmoney.com/api/qt/clist/get
        对应页面: https://quote.eastmoney.com/center/board/rank.html

    Args:
        rank_type: 排行类型，可选:
            - "volume"  : 成交量排行（默认）
            - "rise"    : 涨幅排行
            - "fall"    : 跌幅排行
            - "amount"  : 成交额排行
            - "turnover": 换手率排行
            - "speed"   : 涨速排行
        limit: 返回条数，默认 20，最大 100

    Returns:
        [
            {
                "code": "601398",        # 股票代码
                "name": "工商银行",       # 股票名称
                "price": 5.68,           # 最新价
                "change_pct": -0.35,     # 涨跌幅(%)
                "volume": 456780000,     # 成交量(手)
                "amount": 25.94,         # 成交额(亿元)
                "turnover": 0.12,        # 换手率(%)
                "pe": 6.8,               # 市盈率
                "rank": 1,               # 排名
            },
            ...
        ]
    """
    # 排行类型→排序字段映射
    rank_config = {
        "volume":   {"fid": "f5",  "po": "1", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"},
        "rise":     {"fid": "f3",  "po": "1", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"},
        "fall":     {"fid": "f3",  "po": "0", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"},
        "amount":   {"fid": "f6",  "po": "1", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"},
        "turnover": {"fid": "f8",  "po": "1", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"},
        "speed":    {"fid": "f22", "po": "1", "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"},
    }

    cfg = rank_config.get(rank_type, rank_config["volume"])

    url = f"{EASTMONEY_PUSH_API}/clist/get"
    params = {
        "pn": "1",
        "pz": str(min(limit, 100)),
        "po": cfg["po"],
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fid": cfg["fid"],
        "fs": cfg["fs"],
        "fields": RANK_FIELDS,
    }

    data = _em_json_get(url, params=params, referer="stock")
    if data is None:
        return []

    results = []
    try:
        items = data.get("data", {}).get("diff", []) if isinstance(data, dict) else []
        if not items and isinstance(data.get("data"), list):
            items = data["data"]

        for idx, item in enumerate(items, 1):
            results.append({
                "code": _safe_str(item.get("f12", "")),
                "name": _safe_str(item.get("f14", "")),
                "price": _safe_float(item.get("f2", 0)),
                "change_pct": _safe_float(item.get("f3", 0)),
                "change": _safe_float(item.get("f4", 0)),
                "volume": _safe_int(item.get("f5", 0)),
                "amount": round(_safe_float(item.get("f6", 0)) / 1e8, 2),
                "turnover": _safe_float(item.get("f8", 0)),
                "pe": _safe_float(item.get("f9", 0)),
                "total_mv": round(_safe_float(item.get("f20", 0)) / 1e8, 2),
                "rank": idx,
            })
    except Exception as e:
        log.error(f"解析热门股票排行失败: {e}")
        return []

    log.info(f"获取 {rank_type} 热门排行 {len(results)} 条")
    return results


# ==================== 北向资金流向 ====================


def get_northbound_flow(market_type: str = "hsgt", days: int = 30) -> List[Dict]:
    """获取沪深港通（北向）资金流向。

    数据来源:
        https://push2.eastmoney.com/api/qt/kamt.kline/get
        对应页面: https://data.eastmoney.com/hsgt/index.html

    Args:
        market_type: 市场类型，可选:
            - "hsgt"  : 沪深港通汇总（北向+南向，默认）
            - "north" : 仅北向资金（外资流入 A 股）
            - "south" : 仅南向资金（内资流入港股）
            - "hgt"   : 沪股通
            - "sgt"   : 深股通
        days: 返回最近 N 个交易日的数据，默认 30，最大 365

    Returns:
        [
            {
                "date": "2024-01-15",         # 日期
                "net_inflow": 5.68,            # 当日净流入(亿元)，正=流入，负=流出
                "balance": 514.32,             # 当日余额(亿元)
                "buy_amount": 850.0,           # 买入成交额(亿元)
                "sell_amount": 844.32,         # 卖出成交额(亿元)
                "cumulative_inflow": 18230.5,  # 累计净流入(亿元)
            },
            ...
        ]
    """
    # 市场类型映射
    market_map = {
        "hsgt":  "1",  # 沪深港通汇总
        "north": "1",  # 北向汇总
        "south": "3",  # 南向汇总
        "hgt":   "1",  # 沪股通（北向-沪）
        "sgt":   "3",  # 深股通（北向-深，与south同ID但不同查询）
    }

    market_id = market_map.get(market_type, "1")

    url = f"{EASTMONEY_PUSH_API}/kamt.kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "klt": "101",           # 日K线
        "lmt": str(min(days, 365)),
        "da": "1",
        "marketType": market_id,
    }

    data = _em_json_get(url, params=params, referer="data")
    if data is None:
        return []

    results = []
    try:
        klines = data.get("data", {}).get("klines", []) if isinstance(data, dict) else []
        if not klines:
            return []

        for line in klines:
            # 数据格式: "日期,当日余额,买入额,卖出额,..."
            parts = str(line).split(",")
            if len(parts) < 4:
                continue

            date_str = parts[0].strip()
            # 字段说明（沪深港通）:
            # f51=日期, f52=当日余额, f53=?, f54=买入成交额, f55=卖出成交额,
            # f56=?, f57=?, f58=?
            balance = _safe_float(parts[1] if len(parts) > 1 else 0)
            buy = _safe_float(parts[3] if len(parts) > 3 else 0)
            sell = _safe_float(parts[4] if len(parts) > 4 else 0)
            # 净流入 = 买入 - 卖出（东方财富有些版本直接提供 net_inflow）
            if len(parts) > 5:
                # f55 可能直接是净买入
                net = _safe_float(parts[5])
            else:
                net = buy - sell

            # 亿元转换（原始单位通常是万元或元，需要根据量级判断）
            net_yi = round(abs(buy) + abs(sell), 2)
            # 如果数值很大（> 100000），说明是万元单位
            if abs(buy) > 100000 or abs(sell) > 100000:
                net_yi = round((abs(buy) + abs(sell)) / 100000000, 2)
                net = round(net / 100000000, 2)
                balance = round(balance / 100000000, 2)
                buy = round(buy / 100000000, 2)
                sell = round(sell / 100000000, 2)

            results.append({
                "date": date_str,
                "net_inflow": net,
                "balance": balance,
                "buy_amount": buy,
                "sell_amount": sell,
                "trade_amount": net_yi,
            })

    except Exception as e:
        log.error(f"解析北向资金数据失败: {e}")
        return []

    log.info(f"获取 {market_type} 北向资金最近 {len(results)} 个交易日数据")
    return results


# ==================== 龙虎榜 ====================


def get_dragon_tiger(date: str = "") -> List[Dict]:
    """获取龙虎榜数据。

    龙虎榜是交易所公布的当日涨跌幅偏离值达 7% 或换手率达 20%
    等异动股票的买卖席位信息。只返回上榜股票的基础行情数据，
    详细的营业部买卖信息需通过东方财富龙虎榜详情页进一步获取。

    数据来源:
        https://push2.eastmoney.com/api/qt/clist/get (龙虎榜筛选)
        对应页面: https://data.eastmoney.com/stock/trade/dragon.html

    Args:
        date: 日期，格式 "YYYY-MM-DD"，为空默认获取最近交易日

    Returns:
        [
            {
                "code": "000628",           # 股票代码
                "name": "高新发展",          # 股票名称
                "price": 35.50,             # 收盘价
                "change_pct": 10.02,        # 涨跌幅(%)
                "turnover": 15.6,           # 换手率(%)
                "net_inflow": 1.25,         # 主力净流入(亿元)
                "net_inflow_pct": 8.5,      # 主力净流入占比(%)
            },
            ...
        ]
    """
    url = f"{EASTMONEY_PUSH_API}/clist/get"
    params = {
        "pn": "1",
        "pz": "50",
        "po": "0",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fid": "f62",
        "fs": "m:0+t:6+t:80+t:2+t:23",
        "fields": DRAGON_TIGER_FIELDS,
    }

    data = _em_json_get(url, params=params, referer="data")
    if data is None:
        return []

    results = []
    try:
        items = data.get("data", {}).get("diff", []) if isinstance(data, dict) else []

        for item in items:
            results.append({
                "code": _safe_str(item.get("f12", "")),
                "name": _safe_str(item.get("f14", "")),
                "price": _safe_float(item.get("f2", 0)),
                "change_pct": _safe_float(item.get("f3", 0)),
                "turnover": _safe_float(item.get("f8", 0)),
                "net_inflow": round(_safe_float(item.get("f62", 0)) / 1e8, 2),
                "net_inflow_pct": _safe_float(item.get("f184", 0)),
                "super_large_net": round(_safe_float(item.get("f66", 0)) / 1e8, 2),
                "large_net": round(_safe_float(item.get("f72", 0)) / 1e8, 2),
                "medium_net": round(_safe_float(item.get("f78", 0)) / 1e8, 2),
                "small_net": round(_safe_float(item.get("f84", 0)) / 1e8, 2),
            })
    except Exception as e:
        log.error(f"解析龙虎榜数据失败: {e}")
        return []

    log.info(f"获取龙虎榜 {len(results)} 条记录")
    return results


# ==================== 板块资金流向 ====================


def get_sector_flow(sector_code: str = "BK0477", days: int = 5) -> List[Dict]:
    """获取板块资金流向。

    数据来源:
        https://push2.eastmoney.com/api/qt/slist/get
        对应页面: https://data.eastmoney.com/bkzj/hy.html

    Args:
        sector_code: 板块代码，默认为 "BK0477"（证券板块）。
                     其他示例:
                         - "BK0477": 证券
                         - "BK0473": 银行
                         - "BK0451": 白酒
                         - "BK0718": 半导体
        days: 返回最近 N 日数据，默认 5

    Returns:
        [
            {
                "date": "2024-01-15",         # 日期
                "sector_code": "BK0477",      # 板块代码
                "sector_name": "证券",         # 板块名称
                "main_net_inflow": 5.68,      # 主力净流入(亿元)
                "super_large_net": 3.21,      # 超大单净流入(亿元)
                "large_net": 2.47,            # 大单净流入(亿元)
                "medium_net": -1.15,          # 中单净流入(亿元)
                "small_net": -4.53,           # 小单净流入(亿元)
                "change_pct": 1.25,           # 板块涨跌幅(%)
            },
            ...
        ]
    """
    url = f"{EASTMONEY_PUSH_API}/slist/get"
    params = {
        "spt": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fs": f"m:90+t:2+f:!50,{(sector_code)}",
        "fields": "f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87,f109,f110,f124",
    }

    data = _em_json_get(url, params=params, referer="data")
    if data is None:
        return []

    results = []
    try:
        items = data.get("data", {}).get("diff", []) if isinstance(data, dict) else []

        for item in items[:days]:
            results.append({
                "sector_code": _safe_str(item.get("f12", "")),
                "sector_name": _safe_str(item.get("f14", "")),
                "price": _safe_float(item.get("f2", 0)),
                "change_pct": _safe_float(item.get("f3", 0)),
                "main_net_inflow": round(_safe_float(item.get("f62", 0)) / 1e8, 2),
                "super_large_net": round(_safe_float(item.get("f66", 0)) / 1e8, 2),
                "super_large_pct": _safe_float(item.get("f69", 0)),
                "large_net": round(_safe_float(item.get("f72", 0)) / 1e8, 2),
                "large_pct": _safe_float(item.get("f75", 0)),
                "medium_net": round(_safe_float(item.get("f78", 0)) / 1e8, 2),
                "medium_pct": _safe_float(item.get("f81", 0)),
                "small_net": round(_safe_float(item.get("f84", 0)) / 1e8, 2),
                "small_pct": _safe_float(item.get("f87", 0)),
                "update_time": _safe_str(item.get("f124", "")),
            })
    except Exception as e:
        log.error(f"解析板块资金流向失败: {e}")
        return []

    log.info(f"获取板块 {sector_code} 资金流向 {len(results)} 条记录")
    return results


# ==================== 获取所有行业板块资金流向 ====================


def get_all_sector_flows(limit: int = 20) -> List[Dict]:
    """获取所有行业板块的资金流向排名。

    返回主力资金净流入最多的板块排行，常用于判断当日市场热点。

    Args:
        limit: 返回板块数量，默认 20

    Returns:
        [{sector_code, sector_name, main_net_inflow, change_pct, ...}, ...]
    """
    url = f"{EASTMONEY_PUSH_API}/clist/get"
    params = {
        "pn": "1",
        "pz": str(min(limit, 100)),
        "po": "0",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fid": "f62",       # 按主力净流入排序
        "fs": "m:90+t:2",   # 行业板块
        "fields": "f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87,f109,f110,f124",
    }

    data = _em_json_get(url, params=params, referer="data")
    if data is None:
        return []

    results = []
    try:
        items = data.get("data", {}).get("diff", []) if isinstance(data, dict) else []

        for item in items:
            results.append({
                "sector_code": _safe_str(item.get("f12", "")),
                "sector_name": _safe_str(item.get("f14", "")),
                "change_pct": _safe_float(item.get("f3", 0)),
                "main_net_inflow": round(_safe_float(item.get("f62", 0)) / 1e8, 2),
                "super_large_net": round(_safe_float(item.get("f66", 0)) / 1e8, 2),
                "large_net": round(_safe_float(item.get("f72", 0)) / 1e8, 2),
                "medium_net": round(_safe_float(item.get("f78", 0)) / 1e8, 2),
                "small_net": round(_safe_float(item.get("f84", 0)) / 1e8, 2),
            })
    except Exception as e:
        log.error(f"解析行业板块资金流向失败: {e}")
        return []

    log.info(f"获取行业板块资金流向 {len(results)} 条记录")
    return results


# ==================== Class Wrapper ====================


class EastMoneyScraper:
    """东方财富数据爬虫 v1.0

    封装六大核心功能：基金净值、股票行情、热门排行、北向资金、龙虎榜、板块资金。

    使用示例:
        >>> em = EastMoneyScraper()
        >>> quote = em.get_stock_quote("600519")
        >>> print(f"{quote['name']}: {quote['price']}")
    """

    def __init__(self):
        self.base_url = EASTMONEY_PUSH_API

    def get_fund_nav(self, fund_code: str, limit: int = 30) -> List[Dict]:
        """获取基金历史净值"""
        return get_fund_nav(fund_code, limit)

    def get_stock_quote(self, stock_code: str) -> Dict:
        """获取股票实时行情"""
        return get_stock_quote(stock_code)

    def get_hot_stocks(self, rank_type: str = "volume", limit: int = 20) -> List[Dict]:
        """获取热门股票排行"""
        return get_hot_stocks(rank_type, limit)

    def get_northbound_flow(self, market_type: str = "hsgt", days: int = 30) -> List[Dict]:
        """获取沪深港通北向资金流向"""
        return get_northbound_flow(market_type, days)

    def get_dragon_tiger(self, date: str = "") -> List[Dict]:
        """获取龙虎榜数据"""
        return get_dragon_tiger(date)

    def get_sector_flow(self, sector_code: str = "BK0477", days: int = 5) -> List[Dict]:
        """获取板块资金流向"""
        return get_sector_flow(sector_code, days)

    def get_all_sector_flows(self, limit: int = 20) -> List[Dict]:
        """获取所有行业板块资金流向"""
        return get_all_sector_flows(limit)


# ==================== 便捷入口 ====================


def get_eastmoney_data(data_type: str, **kwargs) -> List[Dict]:
    """东方财富数据统一便捷入口。

    Args:
        data_type: 数据类型，可选:
            - "fund_nav"         — 基金净值，需传 fund_code
            - "stock_quote"      — 股票行情，需传 stock_code
            - "hot_stocks"       — 热门排行，可选 rank_type
            - "northbound_flow"  — 北向资金，可选 market_type, days
            - "dragon_tiger"     — 龙虎榜，可选 date
            - "sector_flow"      — 板块资金，可选 sector_code, days
            - "all_sector_flows" — 全行业板块资金，可选 limit
        **kwargs: 传递给对应函数的参数

    Returns:
        对应数据列表或字典

    Examples:
        >>> get_eastmoney_data("stock_quote", stock_code="600519")
        >>> get_eastmoney_data("hot_stocks", rank_type="rise", limit=10)
        >>> get_eastmoney_data("northbound_flow", days=5)
    """
    dispatcher = {
        "fund_nav": lambda: get_fund_nav(
            fund_code=kwargs.get("fund_code", ""),
            limit=kwargs.get("limit", 30),
        ),
        "stock_quote": lambda: [get_stock_quote(
            stock_code=kwargs.get("stock_code", ""),
        )],
        "hot_stocks": lambda: get_hot_stocks(
            rank_type=kwargs.get("rank_type", "volume"),
            limit=kwargs.get("limit", 20),
        ),
        "northbound_flow": lambda: get_northbound_flow(
            market_type=kwargs.get("market_type", "hsgt"),
            days=kwargs.get("days", 30),
        ),
        "dragon_tiger": lambda: get_dragon_tiger(
            date=kwargs.get("date", ""),
        ),
        "sector_flow": lambda: get_sector_flow(
            sector_code=kwargs.get("sector_code", "BK0477"),
            days=kwargs.get("days", 5),
        ),
        "all_sector_flows": lambda: get_all_sector_flows(
            limit=kwargs.get("limit", 20),
        ),
    }

    handler = dispatcher.get(data_type)
    if handler is None:
        log.error(f"不支持的数据类型: {data_type}，可选: {list(dispatcher.keys())}")
        return [{"error": f"不支持的数据类型: {data_type}"}]

    try:
        return handler()
    except Exception as e:
        log.error(f"get_eastmoney_data({data_type}) 执行失败: {e}")
        return [{"error": str(e)}]


# ==================== CLI 测试入口 ====================


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("东方财富数据爬虫 v1.0 — 功能测试")
    print("=" * 60)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd in ("fund", "all"):
        # 测试1: 基金净值
        print("\n[测试1] 获取基金净值 — 华夏成长混合(000001)")
        fund_data = get_fund_nav("000001", limit=5)
        print(f"获取到 {len(fund_data)} 条记录")
        for i, item in enumerate(fund_data[:3], 1):
            print(f"  {i}. {item.get('date', '?')} "
                  f"单位净值={item.get('nav', '?')} "
                  f"日涨跌={item.get('daily_return', '?')}%")

    if cmd in ("stock", "all"):
        # 测试2: 股票行情
        print("\n[测试2] 获取股票实时行情")
        for code in ["600519", "000001"]:
            quote = get_stock_quote(code)
            if "error" not in quote:
                sign = "+" if quote.get("change_pct", 0) >= 0 else ""
                print(f"  {quote.get('name', code)} "
                      f"最新价={quote.get('price', '?')} "
                      f"涨跌幅={sign}{quote.get('change_pct', '?')}%")
            else:
                print(f"  {code}: {quote.get('error')}")

    if cmd in ("hot", "all"):
        # 测试3: 热门股票
        print("\n[测试3] 获取涨幅榜 Top 10")
        hot = get_hot_stocks(rank_type="rise", limit=10)
        for i, item in enumerate(hot[:5], 1):
            print(f"  {i}. {item.get('name', '?')} "
                  f"涨跌幅={item.get('change_pct', '?')}% "
                  f"成交额={item.get('amount', '?')}亿")

    if cmd in ("flow", "all"):
        # 测试4: 北向资金
        print("\n[测试4] 获取北向资金流向（近5日）")
        flow = get_northbound_flow(days=5)
        for i, item in enumerate(flow[:5], 1):
            direction = "流入" if item.get("net_inflow", 0) >= 0 else "流出"
            print(f"  {i}. {item.get('date', '?')} "
                  f"净{direction}={abs(item.get('net_inflow', 0)):.2f}亿 "
                  f"成交额={item.get('trade_amount', 0):.2f}亿")

    if cmd in ("dragon", "all"):
        # 测试5: 龙虎榜
        print("\n[测试5] 获取龙虎榜 Top 10")
        dragon = get_dragon_tiger()
        for i, item in enumerate(dragon[:10], 1):
            sign = "+" if item.get("change_pct", 0) >= 0 else ""
            print(f"  {i}. {item.get('name', '?')} "
                  f"涨跌幅={sign}{item.get('change_pct', '?')}% "
                  f"主力净流入={item.get('net_inflow', '?')}亿")

    if cmd in ("sector", "all"):
        # 测试6: 板块资金
        print("\n[测试6] 获取行业板块资金流向 Top 5")
        sector_flows = get_all_sector_flows(limit=5)
        for i, item in enumerate(sector_flows, 1):
            direction = "流入" if item.get("main_net_inflow", 0) >= 0 else "流出"
            print(f"  {i}. {item.get('sector_name', '?')} "
                  f"涨跌幅={item.get('change_pct', '?')}% "
                  f"主力{direction}={abs(item.get('main_net_inflow', 0)):.2f}亿")

    if cmd in ("convenience", "all"):
        # 测试7: 便捷入口
        print("\n[测试7] 便捷入口 get_eastmoney_data()")
        data = get_eastmoney_data("hot_stocks", rank_type="volume", limit=5)
        for i, item in enumerate(data, 1):
            print(f"  {i}. {item.get('name', '?')} 成交量={item.get('volume', '?')}")

    print("\n" + "=" * 60)
    print("测试完成")
