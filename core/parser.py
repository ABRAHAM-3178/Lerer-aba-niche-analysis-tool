"""
ABA CSV 解析器
"""

import pandas as pd
import re
from collections import Counter
from typing import Dict, List, Any, Optional

from utils.constants import (
    CATEGORY_KEYWORDS,
    BRAND_SUFFIXES,
    BRAND_PATTERNS,
    STOP_WORDS,
    GENERIC_BASE_WORDS,
    MODIFIER_CATEGORIES
)


def detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """自动检测列名映射"""
    cols = df.columns.tolist()
    mapping = {}
    
    possible_mappings = {
        'search_term': ['Search Term', 'Search Term (Customer Search Term)', 
                       'Customer Search Term', 'Keyword', 'search_term', '关键词'],
        'search_frequency_rank': ['Search Frequency Rank', 'Search Rank',
                                 'Frequency Rank', 'search_frequency_rank', 'Rank', '排名'],
        'top_clicked_brand': ['Top Clicked Brand', 'Top Brand',
                             'top_clicked_brand', 'Brand', '品牌'],
        'top_clicked_category': ['Top Clicked Category', 'Category',
                                'top_clicked_category', '类目'],
        'top_clicked_product_asin': ['Top Clicked Product ASIN', 'Top ASIN',
                                    'top_clicked_product_asin', 'ASIN'],
        'product_title': ['Product Title', 'Title', 'product_title', '标题'],
        'click_share': ['Click Share', 'Click %', 'click_share', '点击份额'],
        'conversion_share': ['Conversion Share', 'Conversion %', 'conversion_share', '转化份额'],
    }
    
    for std_name, possible in possible_mappings.items():
        for p in possible:
            for col in cols:
                if col.strip() == p:
                    mapping[std_name] = col
                    break
            if std_name in mapping:
                break
    
    # 模糊匹配
    if 'search_term' not in mapping:
        for col in cols:
            if 'search' in col.lower() and 'term' in col.lower():
                mapping['search_term'] = col
                break
    
    if 'click_share' not in mapping:
        for col in cols:
            if 'click' in col.lower() and ('share' in col.lower() or '%' in col):
                mapping['click_share'] = col
                break
    
    if 'conversion_share' not in mapping:
        for col in cols:
            if 'conversion' in col.lower() and ('share' in col.lower() or '%' in col):
                mapping['conversion_share'] = col
                break
    
    return mapping


def detect_category(keywords: List[str], titles: List[str]) -> str:
    """自动检测类目"""
    all_text = " ".join(keywords + titles).lower()
    category_scores = {}
    for cat, cat_keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in cat_keywords:
            if kw in all_text:
                score += 1
        if score > 0:
            category_scores[cat] = score
    if category_scores:
        return max(category_scores, key=category_scores.get)
    return "未识别"


def is_brand_keyword(term: str) -> tuple:
    """判断是否为品牌词"""
    term_lower = term.lower().strip()
    for brand in BRAND_SUFFIXES:
        if brand in term_lower:
            return True, brand
    for pattern in BRAND_PATTERNS:
        if re.search(pattern, term_lower):
            return True, re.search(pattern, term_lower).group()
    return False, None


def extract_modifiers(term: str, category_base_words: set = None) -> List[str]:
    """提取修饰词"""
    term_lower = term.lower()
    base_words = category_base_words or set()
    all_base_words = base_words | GENERIC_BASE_WORDS
    for word in all_base_words:
        term_lower = re.sub(rf'\b{word}\b', '', term_lower)
        term_lower = re.sub(rf'\b{word}s\b', '', term_lower)
    words = re.findall(r'[a-z]+', term_lower)
    modifiers = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return modifiers


def get_modifier_category(modifier: str) -> str:
    """获取修饰词所属类别"""
    modifier_lower = modifier.lower()
    for category, keywords in MODIFIER_CATEGORIES.items():
        for kw in keywords:
            if kw in modifier_lower:
                return category
    return "其他"


def parse_aba_csv(df: pd.DataFrame) -> Dict[str, Any]:
    """解析ABA数据"""
    if df is None:
        return {"error": "未提供ABA数据"}
    
    # 检测列映射
    col_mapping = detect_columns(df)
    
    # 重命名列
    rename_map = {v: k for k, v in col_mapping.items() if v}
    df_clean = df.rename(columns=rename_map)
    
    # 确保必要列存在
    if 'search_term' not in df_clean.columns:
        return {"error": "无法找到Search Term列"}
    
    # 清理数据
    df_clean = df_clean.dropna(subset=['search_term'])
    df_clean = df_clean[df_clean['search_term'].astype(str).str.strip() != '']
    df_clean = df_clean.reset_index(drop=True)
    
    # 排名列
    if 'search_frequency_rank' in df_clean.columns:
        df_clean['search_frequency_rank'] = pd.to_numeric(
            df_clean['search_frequency_rank'], errors='coerce'
        )
    
    # 份额列
    for col in ['click_share', 'conversion_share']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.replace('%', '')
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # 关键词分类
    brand_keywords = []
    non_brand_keywords = []
    for _, row in df_clean.iterrows():
        term = str(row['search_term'])
        is_brand, brand_name = is_brand_keyword(term)
        item = {
            'search_term': term,
            'search_frequency_rank': row.get('search_frequency_rank', None),
            'click_share': row.get('click_share', None),
            'conversion_share': row.get('conversion_share', None),
        }
        if is_brand:
            item['brand'] = brand_name
            brand_keywords.append(item)
        else:
            non_brand_keywords.append(item)
    
    # 提取修饰词
    all_modifiers = []
    for item in non_brand_keywords:
        modifiers = extract_modifiers(item['search_term'])
        all_modifiers.extend(modifiers)
    
    modifier_counts = Counter(all_modifiers)
    
    # Top品牌
    top_brands = Counter()
    for item in brand_keywords:
        if item.get('brand'):
            top_brands[item['brand']] += 1
    
    # Top ASIN
    top_asins = Counter()
    if 'top_clicked_product_asin' in df_clean.columns:
        asin_data = df_clean[df_clean['top_clicked_product_asin'].notna()]
        for _, row in asin_data.iterrows():
            asin = str(row['top_clicked_product_asin']).strip()
            if asin and asin != 'nan':
                top_asins[asin] += 1
    
    # 统计
    avg_click_share = df_clean['click_share'].mean() if 'click_share' in df_clean.columns else None
    avg_conversion_share = df_clean['conversion_share'].mean() if 'conversion_share' in df_clean.columns else None
    
    # 类目识别
    keywords = df_clean['search_term'].astype(str).tolist()
    titles = df_clean['product_title'].astype(str).tolist() if 'product_title' in df_clean.columns else []
    detected_category = detect_category(keywords, titles)
    
    return {
        'total_keywords': len(df_clean),
        'brand_count': len(brand_keywords),
        'non_brand_count': len(non_brand_keywords),
        'avg_click_share': avg_click_share,
        'avg_conversion_share': avg_conversion_share,
        'top_modifiers': modifier_counts.most_common(20),
        'top_brands': top_brands.most_common(20),
        'top_asins': top_asins.most_common(20),
        'non_brand_keywords': non_brand_keywords,
        'brand_keywords': brand_keywords,
        'detected_category': detected_category,
        'all_keywords': df_clean.to_dict('records')
    }
