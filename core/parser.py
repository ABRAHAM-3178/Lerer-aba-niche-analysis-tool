"""
ABA CSV 解析器（支持中文多列格式 + 全类目词库）
包含 extract_modifiers, get_modifier_category 等所有必需函数
"""

import pandas as pd
import re
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple, Set

from utils.constants import (
    CATEGORY_KEYWORDS,
    BRAND_SUFFIXES,
    BRAND_PATTERNS,
    STOP_WORDS,
    GENERIC_BASE_WORDS,
    MODIFIER_CATEGORIES
)


def detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """自动检测列名映射（支持中英文 + 模糊匹配）"""
    cols = df.columns.tolist()
    mapping = {}
    
    possible_mappings = {
        'search_term': ['Search Term', 'Search Term (Customer Search Term)', 
                       'Customer Search Term', 'Keyword', 'search_term', '关键词', '搜索词', '搜索关键词'],
        'search_frequency_rank': ['Search Frequency Rank', 'Search Rank',
                                 'Frequency Rank', 'search_frequency_rank', 'Rank', '排名', '搜索频率排名', '频率排名', '搜索排名'],
        'top_clicked_brand': ['Top Clicked Brand', 'Top Brand',
                             'top_clicked_brand', 'Brand', '品牌', '热门点击品牌'],
        'top_clicked_category': ['Top Clicked Category', 'Category',
                                'top_clicked_category', '类目', '热门点击类目'],
        'top_clicked_product_asin': ['Top Clicked Product ASIN', 'Top ASIN',
                                    'top_clicked_product_asin', 'ASIN', '热门点击ASIN'],
        'product_title': ['Product Title', 'Title', 'product_title', '标题', '产品标题', '商品标题'],
        'click_share': ['Click Share', 'Click %', 'click_share', '点击份额', '点击量占比', '点击量份额'],
        'conversion_share': ['Conversion Share', 'Conversion %', 'conversion_share', '转化份额', '转化量占比', '转化贡献占比'],
    }
    
    for std_name, possible in possible_mappings.items():
        for p in possible:
            for col in cols:
                if col.strip() == p:
                    mapping[std_name] = col
                    break
            if std_name in mapping:
                break
    
    # 模糊匹配（兜底）
    if 'search_term' not in mapping:
        for col in cols:
            col_clean = col.strip()
            if '搜索' in col_clean and '词' in col_clean:
                mapping['search_term'] = col
                break
            if 'search' in col_clean.lower() and 'term' in col_clean.lower():
                mapping['search_term'] = col
                break
    
    if 'search_frequency_rank' not in mapping:
        for col in cols:
            col_clean = col.strip()
            if '搜索' in col_clean and '排名' in col_clean:
                mapping['search_frequency_rank'] = col
                break
            if 'search' in col_clean.lower() and 'rank' in col_clean.lower():
                mapping['search_frequency_rank'] = col
                break
    
    if 'click_share' not in mapping:
        for col in cols:
            col_clean = col.strip()
            if '点击' in col_clean and '份额' in col_clean:
                mapping['click_share'] = col
                break
            if 'click' in col_clean.lower() and 'share' in col_clean.lower():
                mapping['click_share'] = col
                break
    
    if 'conversion_share' not in mapping:
        for col in cols:
            col_clean = col.strip()
            if '转化' in col_clean and '份额' in col_clean:
                mapping['conversion_share'] = col
                break
            if 'conversion' in col_clean.lower() and 'share' in col_clean.lower():
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


def is_brand_keyword(term: str) -> Tuple[bool, Optional[str]]:
    """判断是否为品牌词"""
    term_lower = term.lower().strip()
    for brand in BRAND_SUFFIXES:
        if brand in term_lower:
            return True, brand
    for pattern in BRAND_PATTERNS:
        if re.search(pattern, term_lower):
            return True, re.search(pattern, term_lower).group()
    return False, None


def extract_modifiers(term: str, category_base_words: Optional[Set[str]] = None) -> List[str]:
    """提取修饰词"""
    import re
    from utils.constants import STOP_WORDS, GENERIC_BASE_WORDS
    
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
    """将修饰词归类到卖点类别"""
    from utils.constants import MODIFIER_CATEGORIES
    
    modifier_lower = modifier.lower()
    for category, keywords in MODIFIER_CATEGORIES.items():
        for kw in keywords:
            if kw in modifier_lower:
                return category
    return "其他"


def parse_chinese_multi_asin_file(df: pd.DataFrame) -> pd.DataFrame:
    """解析中文多列 ASIN 格式的 ABA 文件"""
    import pandas as pd
    
    df.columns = df.columns.str.strip()
    print("🔍 实际列名:", df.columns.tolist())
    
    def find_column(patterns: List[str], fallback_pattern: str = None) -> Optional[str]:
        for col in df.columns:
            col_clean = col.strip()
            if all(p in col_clean for p in patterns):
                return col
        if fallback_pattern:
            for col in df.columns:
                col_clean = col.strip()
                if fallback_pattern in col_clean:
                    return col
        return None
    
    search_term_col = find_column(['搜索词'], '搜索词')
    search_rank_col = find_column(['搜索频率排名'], '排名') or find_column(['频率排名'], '排名')
    
    asin_1_col = find_column(['点击量第1的商品', 'ASIN'], 'ASIN')
    brand_1_col = find_column(['点击量第1的品牌'], '品牌')
    category_1_col = find_column(['点击量最高的分类'], '分类')
    title_1_col = find_column(['点击量第1的商品', '商品标题'], '标题')
    click_1_col = find_column(['点击量最高的商品', '点击份额'], '点击份额')
    conv_1_col = find_column(['点击量第1的商品', '转化贡献占比'], '转化贡献')
    
    asin_2_col = find_column(['点击量第2的商品', 'ASIN'], 'ASIN')
    brand_2_col = find_column(['点击量第2的品牌'], '品牌')
    category_2_col = find_column(['点击量第二的分类'], '分类')
    title_2_col = find_column(['点击量第2的商品', '商品标题'], '标题')
    click_2_col = find_column(['点击量第二的商品', '点击份额'], '点击份额')
    conv_2_col = find_column(['热门点击商品第2名', '转化贡献占比'], '转化贡献')
    
    asin_3_col = find_column(['点击量第三的商品', 'ASIN'], 'ASIN')
    brand_3_col = find_column(['点击量第3的品牌'], '品牌')
    category_3_col = find_column(['点击量第 3 的分类'], '分类')
    title_3_col = find_column(['点击量第3的商品', '商品标题'], '标题')
    click_3_col = find_column(['点击量第三的商品', '点击份额'], '点击份额')
    conv_3_col = find_column(['点击量第3的商品', '转化贡献占比'], '转化贡献')
    
    if not search_term_col:
        raise ValueError("未找到 '搜索词' 列")
    if not search_rank_col:
        raise ValueError("未找到 '搜索频率排名' 列")
    
    print(f"✅ 搜索词列: {search_term_col}")
    print(f"✅ 排名列: {search_rank_col}")
    print(f"✅ 第1名ASIN列: {asin_1_col}")
    print(f"✅ 第2名ASIN列: {asin_2_col}")
    print(f"✅ 第3名ASIN列: {asin_3_col}")
    
    df[search_rank_col] = pd.to_numeric(df[search_rank_col], errors='coerce')
    
    rows = []
    for _, row in df.iterrows():
        search_term = row.get(search_term_col, '') if search_term_col else ''
        search_rank = row.get(search_rank_col, None) if search_rank_col else None
        
        if asin_1_col and pd.notna(row.get(asin_1_col)) and str(row.get(asin_1_col)).strip():
            rows.append({
                "searchTerm": str(search_term),
                "searchFrequencyRank": search_rank,
                "clickedAsin": str(row.get(asin_1_col, '')).strip(),
                "clickedBrand": str(row.get(brand_1_col, '')).strip() if brand_1_col else '',
                "clickedCategory": str(row.get(category_1_col, '')).strip() if category_1_col else '',
                "productTitle": str(row.get(title_1_col, '')).strip() if title_1_col else '',
                "clickShare": float(row.get(click_1_col, 0)) if click_1_col and pd.notna(row.get(click_1_col)) else 0,
                "conversionShare": float(row.get(conv_1_col, 0)) if conv_1_col and pd.notna(row.get(conv_1_col)) else 0,
                "rankPosition": 1
            })
        
        if asin_2_col and pd.notna(row.get(asin_2_col)) and str(row.get(asin_2_col)).strip():
            rows.append({
                "searchTerm": str(search_term),
                "searchFrequencyRank": search_rank,
                "clickedAsin": str(row.get(asin_2_col, '')).strip(),
                "clickedBrand": str(row.get(brand_2_col, '')).strip() if brand_2_col else '',
                "clickedCategory": str(row.get(category_2_col, '')).strip() if category_2_col else '',
                "productTitle": str(row.get(title_2_col, '')).strip() if title_2_col else '',
                "clickShare": float(row.get(click_2_col, 0)) if click_2_col and pd.notna(row.get(click_2_col)) else 0,
                "conversionShare": float(row.get(conv_2_col, 0)) if conv_2_col and pd.notna(row.get(conv_2_col)) else 0,
                "rankPosition": 2
            })
        
        if asin_3_col and pd.notna(row.get(asin_3_col)) and str(row.get(asin_3_col)).strip():
            rows.append({
                "searchTerm": str(search_term),
                "searchFrequencyRank": search_rank,
                "clickedAsin": str(row.get(asin_3_col, '')).strip(),
                "clickedBrand": str(row.get(brand_3_col, '')).strip() if brand_3_col else '',
                "clickedCategory": str(row.get(category_3_col, '')).strip() if category_3_col else '',
                "productTitle": str(row.get(title_3_col, '')).strip() if title_3_col else '',
                "clickShare": float(row.get(click_3_col, 0)) if click_3_col and pd.notna(row.get(click_3_col)) else 0,
                "conversionShare": float(row.get(conv_3_col, 0)) if conv_3_col and pd.notna(row.get(conv_3_col)) else 0,
                "rankPosition": 3
            })
    
    if not rows:
        raise ValueError("未能从文件中提取任何有效 ASIN 数据")
    
    return pd.DataFrame(rows)


def parse_aba_csv(df: pd.DataFrame) -> Dict[str, Any]:
    """解析 ABA 数据"""
    if df is None:
        return {"error": "未提供ABA数据"}
    
    df.columns = df.columns.str.strip() if hasattr(df.columns, 'str') else df.columns
    
    has_chinese_format = False
    for col in df.columns:
        col_clean = col.strip() if isinstance(col, str) else str(col)
        if '搜索词' in col_clean:
            for col2 in df.columns:
                col2_clean = col2.strip() if isinstance(col2, str) else str(col2)
                if '点击量第1的商品' in col2_clean or '点击量第1' in col2_clean:
                    has_chinese_format = True
                    break
        if has_chinese_format:
            break
    
    if has_chinese_format:
        print("🔍 检测到中文多列格式，正在转换为标准ABA格式...")
        df = parse_chinese_multi_asin_file(df)
        print(f"✅ 转换完成，共 {len(df)} 行")
    
    col_mapping = detect_columns(df)
    rename_map = {v: k for k, v in col_mapping.items() if v}
    df_clean = df.rename(columns=rename_map)
    
    if 'search_term' not in df_clean.columns:
        return {"error": "无法找到Search Term列"}
    
    df_clean = df_clean.dropna(subset=['search_term'])
    df_clean = df_clean[df_clean['search_term'].astype(str).str.strip() != '']
    df_clean = df_clean.reset_index(drop=True)
    
    if 'search_frequency_rank' in df_clean.columns:
        df_clean['search_frequency_rank'] = pd.to_numeric(df_clean['search_frequency_rank'], errors='coerce')
    
    for col in ['click_share', 'conversion_share']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.replace('%', '')
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
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
    
    all_modifiers = []
    for item in non_brand_keywords:
        modifiers = extract_modifiers(item['search_term'])
        all_modifiers.extend(modifiers)
    
    modifier_counts = Counter(all_modifiers)
    
    top_brands = Counter()
    for item in brand_keywords:
        if item.get('brand'):
            top_brands[item['brand']] += 1
    
    top_asins = Counter()
    if 'clickedAsin' in df_clean.columns:
        asin_data = df_clean[df_clean['clickedAsin'].notna()]
        for _, row in asin_data.iterrows():
            asin = str(row['clickedAsin']).strip()
            if asin and asin != 'nan':
                top_asins[asin] += 1
    elif 'top_clicked_product_asin' in df_clean.columns:
        asin_data = df_clean[df_clean['top_clicked_product_asin'].notna()]
        for _, row in asin_data.iterrows():
            asin = str(row['top_clicked_product_asin']).strip()
            if asin and asin != 'nan':
                top_asins[asin] += 1
    
    avg_click_share = df_clean['click_share'].mean() if 'click_share' in df_clean.columns else None
    avg_conversion_share = df_clean['conversion_share'].mean() if 'conversion_share' in df_clean.columns else None
    
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
