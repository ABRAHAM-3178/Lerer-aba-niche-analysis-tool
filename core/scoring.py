"""
10维综合评分模块
"""

from typing import Dict, Any, Optional
import pandas as pd


def assign_weight_level(rank: float, total_keywords: int) -> tuple:
    """分配权重等级"""
    if total_keywords <= 0:
        return ("🔴低", 1.0)
    
    percentile = rank / total_keywords
    
    if percentile <= 0.1:
        return ("🟢高", 3.0)
    elif percentile <= 0.5:
        return ("🟡中", 2.0)
    else:
        return ("🔴低", 1.0)


def score_market_size(monthly_search_volume: Optional[float], rank: Optional[float]) -> float:
    """市场规模评分"""
    if monthly_search_volume is not None:
        if monthly_search_volume > 80000:
            return 10.0
        elif monthly_search_volume > 50000:
            return 9.0
        elif monthly_search_volume > 20000:
            return 7.5
        elif monthly_search_volume > 5000:
            return 6.0
        elif monthly_search_volume > 1000:
            return 4.0
        else:
            return 2.0
    
    if rank is not None:
        if rank < 5000:
            return 9.0
        elif rank < 10000:
            return 8.0
        elif rank < 50000:
            return 6.0
        elif rank < 100000:
            return 4.0
        else:
            return 2.0
    
    return 5.0


def score_conversion_potential(purchase_rate: Optional[float], conversion_share: Optional[float]) -> float:
    """转化潜力评分"""
    if purchase_rate is not None:
        if purchase_rate > 8:
            return 10.0
        elif purchase_rate > 5:
            return 9.0
        elif purchase_rate > 3:
            return 7.0
        elif purchase_rate > 1.5:
            return 5.0
        elif purchase_rate > 0.5:
            return 3.0
        else:
            return 1.0
    
    if conversion_share is not None:
        if conversion_share > 70:
            return 9.0
        elif conversion_share > 50:
            return 7.0
        elif conversion_share > 30:
            return 5.0
        elif conversion_share > 10:
            return 3.0
        else:
            return 1.0
    
    return 5.0


def score_competition(click_concentration: Optional[float], spr: Optional[float], 
                      supply_demand: Optional[float]) -> float:
    """竞争难度评分（越高越难）"""
    if click_concentration is not None:
        if click_concentration < 20:
            base = 1.5
        elif click_concentration < 30:
            base = 3.0
        elif click_concentration < 45:
            base = 5.0
        elif click_concentration < 60:
            base = 7.0
        elif click_concentration < 80:
            base = 8.5
        else:
            base = 10.0
        
        if spr is not None:
            if spr < 5 and base < 5:
                base -= 1.0
            elif spr > 30 and base > 5:
                base += 1.0
        
        if supply_demand is not None:
            if supply_demand > 3 and base > 3:
                base -= 1.0
            elif supply_demand < 0.5 and base < 8:
                base += 1.0
        
        return max(1.0, min(10.0, base))
    
    return 5.0


def score_growth(search_growth_rate: Optional[float]) -> float:
    """成长性评分"""
    if search_growth_rate is not None:
        if search_growth_rate > 50:
            return 10.0
        elif search_growth_rate > 30:
            return 9.0
        elif search_growth_rate > 15:
            return 7.0
        elif search_growth_rate > 5:
            return 5.0
        elif search_growth_rate > -5:
            return 3.0
        else:
            return 1.0
    return 5.0


def score_profit(price: Optional[float], ppc_bid: Optional[float]) -> float:
    """利润空间评分"""
    if price is not None:
        if price > 35:
            base = 10.0
        elif price > 25:
            base = 9.0
        elif price > 18:
            base = 7.0
        elif price > 12:
            base = 5.0
        elif price > 8:
            base = 3.0
        else:
            base = 1.0
        
        if ppc_bid is not None:
            if ppc_bid < 1.0 and price > 20:
                base = min(10.0, base + 1.0)
            elif ppc_bid > 3.0 and price < 15:
                base = max(1.0, base - 1.0)
        
        return base
    
    return 5.0


def score_brand_monopoly(top_brands: list, total_keywords: int) -> float:
    """品牌垄断度评分"""
    if not top_brands or total_keywords == 0:
        return 5.0
    
    top3_count = sum([count for _, count in top_brands[:3]])
    ratio = top3_count / total_keywords
    
    if ratio < 0.2:
        return 2.0
    elif ratio < 0.35:
        return 4.0
    elif ratio < 0.5:
        return 6.0
    elif ratio < 0.65:
        return 8.0
    else:
        return 10.0


def score_new_product_survival(asins: list) -> float:
    """新品存活率评分"""
    if not asins:
        return 5.0
    
    import datetime
    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
    
    new_count = 0
    for asin in asins:
        listing_date = asin.get('listing_date')
        if listing_date:
            try:
                if isinstance(listing_date, str):
                    date = datetime.datetime.strptime(listing_date, '%Y-%m-%d')
                else:
                    date = listing_date
                if date > six_months_ago:
                    new_count += 1
            except:
                pass
    
    ratio = new_count / len(asins) if asins else 0
    
    if ratio > 0.3:
        return 9.0
    elif ratio > 0.2:
        return 7.0
    elif ratio > 0.1:
        return 5.0
    elif ratio > 0.05:
        return 3.0
    else:
        return 1.0


def score_seasonality(trend_data: list) -> float:
    """季节性波动评分"""
    if not trend_data or len(trend_data) < 4:
        return 7.0
    
    values = [d.get('value', 0) for d in trend_data if d.get('value')]
    if len(values) < 4:
        return 7.0
    
    mean = sum(values) / len(values)
    if mean == 0:
        return 7.0
    
    max_val = max(values)
    min_val = min(values)
    volatility = (max_val - min_val) / mean if mean else 0
    
    if volatility < 0.2:
        return 9.0
    elif volatility < 0.4:
        return 7.0
    elif volatility < 0.6:
        return 5.0
    elif volatility < 0.8:
        return 3.0
    else:
        return 1.0


def calculate_10d_scores(cluster: Dict[str, Any], keyword_df: pd.DataFrame = None,
                         asin_df: pd.DataFrame = None, trend_df: pd.DataFrame = None) -> Dict[str, Any]:
    """计算10维综合评分"""
    
    keywords = [k.get('search_term', '') for k in cluster.get('items', [])]
    
    keyword_data = None
    if keyword_df is not None and not keyword_df.empty:
        matched = keyword_df[keyword_df['keyword'].isin(keywords)]
        if not matched.empty:
            keyword_data = matched.iloc[0]
    
    asin_data = None
    if asin_df is not None and not asin_df.empty:
        matched = asin_df[asin_df['keyword'].isin(keywords)]
        if not matched.empty:
            asin_data = matched.iloc[0]
    
    market_size = score_market_size(
        keyword_data.get('monthly_search_volume') if keyword_data is not None else None,
        cluster.get('avg_rank')
    )
    
    conversion = score_conversion_potential(
        keyword_data.get('purchase_rate') if keyword_data is not None else None,
        cluster.get('avg_conversion_share')
    )
    
    competition = score_competition(
        keyword_data.get('click_concentration') if keyword_data is not None else None,
        None,
        keyword_data.get('supply_demand_ratio') if keyword_data is not None else None
    )
    
    growth = score_growth(
        keyword_data.get('search_growth_rate') if keyword_data is not None else None
    )
    
    profit = score_profit(
        asin_data.get('price') if asin_data is not None else None,
        keyword_data.get('ppc_bid') if keyword_data is not None else None
    )
    
    brand_monopoly = score_brand_monopoly(
        cluster.get('top_brands', []),
        cluster.get('keyword_count', 1)
    )
    
    new_product = score_new_product_survival(
        asin_df.to_dict('records') if asin_df is not None else []
    )
    
    seasonality = score_seasonality(
        trend_df.to_dict('records') if trend_df is not None else []
    )
    
    modifier_acceptance = min(10.0, (cluster.get('keyword_count', 0) / 10) * 2 + 3)
    if modifier_acceptance > 10:
        modifier_acceptance = 10
    
    price_elasticity = 5.0
    if asin_data is not None and asin_data.get('price'):
        price = asin_data.get('price')
        if price > 35:
            price_elasticity = 8.0
        elif price > 20:
            price_elasticity = 6.0
        elif price > 10:
            price_elasticity = 4.0
        else:
            price_elasticity = 2.0
    
    weights = {
        'market_size': 0.25,
        'conversion': 0.20,
        'competition': 0.25,
        'growth': 0.15,
        'profit': 0.15,
        'brand_monopoly': 0.05,
        'new_product': 0.05,
        'modifier_acceptance': 0.05,
        'price_elasticity': 0.05,
        'seasonality': 0.05
    }
    
    base_score = (
        market_size * weights['market_size'] +
        conversion * weights['conversion'] +
        (10 - competition) * weights['competition'] +
        growth * weights['growth'] +
        profit * weights['profit'] +
        (10 - brand_monopoly) * weights['brand_monopoly'] +
        new_product * weights['new_product'] +
        modifier_acceptance * weights['modifier_acceptance'] +
        price_elasticity * weights['price_elasticity'] +
        seasonality * weights['seasonality']
    )
    
    weight_level, weight_factor = assign_weight_level(
        cluster.get('avg_rank', 999999), 
        100000
    )
    
    final_score = min(base_score * weight_factor, 10)
    
    if final_score >= 8.0:
        grade = "S"
        grade_label = "强烈推荐"
    elif final_score >= 7.0:
        grade = "A"
        grade_label = "值得进入"
    elif final_score >= 6.0:
        grade = "B"
        grade_label = "谨慎考虑"
    elif final_score >= 4.5:
        grade = "C"
        grade_label = "一般不推荐"
    else:
        grade = "D"
        grade_label = "不推荐"
    
    return {
        'name': cluster.get('name', '未知'),
        'keyword_count': cluster.get('keyword_count', 0),
        'weight_level': weight_level,
        'weight_factor': weight_factor,
        'market_size_score': round(market_size, 1),
        'conversion_score': round(conversion, 1),
        'competition_score': round(competition, 1),
        'growth_score': round(growth, 1),
        'profit_score': round(profit, 1),
        'brand_monopoly_score': round(brand_monopoly, 1),
        'new_product_score': round(new_product, 1),
        'modifier_acceptance_score': round(modifier_acceptance, 1),
        'price_elasticity_score': round(price_elasticity, 1),
        'seasonality_score': round(seasonality, 1),
        'base_score': round(base_score, 2),
        'final_score': round(final_score, 2),
        'grade': grade,
        'grade_label': grade_label,
        'keywords': cluster.get('keywords', [])[:5],
        'ai_generated': cluster.get('ai_generated', False)
    }
