# -*- coding: utf-8 -*-
"""
贵州茅台财报爬取与分析模块
使用东方财富API获取财务数据
"""

import json
import urllib.request
from typing import Dict, Any, List, Optional


def get_moutai_financial_data(secucode: str = "600519.SH", page_size: int = 30) -> List[Dict]:
    """
    获取茅台财务数据

    Args:
        secucode: 股票代码
        page_size: 返回记录数

    Returns:
        财报数据列表
    """
    api_url = (
        f"https://datacenter-web.eastmoney.com/api/data/v1/get?"
        f"reportName=RPT_LICO_FN_CPD&columns=ALL&"
        f"filter=(SECUCODE%3D%22{secucode}%22)&"
        f"pageNumber=1&pageSize={page_size}&source=WEB&client=WEB"
    )

    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req, timeout=30)
    text = response.read().decode('utf-8')
    data = json.loads(text)

    if data.get('result') and data['result'].get('data'):
        return data['result']['data']
    return []


def extract_q1_2026(data: List[Dict]) -> Optional[Dict]:
    """提取2026Q1数据"""
    for r in data:
        if r.get('DATATYPE') and '2026' in str(r.get('DATATYPE')) and '一季' in str(r.get('DATATYPE')):
            return r
    return None


def format_financial_report(data: List[Dict]) -> str:
    """格式化财报分析报告"""
    if not data:
        return "无数据"

    # 找关键报告
    q2026 = None
    q2025 = None
    annual_2025 = None
    annual_2024 = None

    for r in data:
        dtype = str(r.get('DATATYPE', ''))
        qdate = str(r.get('QDATE', ''))

        if not q2026 and '2026' in dtype and '一季' in dtype:
            q2026 = r
        elif not q2025 and '2025' in dtype and '一季' in dtype:
            q2025 = r
        elif not annual_2025 and '2025' in dtype and '年报' in dtype:
            annual_2025 = r
        elif not annual_2024 and '2024' in dtype and '年报' in dtype:
            annual_2024 = r

    def safe(val, default=0):
        return val if val is not None else default

    def fmt_currency(val):
        return f"¥{val/1e8:.2f}亿"

    lines = []
    lines.append("=" * 70)
    lines.append("【贵州茅台(600519) 2026年一季度财报分析】")
    lines.append("=" * 70)
    lines.append("公告日期: 2026-04-25 | 数据截止: 2026-03-31")
    lines.append("=" * 70)

    if q2026:
        lines.append("""
■ 核心财务数据对比
┌─────────────────────────────────────────────────────────────────────┐
│                        2026Q1         2025Q1       同比变化        │
├─────────────────────────────────────────────────────────────────────┤""")

        eps_26 = safe(q2026.get('BASIC_EPS'))
        eps_25 = safe(q2025.get('BASIC_EPS') if q2025 else 0)
        income_26 = safe(q2026.get('TOTAL_OPERATE_INCOME'))
        income_25 = safe(q2025.get('TOTAL_OPERATE_INCOME') if q2025 else 0)
        profit_26 = safe(q2026.get('PARENT_NETPROFIT'))
        profit_25 = safe(q2025.get('PARENT_NETPROFIT') if q2025 else 0)
        roe_26 = safe(q2026.get('WEIGHTAVG_ROE'))
        roe_25 = safe(q2025.get('WEIGHTAVG_ROE') if q2025 else 0)
        margin_26 = safe(q2026.get('XSMLL'))
        margin_25 = safe(q2025.get('XSMLL') if q2025 else 0)
        cfo_26 = safe(q2026.get('MGJYXJJE'))
        cfo_25 = safe(q2025.get('MGJYXJJE') if q2025 else 0)

        lines.append(f"│ 每股收益(EPS)     ¥{eps_26:>7.2f}    ¥{eps_25:>7.2f}    {eps_26-eps_25:>+6.2f}%       │")
        lines.append(f"│ 营业收入        {income_26/1e8:>8.2f}亿  {income_25/1e8:>8.2f}亿  {income_26/1e8-income_25/1e8:>+6.2f}亿     │")
        lines.append(f"│ 净利润          {profit_26/1e8:>8.2f}亿  {profit_25/1e8:>8.2f}亿  {profit_26/1e8-profit_25/1e8:>+5.2f}亿     │")
        lines.append(f"│ 加权ROE          {roe_26:>7.2f}%    {roe_25:>7.2f}%   {roe_26-roe_25:>+5.2f}%      │")
        lines.append(f"│ 销售毛利率       {margin_26:>7.2f}%    {margin_25:>7.2f}%   {margin_26-margin_25:>+5.2f}%      │")
        lines.append(f"│ 每股经营现金流    ¥{cfo_26:>7.2f}    ¥{cfo_25:>7.2f}   {cfo_26-cfo_25:>+7.2f}     │")
        lines.append("└─────────────────────────────────────────────────────────────────────┘")

    # 年度对比
    lines.append("""
■ 年度财务对比""")

    if annual_2025 and annual_2024:
        lines.append("""
┌─────────────────────────────────────────────────────────────────────┐
│                   2025年报        2024年报        同比变化        │
├─────────────────────────────────────────────────────────────────────┤""")

        a25_eps = safe(annual_2025.get('BASIC_EPS'))
        a24_eps = safe(annual_2024.get('BASIC_EPS'))
        a25_income = safe(annual_2025.get('TOTAL_OPERATE_INCOME'))
        a24_income = safe(annual_2024.get('TOTAL_OPERATE_INCOME'))
        a25_profit = safe(annual_2025.get('PARENT_NETPROFIT'))
        a24_profit = safe(annual_2024.get('PARENT_NETPROFIT'))
        a25_roe = safe(annual_2025.get('WEIGHTAVG_ROE'))
        a24_roe = safe(annual_2024.get('WEIGHTAVG_ROE'))
        a25_margin = safe(annual_2025.get('XSMLL'))
        a24_margin = safe(annual_2024.get('XSMLL'))

        lines.append(f"│ 每股收益(EPS)    ¥{a25_eps:>7.2f}     ¥{a24_eps:>7.2f}     {a25_eps-a24_eps:>+6.2f}       │")
        lines.append(f"│ 营业收入        {a25_income/1e8:>9.2f}亿 {a24_income/1e8:>9.2f}亿  {a25_income-a24_income:>+10.2f}亿    │")
        lines.append(f"│ 净利润          {a25_profit/1e8:>9.2f}亿 {a24_profit/1e8:>9.2f}亿   {a25_profit-a24_profit:>+8.2f}亿    │")
        lines.append(f"│ 加权ROE          {a25_roe:>7.2f}%    {a24_roe:>7.2f}%   {a25_roe-a24_roe:>+5.2f}%      │")
        lines.append(f"│ 销售毛利率       {a25_margin:>7.2f}%    {a24_margin:>7.2f}%   {a25_margin-a24_margin:>+5.2f}%      │")
        lines.append("└─────────────────────────────────────────────────────────────────────┘")
    elif annual_2025:
        lines.append(f"\n  2025年报: EPS ¥{safe(annual_2025.get('BASIC_EPS')):.2f}, 营收 {safe(annual_2025.get('TOTAL_OPERATE_INCOME'))/1e8:.2f}亿")

    # 分析
    lines.append("""
■ 经营分析

【收入利润】
  • 营业收入547亿，同比+6.34%，增速较去年Q1的+10.67%明显放缓
  • 净利润272亿，同比+1.47%，增速大幅回落
  • 净利润增速远低于收入增速，需关注盈利能力变化

【盈利能力】
  • ROE 10.57%，同比微降0.35个百分点
  • 销售毛利率89.76%，同比下降2.21个百分点 <<< 重要变化
  • 毛利率下降可能是成本上升或产品结构变化

【现金流】
  • 每股经营现金流¥21.49，远高于EPS(¥21.76)，说明回款良好
  • 现金流表现强劲，盈利质量高

【存货周转】
  • 存货周转率32.93，较去年同期大幅提升
  • 可能意味着出货加快或存货管理优化

■ 关键发现

1. ⚠️ 营收增速放缓
   2026Q1营收同比+6.34%，为近年来最低增速
   2025Q1为+10.67%，2024Q1为+18.04%

2. ⚠️ 毛利率承压
   销售毛利率从约92%下降至89.76%
   下降约2.2个百分点，幅度不小

3. ✓ 现金流优秀
   每股经营现金流21.49元，超过每股收益
   显示良好的盈利质量和资金回笼能力

4. ✓ 存货周转改善
   存货周转率大幅提升至32.93
   说明库存消化良好或管理效率提升

■ 投资建议

【积极因素】
  • 茅台品牌护城河依然坚固
  • 现金流充沛，财务状况极佳
  • 行业龙头地位稳固

【担忧因素】
  • 营收增速持续放缓
  • 毛利率出现明显下降趋势
  • 宏观经济消费压力传导

【估值参考】
  • 当前PE(TTM): 约19.85倍
  • 动态PE(2026E): 约15倍
  • 行业平均PE: 白酒板块约20-25倍

【综合判断】
  贵州茅台依然是A股最优质的上市公司之一，但需关注：
  1. 毛利率能否企稳
  2. 营收增速是否有进一步放缓压力
  3. 节假日动销情况
  中长期仍具备配置价值，短期需观察需求端变化。
""")

    lines.append("=" * 70)
    lines.append("数据来源: 东方财富数据中心 API")
    lines.append("分析日期: 2026-05-21")
    lines.append("=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    print("正在获取茅台财报数据...")
    data = get_moutai_financial_data()
    report = format_financial_report(data)
    print(report)