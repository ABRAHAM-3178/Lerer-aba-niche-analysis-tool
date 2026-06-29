"""
AI语义聚类模块
"""

from collections import defaultdict
from typing import Dict, List, Any
from utils.constants import MODIFIER_CATEGORIES
from .parser import extract_modifiers, get_modifier_category


def semantic_clustering(aba_result: Dict[str, Any], category: str = "") -> List[Dict[str, Any]]:
    """对非品牌关键词进行语义聚类"""
    
    non_brand = aba_result.get('non_brand_keywords', [])
    
    if not non_brand:
        return []
    
    # 按修饰词聚类
    clusters = defaultdict(list)
    
    for item in non_brand:
        term = item.get('search_term', '')
        modifiers = extract_modifiers(term)
        
        for mod in modifiers:
            cat = get_modifier_category(mod)
            if cat != "其他":
                clusters[cat].append(item)
            else:
                # 尝试匹配子类别
                for category_name, keywords in MODIFIER_CATEGORIES.items():
                    for kw in keywords:
                        if kw in mod:
                            clusters[category_name].append(item)
                            break
                    if item in clusters[category_name]:
                        break
    
    # 如果没有聚类结果，按高频词聚类
    if len(clusters) == 0:
        top_mods = aba_result.get('top_modifiers', [])[:5]
        for mod, _ in top_mods:
            for item in non_brand:
                if mod in item.get('search_term', '').lower():
                    clusters[f"🔍 {mod}相关"].append(item)
    
    # 计算每个簇的统计信息
    result = []
    for cluster_name, items in clusters.items():
        if len(items) < 2:
            continue
        
        ranks = [i.get('search_frequency_rank', 999999) for i in items if i.get('search_frequency_rank')]
        click_shares = [i.get('click_share', 0) for i in items if i.get('click_share')]
        conversion_shares = [i.get('conversion_share', 0) for i in items if i.get('conversion_share')]
        
        result.append({
            'name': cluster_name,
            'keyword_count': len(items),
            'avg_rank': sum(ranks) / len(ranks) if ranks else 999999,
            'avg_click_share': sum(click_shares) / len(click_shares) if click_shares else 0,
            'avg_conversion_share': sum(conversion_shares) / len(conversion_shares) if conversion_shares else 0,
            'keywords': [i.get('search_term', '') for i in items[:10]],
            'items': items
        })
    
    # 按关键词数量排序
    result.sort(key=lambda x: x['keyword_count'], reverse=True)
    
    return result
