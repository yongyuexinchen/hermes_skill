# -*- coding: utf-8 -*-
"""
金融产品分析模块
基于爬取数据进行财务分析和投资组合建议
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
FUND_DB_DIR = Path(__file__).parent.parent / "data"


def calculate_risk_metrics(nav_data: Dict[str, float]) -> Dict[str, float]:
    """
    计算风险指标

    Args:
        nav_data: 净值数据，包含1month, 3month, 6month, 1year, 3year收益率

    Returns:
        风险指标字典
    """
    metrics = {}

    # 年化收益率计算（基于各周期收益率估算）
    if "1year" in nav_data:
        metrics["annual_return"] = nav_data["1year"]
    if "3year" in nav_data:
        metrics["annual_return_3y"] = (1 + nav_data["3year"] / 100) ** (1/3) - 1

    # 估算夏普比率（简化版，需要无风险利率和波动率）
    # 这里用收益率/最大回撤估算
    if "max_drawdown" in nav_data:
        metrics["calmar_ratio"] = abs(nav_data.get("annual_return", 0) / nav_data["max_drawdown"]) if nav_data["max_drawdown"] != 0 else 0

    return metrics


def analyze_investment_style(holdings: Dict[str, Any], nav_data: Dict[str, float]) -> str:
    """
    分析投资风格

    Args:
        holdings: 持仓数据
        nav_data: 净值数据

    Returns:
        风格标签
    """
    style_indicators = []

    # 基于持仓分析
    if "stocks" in holdings and holdings["stocks"]:
        stocks = holdings["stocks"]

        # 计算持仓集中度
        total_weight = sum(s.get("weight", 0) for s in stocks)
        avg_weight = total_weight / len(stocks) if stocks else 0

        if avg_weight > 5:
            style_indicators.append("集中")
        else:
            style_indicators.append("分散")

        # 行业分析
        industries = set()
        for stock in stocks:
            # 简单基于股票代码判断（仅示例）
            code = stock.get("code", "")
            if code.startswith("6"):
                industries.add("主板")
            elif code.startswith("3") or code.startswith("0"):
                industries.add("创业板/中小板")

        # 基于收益分析
        if "1year" in nav_data:
            if nav_data["1year"] > 30:
                style_indicators.append("积极成长")
            elif nav_data["1year"] > 15:
                style_indicators.append("成长")
            elif nav_data["1year"] > 5:
                style_indicators.append("均衡")
            else:
                style_indicators.append("稳健")

    return "-".join(style_indicators) if style_indicators else "均衡型"


def suggest_similar_products(product_info: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """
    推荐相似产品（基于本地基金数据库）

    Args:
        product_info: 产品信息
        limit: 返回数量

    Returns:
        相似产品列表
    """
    suggestions = []

    # 加载本地基金数据库
    fund_db_path = FUND_DB_DIR / "fund_managers_distilled.json"
    if not fund_db_path.exists():
        return [{"note": "本地数据库不可用，请先更新基金数据"}]

    try:
        with open(fund_db_path, 'r', encoding='utf-8') as f:
            fund_db = json.load(f)

        # 获取管理器列表（数据库结构为 {managers: [...], meta: {...}}）
        fund_data = fund_db.get('managers', [])

        # 简单匹配（基于风格和类型）
        target_type = product_info.get("product_type", "")
        target_style = analyze_investment_style(
            product_info.get("holdings", {}),
            product_info.get("historical_nav", {})
        )

        matches = []
        for item in fund_data[:500]:  # 只检查前500条
            # 简单相似度计算
            score = 0
            if target_type in item.get("fund_type", ""):
                score += 1
            # 风格匹配（支持部分匹配，如"成长"匹配"成长型"）
            item_style = item.get("investment_style", "")
            if item_style and target_style:
                if item_style in target_style or target_style.split("-")[-1] in item_style:
                    score += 2

            if score > 0:
                matches.append({
                    "name": item.get("name", ""),
                    "fund_name": item.get("current_fund_name", ""),
                    "company": item.get("company_name", ""),
                    "style": item.get("investment_style", ""),
                    "score": score
                })

        # 排序并返回top结果
        matches.sort(key=lambda x: x["score"], reverse=True)
        suggestions = matches[:limit]

    except Exception as e:
        return [{"error": f"数据库查询失败: {e}"}]

    return suggestions


def generate_portfolio_replication(product_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成投资组合复刻建议

    Args:
        product_info: 原始产品信息

    Returns:
    复刻建议
    """
    replication = {
        "target_product": product_info.get("product_name", "未知"),
        "target_code": product_info.get("product_code", ""),
        "target_style": "",
        "allocation": [],
        "similar_products": [],
        "total_suggestion": ""
    }

    # 分析风格
    holdings = product_info.get("holdings", {})
    nav_data = product_info.get("historical_nav", {})
    style = analyze_investment_style(holdings, nav_data)
    replication["target_style"] = style

    # 提取核心持仓
    if "stocks" in holdings and holdings["stocks"]:
        for i, stock in enumerate(holdings["stocks"][:10], 1):
            replication["allocation"].append({
                "rank": i,
                "stock_code": stock.get("code", ""),
                "stock_name": stock.get("name", ""),
                "weight": stock.get("weight", 0),
                "alternative": suggest_alternatives(stock.get("name", ""))
            })

    # 推荐相似产品
    replication["similar_products"] = suggest_similar_products(product_info)

    # 总配置建议
    replication["total_suggestion"] = f"""
基于{replication['target_product']}的分析：
- 投资风格：{style}
- 建议持有周期：3-5年
- 适合投资者类型：积极型
- 配置建议：可将总资产的20-30%配置于同类风格产品
"""

    return replication


def suggest_alternatives(stock_name: str) -> List[str]:
    """
    推荐股票替代品

    Args:
        stock_name: 原始股票名称

    Returns:
    替代品列表
    """
    # 简化的替代品映射（实际应该基于行业和基本面）
    alternatives_map = {
        "贵州茅台": ["五粮液", "泸州老窖", "洋河股份"],
        "宁德时代": ["比亚迪", "国轩高科", "亿纬锂能"],
        "五粮液": ["贵州茅台", "泸州老窖", "古井贡酒"],
        "比亚迪": ["宁德时代", "理想汽车", "小鹏汽车"],
        "招商银行": ["宁波银行", "平安银行", "兴业银行"],
        "中国平安": ["中国人寿", "新华保险", "太平洋保险"],
        "腾讯控股": ["阿里巴巴", "美团", "京东"],
        "阿里巴巴": ["腾讯控股", "拼多多", "京东"],
    }

    return alternatives_map.get(stock_name, ["同行业龙头股"])


def analyze_product(product_info: Dict[str, Any]) -> str:
    """
    综合分析产品并生成报告

    Args:
        product_info: 产品信息字典

    Returns:
    分析报告文本
    """
    name = product_info.get("product_name", "未知")
    code = product_info.get("product_code", "")
    product_type = product_info.get("product_type", "")
    company = product_info.get("company", "")
    manager = product_info.get("manager", "")
    risk = product_info.get("risk_level", "")

    nav = product_info.get("nav", {})
    historical = product_info.get("historical_nav", {})
    holdings = product_info.get("holdings", {})
    risk_metrics = product_info.get("risk_metrics", {})

    # 计算风格
    style = analyze_investment_style(holdings, historical)

    # 风险指标
    metrics_calc = calculate_risk_metrics(historical)

    # 构建报告
    report = f"""
【产品分析报告】

■ 基本信息
名称：{name}
代码：{code}
类型：{product_type}
公司：{company}
经理：{manager}
风险等级：{risk}

■ 收益表现
{"-"*40}
"""
    if nav:
        report += f"最新净值：{nav.get('current', 'N/A')}\n"
        report += f"日涨跌幅：{nav.get('daily_change', 'N/A')}%\n"

    if historical:
        report += "\n历史收益：\n"
        for period, value in historical.items():
            report += f"  近{period}：{value}%\n"

    report += f"""
■ 风险指标
{"-"*40}
"""
    if risk_metrics:
        for k, v in risk_metrics.items():
            report += f"{k}：{v}\n"
    if metrics_calc:
        for k, v in metrics_calc.items():
            report += f"{k}：{v:.2f}\n"

    report += f"""
■ 持仓分析
{"-"*40}
"""
    if "stocks" in holdings and holdings["stocks"]:
        report += "前十大重仓股：\n"
        for i, stock in enumerate(holdings["stocks"][:10], 1):
            report += f"  {i}. {stock.get('name', '')}({stock.get('code', '')}) - {stock.get('weight', 0)}%\n"
    if holdings.get("top_industry"):
        report += f"\n重点行业：{holdings['top_industry']}\n"

    report += f"""
■ 风格定位
{"-"*40}
{style}

■ 综合建议
{"-"*40}
"""
    # 基于分析生成建议
    if "成长" in style:
        report += "该产品为成长风格，适合积极型投资者，建议定投介入，持有周期3年以上。\n"
    elif "均衡" in style:
        report += "该产品为均衡风格，适合稳健型投资者，可作为资产配置的一部分。\n"
    elif "稳健" in style:
        report += "该产品为稳健风格，适合保守型投资者，可用于资产保值。\n"
    else:
        report += "建议根据自身风险偏好适量配置。\n"

    return report


if __name__ == "__main__":
    # 测试
    test_product = {
        "product_name": "华夏成长混合",
        "product_code": "000001",
        "product_type": "混合型-灵活配置",
        "company": "华夏基金",
        "manager": "张明",
        "risk_level": "中高风险",
        "nav": {"current": 3.4567, "daily_change": 1.23},
        "historical_nav": {"1month": 2.34, "3month": 5.89, "6month": 8.45, "1year": 15.67},
        "holdings": {
            "stocks": [
                {"code": "600519", "name": "贵州茅台", "weight": 5.2},
                {"code": "000858", "name": "五粮液", "weight": 4.8},
                {"code": "300750", "name": "宁德时代", "weight": 4.5}
            ],
            "top_industry": "食品饮料"
        }
    }

    print(analyze_product(test_product))
    print("\n" + "="*50 + "\n")
    print("【组合复刻建议】")
    print(json.dumps(generate_portfolio_replication(test_product), ensure_ascii=False, indent=2))