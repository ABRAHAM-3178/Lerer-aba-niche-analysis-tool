"""
Excel报告生成模块（支持AI摘要）
"""

import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Any


def generate_excel_report(
    scored_markets: List[Dict[str, Any]],
    data: Dict[str, pd.DataFrame],
    comment_insights: List[Dict[str, Any]],
    project_name: str,
    category: str,
    date_range: list,
    use_ai: bool = False,
    api_key: str = None,
    model: str = None,
    base_url: str = None
) -> bytes:
    
    if use_ai and api_key and scored_markets:
        try:
            from utils.ai_client import AIClient
            from utils.prompts import build_summary_messages
            client = AIClient(api_key=api_key, model=model, base_url=base_url)
            for market in scored_markets:
                try:
                    messages = build_summary_messages(market)
                    market['ai_summary'] = client.chat_text(messages)
                except Exception as e:
                    market['ai_summary'] = f"AI摘要生成失败: {e}"
        except Exception as e:
            print(f"⚠️ AI 摘要生成失败: {e}")
            for market in scored_markets:
                market['ai_summary'] = "AI摘要生成失败，请检查API配置"
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_overview = pd.DataFrame(scored_markets)
        if 'ai_summary' in df_overview.columns:
            cols = ['name', 'grade', 'final_score', 'keyword_count', 'weight_level',
                    'market_size_score', 'conversion_score', 'competition_score',
                    'growth_score', 'profit_score', 'brand_monopoly_score',
                    'new_product_score', 'modifier_acceptance_score',
                    'price_elasticity_score', 'seasonality_score',
                    'ai_summary', 'keywords']
            available_cols = [c for c in cols if c in df_overview.columns]
            df_overview = df_overview[available_cols]
        df_overview.to_excel(writer, sheet_name='细分市场总览', index=False)
        
        if 'keyword' in data and data['keyword'] is not None:
            df_keyword = data['keyword'].copy()
            df_keyword.to_excel(writer, sheet_name='关键词明细', index=False)
        
        if 'asin' in data and data['asin'] is not None:
            df_asin = data['asin'].copy()
            df_asin.to_excel(writer, sheet_name='ASIN排行', index=False)
        
        if comment_insights:
            df_comment = pd.DataFrame(comment_insights)
            cols = ['asin', 'review_count', 'depth', 'avg_rating', 'positive_ratio',
                    'top_pains', 'top_praises', 'product_suggestions', 'listing_suggestions']
            available_cols = [c for c in cols if c in df_comment.columns]
            df_comment = df_comment[available_cols]
            df_comment.to_excel(writer, sheet_name='评论洞察与优化', index=False)
        
        df_timing = pd.DataFrame([{
            '细分市场': m.get('name', ''),
            '等级': m.get('grade', ''),
            '综合分': m.get('final_score', 0),
            '推荐入场时间': '建议3-6个月内',
            '备货建议': '首批1-2个月销量'
        } for m in scored_markets])
        df_timing.to_excel(writer, sheet_name='入场时机规划', index=False)
        
        df_trend = pd.DataFrame([{
            '卖点': m.get('name', ''),
            '等级': m.get('grade', ''),
            '综合分': m.get('final_score', 0)
        } for m in scored_markets])
        df_trend.to_excel(writer, sheet_name='卖点趋势验证', index=False)
    
    return output.getvalue()
