# -*- coding: utf-8 -*-
"""雪球股票数据提取模块"""

import re
import json
from pathlib import Path
from typing import Dict, Any, Optional


def extract_xueqiu_stock_data(html: str) -> Dict[str, Any]:
    """
    从雪球页面HTML中提取股票数据

    Args:
        html: 雪球页面HTML内容

    Returns:
        股票数据字典
    """
    data = {}

    # 方法1: 直接查找 quote: {...} 模式
    quote_match = re.search(r'quote:\s*(\{".+?\})', html, re.DOTALL)
    if quote_match:
        quote_str = quote_match.group(1)
        try:
            quote_data = json.loads(quote_str)
            # 映射字段
            data['symbol'] = quote_data.get('symbol', 'N/A')
            data['name'] = quote_data.get('name', 'N/A')
            data['code'] = quote_data.get('code', 'N/A')
            data['current'] = str(quote_data.get('current', 'N/A'))
            data['percent'] = str(quote_data.get('percent', 'N/A'))
            data['chg'] = quote_data.get('chg', 'N/A')
            data['open'] = str(quote_data.get('open', 'N/A'))
            data['high'] = str(quote_data.get('high', 'N/A'))
            data['low'] = str(quote_data.get('low', 'N/A'))
            data['high52w'] = str(quote_data.get('high52w', 'N/A'))
            data['low52w'] = str(quote_data.get('low52w', 'N/A'))
            data['volume'] = str(quote_data.get('volume', 'N/A'))
            data['amount'] = str(quote_data.get('amount', 'N/A'))
            data['market_capital'] = str(quote_data.get('market_capital', 'N/A'))
            data['float_market_capital'] = str(quote_data.get('float_market_capital', 'N/A'))
            data['pe_ttm'] = str(quote_data.get('pe_ttm', 'N/A'))
            data['pe_lyr'] = str(quote_data.get('pe_lyr', 'N/A'))
            data['pe_forecast'] = str(quote_data.get('pe_forecast', 'N/A'))
            data['pb'] = str(quote_data.get('pb', 'N/A'))
            data['dividend_yield'] = str(quote_data.get('dividend_yield', 'N/A'))
            data['dividend'] = str(quote_data.get('dividend', 'N/A'))
            data['eps'] = str(quote_data.get('eps', 'N/A'))
            data['navps'] = str(quote_data.get('navps', 'N/A'))
            data['turnover_rate'] = str(quote_data.get('turnover_rate', 'N/A'))
            data['volume_ratio'] = str(quote_data.get('volume_ratio', 'N/A'))
            data['float_shares'] = str(quote_data.get('float_shares', 'N/A'))
            data['total_shares'] = str(quote_data.get('total_shares', 'N/A'))
            data['limit_up'] = str(quote_data.get('limit_up', 'N/A'))
            data['limit_down'] = str(quote_data.get('limit_down', 'N/A'))
            data['profit'] = str(quote_data.get('profit', 'N/A'))
            data['profit_four'] = str(quote_data.get('profit_four', 'N/A'))
            data['followerText'] = quote_data.get('followerText', 'N/A')

            return data
        except json.JSONDecodeError:
            pass

    # 方法2: SNB模式（备用）
    sn_match = re.search(r'SNB\s*=\s*\{', html)
    if not sn_match:
        return {"error": "未找到股票数据"}
    # 从匹配到的 '{' 开始做花括号配对
    # （修复原 start+7 硬编码偏移 Bug：正则 SNB\s*=\s*\{ 允许可变空白，
    #   固定偏移 7 在 "SNB={" 等情形下会截断 JSON）
    brace_start = sn_match.end() - 1  # '{' 的位置
    brace_count = 0
    end = brace_start

    for i, c in enumerate(html[brace_start:]):
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                end = brace_start + i + 1
                break

    snb_str = html[brace_start:end]

    # 提取关键字段
    def extract_field(pattern: str) -> Optional[str]:
        match = re.search(pattern, snb_str)
        return match.group(1) if match else None

    data['symbol'] = extract_field(r'"symbol":"([^"]+)"') or 'N/A'
    data['name'] = extract_field(r'"name":"([^"]+)"') or 'N/A'
    data['code'] = extract_field(r'"code":"([^"]+)"') or 'N/A'
    data['current'] = extract_field(r'"current":"?([0-9.]+)"?') or extract_field(r'"current":([0-9.]+)') or 'N/A'
    data['percent'] = extract_field(r'"percent":([0-9.-]+)') or 'N/A'
    data['chg'] = extract_field(r'"chg":"?([0-9.-]+)"?') or 'N/A'
    data['open'] = extract_field(r'"open":"?([0-9.]+)"?') or 'N/A'
    data['high'] = extract_field(r'"high":"?([0-9.]+)"?') or 'N/A'
    data['low'] = extract_field(r'"low":"?([0-9.]+)"?') or 'N/A'
    data['high52w'] = extract_field(r'"high52w":([0-9.]+)') or 'N/A'
    data['low52w'] = extract_field(r'"low52w":([0-9.]+)') or 'N/A'
    data['volume'] = extract_field(r'"volume":([0-9]+)') or 'N/A'
    data['amount'] = extract_field(r'"amount":([0-9]+)') or 'N/A'
    data['market_capital'] = extract_field(r'"market_capital":([0-9]+)') or 'N/A'
    data['float_market_capital'] = extract_field(r'"float_market_capital":([0-9]+)') or 'N/A'
    data['pe_ttm'] = extract_field(r'"pe_ttm":([0-9.]+)') or 'N/A'
    data['pe_lyr'] = extract_field(r'"pe_lyr":([0-9.]+)') or 'N/A'
    data['pe_forecast'] = extract_field(r'"pe_forecast":([0-9.]+)') or 'N/A'
    data['pb'] = extract_field(r'"pb":([0-9.]+)') or 'N/A'
    data['dividend_yield'] = extract_field(r'"dividend_yield":([0-9.]+)') or 'N/A'
    data['dividend'] = extract_field(r'"dividend":([0-9.]+)') or 'N/A'
    data['eps'] = extract_field(r'"eps":([0-9.]+)') or 'N/A'
    data['navps'] = extract_field(r'"navps":([0-9.]+)') or 'N/A'
    data['turnover_rate'] = extract_field(r'"turnover_rate":([0-9.]+)') or 'N/A'
    data['volume_ratio'] = extract_field(r'"volume_ratio":([0-9.]+)') or 'N/A'
    data['float_shares'] = extract_field(r'"float_shares":([0-9]+)') or 'N/A'
    data['total_shares'] = extract_field(r'"total_shares":([0-9]+)') or 'N/A'
    data['limit_up'] = extract_field(r'"limit_up":([0-9.]+)') or 'N/A'
    data['limit_down'] = extract_field(r'"limit_down":([0-9.]+)') or 'N/A'
    data['profit'] = extract_field(r'"profit":([0-9.]+)') or 'N/A'
    data['profit_four'] = extract_field(r'"profit_four":([0-9.]+)') or 'N/A'
    data['followerText'] = extract_field(r'"followerText":"([^"]+)"') or 'N/A'

    return data


def safe_float(val, default=0.0):
    """安全转换为浮点数"""
    if val is None or val == 'N/A' or val == '':
        return default
    try:
        return float(val)
    except:
        return default

def safe_int(val, default=0):
    """安全转换为整数"""
    if val is None or val == 'N/A' or val == '':
        return default
    try:
        return int(float(val))  # 先转float再转int，处理 "82320067101.68" 这种情况
    except:
        return default


def format_stock_report(data: Dict[str, Any]) -> str:
    """
    格式化股票数据为可读报告

    Args:
        data: 股票数据字典

    Returns:
        格式化报告文本
    """
    if "error" in data:
        return f"错误: {data['error']}"

    try:
        current = safe_float(data.get('current', 0))
        market_cap = safe_int(data.get('market_capital', 0))
        pe_ttm = safe_float(data.get('pe_ttm', 0))
        pb = safe_float(data.get('pb', 0))
        dividend_yield = safe_float(data.get('dividend_yield', 0))
        low52w = safe_float(data.get('low52w', 0))
        high52w = safe_float(data.get('high52w', 0))

        position_52w = (current - low52w) / (high52w - low52w) * 100 if high52w > low52w else 0

        report = f"""
■ 基本行情
  股票名称: {data.get('name', 'N/A')}
  股票代码: {data.get('symbol', 'N/A')}
  当前价格: ¥{current:,.2f}
  涨跌额: {data.get('chg', 'N/A')}
  涨跌幅: {data.get('percent', 'N/A')}%
  今开: {data.get('open', 'N/A')}
  最高: {data.get('high', 'N/A')}
  最低: {data.get('low', 'N/A')}
  涨停价: {data.get('limit_up', 'N/A')}
  跌停价: {data.get('limit_down', 'N/A')}

■ 交易数据
  成交量: {safe_int(data.get('volume', 0)):,}股
  成交额: ¥{safe_int(data.get('amount', 0)):,.0f}
  换手率: {data.get('turnover_rate', 'N/A')}%
  量比: {data.get('volume_ratio', 'N/A')}

■ 市值数据
  总市值: ¥{market_cap/1e8:.2f}亿 ({market_cap/1e9:.2f}万亿)
  流通市值: ¥{safe_int(data.get('float_market_capital', 0))/1e8:.2f}亿
  总股本: {safe_int(data.get('total_shares', 0))/1e8:.2f}亿股
  流通股: {safe_int(data.get('float_shares', 0))/1e8:.2f}亿股

■ 估值指标
  PE(TTM): {pe_ttm:.2f}
  PE(动态): {data.get('pe_forecast', 'N/A')}
  PE(静): {data.get('pe_lyr', 'N/A')}
  PB: {pb:.2f}
  股息率: {dividend_yield:.2f}%
  每股收益(EPS): ¥{data.get('eps', 'N/A')}
  每股净资产: ¥{data.get('navps', 'N/A')}

■ 52周数据
  52周最高: ¥{high52w:.2f}
  52周最低: ¥{low52w:.2f}
  当前处于52周位置: {position_52w:.1f}%

■ 盈利能力
  净利润: ¥{safe_float(data.get('profit', 0))/1e8:.2f}亿
  四季度净利润: ¥{safe_float(data.get('profit_four', 0))/1e8:.2f}亿

■ 市场关注度
  雪球关注: {data.get('followerText', 'N/A')}
"""
        return report
    except Exception as e:
        return f"格式化错误: {e}"


if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'scripts')

    from scrapling.fetchers import DynamicSession

    url = "https://xueqiu.com/S/SH600519"

    print("正在爬取雪球茅台数据...")
    print("="*60)

    with DynamicSession(headless=True, network_idle=True, timeout=60000) as session:
        page = session.fetch(url)
        html = page.prettify()

        # 保存HTML
        output_dir = Path(__file__).parent.parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        html_file = output_dir / 'xueqiu_maotai.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML已保存: {html_file}")

        # 提取数据
        data = extract_xueqiu_stock_data(html)

        # 生成报告
        report = format_stock_report(data)

        print("\n" + "="*60)
        print("【雪球 - 贵州茅台(SH600519) 数据提取报告】")
        print("="*60)
        print(report)
        print("="*60)
        print("✓ 数据提取成功!")