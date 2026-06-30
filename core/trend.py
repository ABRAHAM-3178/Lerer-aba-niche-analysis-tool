"""
卖点趋势验证模块 - 九象限判断矩阵
"""

from typing import Dict, Any, List
import pandas as pd


def trend_verification(market: Dict[str, Any], trend_df: pd.DataFrame) -> Dict[str, Any]:
    """执行卖点趋势验证"""
    
    if trend_df is None or trend_df.empty:
        return {
            "status": "数据不足",
            "quadrant": "未知",
            "conclusion": "无法判断",
            "strategy": "建议补充趋势验证数据"
        }
    
    name = market.get('name', '')
    matched = trend_df[trend_df['modifier'].str.contains(name, case=False, na=False)]
    
    if matched.empty:
        return {
            "status": "无匹配数据",
            "quadrant": "未知",
            "conclusion": "无法判断",
            "strategy": "建议补充该卖点的趋势数据"
        }
    
    sales_changes = []
    price_changes = []
    
    for _, row in matched.iterrows():
        if row.get('initial_monthly_sales') and row.get('current_monthly_sales'):
            try:
                change = (row['current_monthly_sales'] - row['initial_monthly_sales']) / row['initial_monthly_sales'] * 100
                sales_changes.append(change)
            except:
                pass
        
        if row.get('initial_price') and row.get('current_price'):
            try:
                change = (row['current_price'] - row['initial_price']) / row['initial_price'] * 100
                price_changes.append(change)
            except:
                pass
    
    if not sales_changes or not price_changes:
        return {
            "status": "数据不完整",
            "quadrant": "未知",
            "conclusion": "无法判断",
            "strategy": "请确保趋势验证表包含销量和价格数据"
        }
    
    avg_sales_change = sum(sales_changes) / len(sales_changes)
    avg_price_change = sum(price_changes) / len(price_changes)
    
    quadrant, conclusion, strategy, color = determine_quadrant(avg_sales_change, avg_price_change)
    
    return {
        "status": "分析完成",
        "avg_sales_change": round(avg_sales_change, 1),
        "avg_price_change": round(avg_price_change, 1),
        "sample_size": len(matched),
        "quadrant": quadrant,
        "conclusion": conclusion,
        "strategy": strategy,
        "color": color
    }


def determine_quadrant(sales_change: float, price_change: float) -> tuple:
    """九象限判断矩阵"""
    
    sales_up = sales_change > 15
    sales_down = sales_change < -15
    sales_stable = -15 <= sales_change <= 15
    
    price_up = price_change > 5
    price_down = price_change < -5
    price_stable = -5 <= price_change <= 5
    
    if sales_up and price_up:
        return ("🟢 完全接受（蓝海）", "可进", "立即进入，撇脂定价，抢占核心关键词", "#27ae60")
    elif sales_up and price_stable:
        return ("🟢 稳定增长（潜力市场）", "可进", "快速跟进，跟随定价，聚焦长尾词", "#2e86c1")
    elif sales_up and price_down:
        return ("🟡 竞争加剧（微蓝海）", "谨慎", "差异化进入，成本领先或高附加值定位", "#f39c12")
    elif sales_stable and price_up:
        return ("🟡 品质溢价（小众高客单）", "可进", "差异化进入高端，极致体验", "#f39c12")
    elif sales_stable and price_stable:
        return ("🟠 成熟稳定（红海）", "不建议", "除非有颠覆性创新，否则不建议进入", "#e67e22")
    elif sales_stable and price_down:
        return ("🟠 价格战（红海）", "不建议", "避免价格战陷阱，寻找差异化机会", "#e67e22")
    elif sales_down and price_up:
        return ("🔴 虚高泡沫（不可持续）", "放弃", "不建议进入，等待泡沫破裂", "#e74c3c")
    elif sales_down and price_stable:
        return ("🟠 衰退前兆（不建议）", "不建议", "寻找替代机会，不建议进入", "#e67e22")
    elif sales_down and price_down:
        return ("🔴 快速衰退（放弃）", "放弃", "坚决不进入，市场正在萎缩", "#c0392b")
    
    return ("未知", "无法判断", "数据异常，请检查数据", "#95a5a6")
