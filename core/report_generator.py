"""
Excel报告生成模块
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
    date_range: list
) -> bytes:
    """生成Excel报告"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        df_overview = pd.DataFrame(scored_markets)
        df_overview.to_excel(writer, sheet_name='细分市场总览', index=False)
        
        if 'aba' in data:
            aba_df = data['aba']
            cols_to_keep = [c for c in ['search_term', 'search_frequency_rank', 'click_share', 'conversion_share'] if c in aba_df.columns]
            if cols_to_keep:
                df_keyword = aba_df[cols_to_keep].copy()
                df_keyword.columns = ['关键词', '搜索排名', '点击份额', '转化份额'][:len(cols_to_keep)]
                df_keyword.to_excel(writer, sheet_name='关键词明细', index=False)
        
        if 'asin' in data:
            df_asin = data['asin'].copy()
            df_asin.to_excel(writer, sheet_name='ASIN排行', index=False)
        
        if comment_insights:
            df_comment = pd.DataFrame(comment_insights)
            if 'suggestions' in df_comment.columns:
                df_comment['产品建议'] = df_comment['suggestions'].apply(lambda x: '; '.join(x.get('product', [])))
                df_comment['Listing建议'] = df_comment['suggestions'].apply(lambda x: '; '.join(x.get('listing', [])))
                df_comment = df_comment.drop(columns=['suggestions'])
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
