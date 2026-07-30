# -*- coding: utf-8 -*-
"""
爬取华宝ETF基金信息
目标页面: https://fund.eastmoney.com/etf/
"""

import json
import re
import time
from pathlib import Path

# Scrapling导入
try:
    from scrapling.fetchers import DynamicFetcher
    from scrapling.parser import Selector
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    print("[错误] Scrapling未安装")

# 输出路径
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "huabao_etf_result.json"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def scrape_etf_list_page():
    """爬取ETF列表页面"""
    url = "https://fund.eastmoney.com/etf/"

    print(f"正在爬取ETF列表页面: {url}")
    print("使用 headless=True, network_idle=True 等待页面加载...")

    try:
        page = DynamicFetcher.fetch(url, headless=True, network_idle=True)
        print("页面加载成功!")
        return page
    except Exception as e:
        print(f"[错误] 页面爬取失败: {e}")
        return None


def extract_etf_table(page):
    """从页面提取ETF表格数据"""
    funds = []

    # 尝试多种方式提取表格数据
    # 方法1: 直接查找表格行
    try:
        table_rows = page.css('tbody tr, .fix-tbody tr, table tr')
    except Exception:
        table_rows = []

    if table_rows:
        print(f"找到 {len(table_rows)} 行表格数据")

        for row in table_rows:
            try:
                cells = row.css('td')
                if len(cells) < 6:
                    continue

                # 解析每行数据
                row_texts = [cell.text().strip() for cell in cells]

                # 尝试提取基金代码和名称
                # 通常格式: [代码, 名称, 当前价, 涨跌幅, 净值, 规模, ...]
                code = ""
                name = ""
                current_price = ""
                change_percent = ""
                nav = ""
                scale = ""
                tracking_index = ""

                # 查找代码和名称 (通常在第一个或第二个单元格)
                for i, text in enumerate(row_texts):
                    if re.match(r'^\d{6}$', text):
                        code = text
                        if i + 1 < len(row_texts):
                            name = row_texts[i + 1]
                        break

                # 提取价格和涨跌幅
                for i, text in enumerate(row_texts):
                    if re.search(r'[\d.]+', text) and i > 1:
                        if '%' in text or '-' in text:
                            change_percent = text
                        elif current_price == "":
                            current_price = text

                # 尝试从更多列获取净值、规模等信息
                # 根据天天基金ETF页面结构调整
                numeric_cols = []
                for text in row_texts[2:]:
                    cleaned = re.sub(r'[^\d.]+', '', text)
                    if cleaned and '.' in cleaned:
                        numeric_cols.append(cleaned)

                if len(numeric_cols) >= 1:
                    current_price = numeric_cols[0] if current_price == "" else current_price
                if len(numeric_cols) >= 2:
                    change_percent = row_texts[row_texts.index(numeric_cols[0]) + 1] if numeric_cols[0] in row_texts else ""
                if len(numeric_cols) >= 3:
                    nav = numeric_cols[2]

                # 尝试提取规模和跟踪指数
                for i, text in enumerate(row_texts):
                    if '亿' in text:
                        scale = text
                    if '指数' in text or 'ETF' in text.upper():
                        tracking_index = text

                if code:
                    fund_info = {
                        "code": code,
                        "name": name,
                        "current_price": current_price,
                        "change_percent": change_percent,
                        "nav": nav,
                        "规模": scale,
                        "跟踪指数": tracking_index
                    }
                    funds.append(fund_info)

            except Exception as e:
                continue

    # 方法2: 如果表格提取失败，尝试其他方式
    if not funds:
        print("表格直接提取失败，尝试备选方法...")

        # 尝试查找所有包含6位数字代码的元素
        all_text = page.css('body').text()

        # 提取页面中所有ETF代码相关的信息块
        # 天天基金ETF页面通常有特定结构
        fund_blocks = page.css('.fix-table, .table-wrapper, #table_wrapper, .etf-table')

        for block in fund_blocks:
            block_text = block.text()
            # 查找华宝基金相关的ETF
            if '华宝' in block_text:
                # 提取该区块中的所有ETF
                links = block.css('a[href*="/fund/"]')
                for link in links:
                    href = link.attrs.get('href', '')
                    text = link.text().strip()
                    code_match = re.search(r'(\d{6})', href)
                    if code_match and text:
                        funds.append({
                            "code": code_match.group(1),
                            "name": text,
                            "current_price": "",
                            "change_percent": "",
                            "nav": "",
                            "规模": "",
                            "跟踪指数": ""
                        })

    return funds


def extract_huabao_etfs(all_funds):
    """从所有ETF中筛选华宝基金的产品"""
    huabao_funds = []

    for fund in all_funds:
        name = fund.get('name', '')
        # 华宝基金ETF名称通常包含"华宝"二字
        if '华宝' in name:
            huabao_funds.append(fund)

    return huabao_funds


def get_huabao_etf_details(etf_codes):
    """获取华宝ETF详细信息"""
    detailed_funds = []

    for code in etf_codes[:10]:  # 限制数量避免请求过多
        url = f"https://fund.eastmoney.com/ETF/{code}.html"
        print(f"  正在获取详情: {code}")

        try:
            page = DynamicFetcher.fetch(url, headless=True, network_idle=True)
            time.sleep(1)  # 礼貌爬取

            fund_info = {"code": code}

            # 提取基金名称
            name_elem = page.css('.title, .fundName, h1, .name')
            if name_elem:
                fund_info["name"] = name_elem[0].text().strip()

            # 提取当前价格
            price_elem = page.css('.price, .current-price, .actual-price')
            if price_elem:
                price_text = price_elem[0].text()
                price_match = re.search(r'([\d.]+)', price_text)
                if price_match:
                    fund_info["current_price"] = price_match.group(1)

            # 提取涨跌幅
            change_elem = page.css('.change, .percent, .fluctuation')
            if change_elem:
                fund_info["change_percent"] = change_elem[0].text().strip()

            # 提取净值
            nav_elem = page.css('.nav, .NAV, .unit-nav')
            if nav_elem:
                nav_text = nav_elem[0].text()
                nav_match = re.search(r'([\d.]+)', nav_text)
                if nav_match:
                    fund_info["nav"] = nav_match.group(1)

            # 提取规模
            scale_elem = page.css('.scale, .fund-scale, [class*="规模"]')
            if scale_elem:
                fund_info["规模"] = scale_elem[0].text().strip()

            # 提取跟踪指数
            index_elem = page.css('.index, .tracking-index, [class*="跟踪指数"]')
            if index_elem:
                fund_info["跟踪指数"] = index_elem[0].text().strip()

            detailed_funds.append(fund_info)

        except Exception as e:
            print(f"    获取 {code} 详情失败: {e}")
            detailed_funds.append({"code": code, "name": "", "error": str(e)})

    return detailed_funds


def main():
    print("=" * 60)
    print("华宝ETF基金信息爬取")
    print("=" * 60)

    if not SCRAPLING_AVAILABLE:
        print("[错误] Scrapling库未安装")
        return

    # 1. 爬取ETF列表页面
    page = scrape_etf_list_page()
    if page is None:
        # 如果无法访问，生成示例数据
        print("\n无法访问页面，生成示例数据结构...")
        sample_result = {
            "funds": [
                {
                    "code": "512700",
                    "name": "华宝中证医疗ETF",
                    "current_price": 0.65,
                    "change_percent": "-2.32%",
                    "nav": 0.6532,
                    "规模": "45.23亿",
                    "跟踪指数": "中证医疗指数"
                },
                {
                    "code": "513600",
                    "name": "华宝纳斯达克ETF",
                    "current_price": 1.25,
                    "change_percent": "1.15%",
                    "nav": 1.2489,
                    "规模": "12.56亿",
                    "跟踪指数": "纳斯达克100指数"
                },
                {
                    "code": "515000",
                    "name": "华宝科技ETF",
                    "current_price": 1.18,
                    "change_percent": "0.85%",
                    "nav": 1.1792,
                    "规模": "28.34亿",
                    "跟踪指数": "中证科技指数"
                },
                {
                    "code": "516110",
                    "name": "华宝消费ETF",
                    "current_price": 0.92,
                    "change_percent": "-0.54%",
                    "nav": 0.9187,
                    "规模": "8.67亿",
                    "跟踪指数": "中证消费指数"
                }
            ],
            "fallback": True,
            "warning": "网络请求失败，返回的是示例数据而非实时数据，请勿用于实际投资决策"
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_result, f, ensure_ascii=False, indent=2)

        print(f"结果已保存到: {OUTPUT_FILE}")
        print("\n示例数据 (由于网络限制):")
        print(json.dumps(sample_result, ensure_ascii=False, indent=2))
        return

    # 2. 提取ETF数据
    print("\n正在提取ETF数据...")
    all_funds = extract_etf_table(page)
    print(f"提取到 {len(all_funds)} 个ETF记录")

    # 3. 筛选华宝基金ETF
    print("\n正在筛选华宝基金ETF...")
    huabao_funds = extract_huabao_etfs(all_funds)
    print(f"找到 {len(huabao_funds)} 个华宝ETF")

    # 4. 如果找到华宝ETF，尝试获取详情
    if huabao_funds:
        codes = [f['code'] for f in huabao_funds]
        detailed = get_huabao_etf_details(codes)

        # 合并详情
        for fund in huabao_funds:
            for detail in detailed:
                if fund['code'] == detail['code']:
                    fund.update(detail)
                    break

    # 5. 保存结果
    result = {"funds": huabao_funds if huabao_funds else []}

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {OUTPUT_FILE}")
    print("\n爬取结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()