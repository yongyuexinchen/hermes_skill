# -*- coding: utf-8 -*-
"""
A股上市公司全量名单更新器 v1.0
数据来源：东方财富（免费公开API，实时更新）
输出：data/listed_companies.json

更新频率：每周一次（上市公司名单变动少）
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from http_utils import http_get, rate_limit
    HTTP_UTILS = True
except ImportError:
    HTTP_UTILS = False

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "listed_companies.json"

# 东方财富全A股列表API（公开接口，无需登录）
EASTMONEY_STOCK_API = (
    "https://push2.eastmoney.com/api/qt/clist/get"
    "?pn={page}&pz=500&po=1&np=1&fltt=2&invt=2"
    "&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
    "&fields=f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f100,f115"
)


class StockListUpdater:
    """A股上市公司名单更新器"""

    def __init__(self):
        self.session = None

    def fetch_all_stocks(self) -> List[Dict]:
        """从东方财富获取全量A股上市公司名单（含行情快照）"""
        all_stocks = []
        page = 1

        while True:
            url = EASTMONEY_STOCK_API.format(page=page)
            if HTTP_UTILS:
                resp = http_get(url, timeout=15, rate_limit_delay=0.5)
                if resp is None:
                    break
                data = resp.json()
            else:
                import requests
                resp = requests.get(url, timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                data = resp.json()

            items = data.get('data', {}).get('diff', [])
            if not items:
                break

            for item in items:
                all_stocks.append({
                    'code': str(item.get('f12', '')),
                    'name': str(item.get('f14', '')),
                    'market': 'SH' if str(item.get('f12', '')).startswith('6') else 'SZ',
                    'price': item.get('f2'),
                    'change_pct': item.get('f3'),
                    'volume': item.get('f5'),
                    'amount': item.get('f6'),
                    'market_cap': item.get('f20'),       # 总市值
                    'pe_ttm': item.get('f9'),            # 市盈率TTM
                    'industry': str(item.get('f100', '')),
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

            total = data.get('data', {}).get('total', 0)
            if len(items) < 500 or page * 500 >= total:
                break
            page += 1
            time.sleep(0.3)

        return all_stocks

    def save(self, stocks: List[Dict]):
        """保存到本地JSON"""
        output = {
            'meta': {
                'total_count': len(stocks),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': '东方财富公开API',
                'markets': {
                    'SH': sum(1 for s in stocks if s['market'] == 'SH'),
                    'SZ': sum(1 for s in stocks if s['market'] == 'SZ'),
                }
            },
            'stocks': stocks
        }
        OUTPUT_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False)
        print(f"保存 {len(stocks)} 只股票到 {OUTPUT_FILE}")

    def run(self):
        """执行更新"""
        print(f"[{datetime.now():%Y-%m-%d %H:%M}] 开始更新A股上市公司名单...")
        stocks = self.fetch_all_stocks()
        if stocks:
            self.save(stocks)
            print(f"完成: {len(stocks)} 只股票")
            return {'success': True, 'count': len(stocks)}
        return {'success': False, 'count': 0}


if __name__ == "__main__":
    updater = StockListUpdater()
    result = updater.run()
    print(json.dumps(result, ensure_ascii=False))
