#!/usr/bin/env python3
"""
A股板块批量数据采集模板 (v3.2)
配合 industry-research 技能使用

使用前必读 references/eastmoney-api-availability-matrix.md
——先查哪些端点可用，避免对 404/503 端点循环重试。
"""

import json
import time
import urllib.request
import os

OUTPUT_DIR = "."
SEMI_STOCKS_BY_CATEGORY = {
    "设计": ["603501","300661","603986","002049","300782","688256","688008","688521","688536"],
    "制造": ["688981","688396"],
    "封测": ["600584","002185","002156"],
    "设备": ["002371","688012","688072","300604"],
    "材料": ["688126","688019","300655","603650"],
}

def fetch_tencent(stock_codes):
    """腾讯行情 API —— 最稳定，直连无需代理"""
    codes = [f"sh{c}" if c.startswith('6') else f"sz{c}" for c in stock_codes]
    url = f"http://qt.gtimg.cn/q={','.join(codes)}"
    raw = urllib.request.urlopen(url, timeout=10).read().decode('gbk')
    results = {}
    for line in raw.strip().split('\n'):
        fields = line.split('"')[1].split('~') if '"' in line else []
        if len(fields) < 50:
            continue
        code = fields[2]
        results[code] = {
            "name": fields[1], "price": float(fields[3] or 0),
            "change_pct": float(fields[32] or 0), "pe": float(fields[39] or 0),
            "market_cap": float(fields[45] or 0),
            "high": float(fields[33] or 0), "low": float(fields[34] or 0),
        }
    return results

def fetch_klines(secid, begin, end):
    """东方财富 K线 —— push2his 比 push2 更稳定"""
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?" \
          f"secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57" \
          f"&klt=101&fqt=1&beg={begin}&end={end}&ut=fa5fd1943c7b386f172d6893dbbdf45b"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://quote.eastmoney.com/'
    })
    raw = urllib.request.urlopen(req, timeout=15).read().decode()
    data = json.loads(raw)
    klines = data.get('data', {}).get('klines', [])
    return [l.split(',') for l in klines]

if __name__ == '__main__':
    # 1. 实时行情（腾讯API → 始终可用）
    all_codes = [c for codes in SEMI_STOCKS_BY_CATEGORY.values() for c in codes]
    stock_data = fetch_tencent(all_codes)
    total_mc = sum(v['market_cap'] for v in stock_data.values())
    pe_median = sorted(v['pe'] for v in stock_data.values() if v['pe'] > 0)[len(stock_data)//2]
    print(f"板块: {len(stock_data)}只, 总市值{total_mc:.0f}亿, PE中位{pe_median:.0f}")

    # 2. ETF K线（push2his）
    etf_klines = fetch_klines("0.159995", "20260601", "20260730")
    if etf_klines:
        first_close = float(etf_klines[0][2])
        last_close = float(etf_klines[-1][2])
        print(f"芯片ETF 159995: {first_close:.3f}→{last_close:.3f} ({((last_close/first_close)-1)*100:+.1f}%)")

    # 3. 保存
    with open(os.path.join(OUTPUT_DIR, "raw_data.json"), "w", encoding="utf-8") as f:
        json.dump(stock_data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存: {OUTPUT_DIR}/raw_data.json")

# ⚠️ 不推荐在脚本中循环调用的端点（已验证全 404/503）：
# - datainterface.eastmoney.com (龙虎榜) → 全 404
# - push2.eastmoney.com/api/qt/clist/get?fs=m:90+t2 (板块估值) → 503
# - push2.eastmoney.com/api/qt/ulist.np/get (批量行情) → 代理断连
# 替代方案见 references/china-financial-data-fallback.md
