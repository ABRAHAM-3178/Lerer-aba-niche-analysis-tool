"""
数据加载器：处理卖家精灵导出的多Sheet Excel文件
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any

def load_keyword_history(file) -> pd.DataFrame:
    """
    加载关键词历史Excel，返回合并后的关键词数据DataFrame
    每个Sheet名格式：History-{keyword}
    """
    sheets = pd.read_excel(file, sheet_name=None, engine='openpyxl')
    all_data = []
    for sheet_name, df in sheets.items():
        if not sheet_name.startswith('History-'):
            continue
        keyword = sheet_name.replace('History-', '').strip()
        if '-' in keyword:
            keyword = keyword.split('-')[0].strip()
        if '月份' not in df.columns:
            continue
        df['月份'] = pd.to_datetime(df['月份'], errors='coerce')
        df = df.sort_values('月份')
        latest = df.iloc[-1].copy()
        record = {
            'keyword': keyword,
            'monthly_search_volume': latest.get('月搜索量', 0),
            'purchase_rate': latest.get('购买率', 0),
            'ppc_bid': latest.get('PPC价格', 0),
            'supply_demand_ratio': latest.get('需供比', 0),
            'click_concentration': latest.get('点击总占比', 0),
            'search_growth_rate': latest.get('搜索增长率', 0),
            'avg_price': latest.get('均价', 0),
            'aba_rank': latest.get('ABA排名', 0),
        }
        all_data.append(record)
    df_keyword = pd.DataFrame(all_data)
    df_keyword = df_keyword[df_keyword['keyword'].notna()]
    return df_keyword

def load_product_history(file) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    加载产品历史数据，返回 (ASIN数据表, 趋势验证表, 价格表)
    """
    sheets = pd.read_excel(file, sheet_name=None, engine='openpyxl')
    sales_sheet = sheets.get('产品历史月销量')
    price_sheet = sheets.get('历史月价格')
    if sales_sheet is None or price_sheet is None:
        raise ValueError("缺少必要的Sheet：产品历史月销量或历史月价格")
    
    sales_df = sales_sheet.set_index('ASIN')
    price_df = price_sheet.set_index('ASIN')
    
    month_cols = [col for col in sales_df.columns if re.match(r'\d{4}-\d{2}', str(col))]
    if not month_cols:
        raise ValueError("未找到月份列")
    month_cols.sort()
    latest_month = month_cols[-1]
    
    if latest_month in price_df.columns:
        current_price_series = price_df[latest_month]
    else:
        current_price_series = pd.Series(index=price_df.index, data=0)
    
    if len(month_cols) >= 6:
        recent_months = month_cols[-3:]
        older_months = month_cols[-6:-3]
        recent_sales = sales_df[recent_months].mean(axis=1)
        older_sales = sales_df[older_months].mean(axis=1)
        sales_growth = (recent_sales - older_sales) / older_sales.replace(0, pd.NA) * 100
    else:
        recent_sales = sales_df[month_cols[-1]]
        older_sales = sales_df[month_cols[0]]
        sales_growth = (recent_sales - older_sales) / older_sales.replace(0, pd.NA) * 100
    
    asin_list = sales_df.index.tolist()
    asin_data = []
    for asin in asin_list:
        price = current_price_series.get(asin, 0)
        asin_data.append({
            'asin': asin,
            'price': price,
        })
    df_asin = pd.DataFrame(asin_data)
    
    trend_data = []
    for asin in asin_list:
        initial_price = None
        if month_cols[0] in price_df.columns:
            initial_price = price_df.loc[asin, month_cols[0]] if asin in price_df.index else None
        trend_data.append({
            'asin': asin,
            'initial_monthly_sales': older_sales.get(asin, 0),
            'current_monthly_sales': recent_sales.get(asin, 0),
            'current_price': current_price_series.get(asin, 0),
            'initial_price': initial_price,
            'sales_growth': sales_growth.get(asin, 0),
            'modifier': '',
        })
    df_trend = pd.DataFrame(trend_data)
    
    df_price = price_df.reset_index().melt(id_vars=['ASIN'], var_name='月份', value_name='价格')
    df_price.rename(columns={'ASIN': 'asin'}, inplace=True)
    
    return df_asin, df_trend, df_price
