"""
AI语义聚类模块（支持AI + 本地回退）
"""

from collections import defaultdict
from typing import Dict, List, Any
from utils.constants import MODIFIER_CATEGORIES
from .parser import extract_modifiers, get_modifier_category


def semantic_clustering(aba_result: Dict[str, Any], category: str = "",
                        use_ai: bool = False, api_key: str = None,
                        model: str = None, base_url: str = None) -> List[Dict[str, Any]]:
    """
    对非品牌关键词进行语义聚类（支持AI模式）
    """
    non_brand = aba_result.get('non_brand_keywords', [])
    
    if not non_brand:
        return []
    
    # ===== AI 模式 =====
    if use_ai and api_key:
        try:
            from utils.ai_client import AIClient
            from utils.prompts import build_clustering_messages
            
            keywords = [item.get('search_term', '') for item in non_brand[:100]]
            client = AIClient(api_key=api_key, model=model, base_url=base_url)
            messages = build_clustering_messages(keywords)
            result = client.chat_json(messages)
            
            clusters = []
            for cluster in result.get("clusters", []):
                cluster_keywords = cluster.get("keywords", [])
                items = []
                for kw in cluster_keywords:
                    for item in non_brand:
                        if item.get('search_term') == kw:
                            items.append(item)
                            break
                if items:
                    ranks = [i.get('search_frequency_rank', 999999) for i in items if i.get('search_frequency_rank')]
                    click_shares = [i.get('click_share', 0) for i in items if i.get('click_share')]
                    conversion_shares = [i.get('conversion_share', 0) for i in items if i.get('conversion_share')]
                    clusters.append({
                        'name': cluster.get('name', '未知'),
                        'keyword_count': len(items),
                        'avg_rank': sum(ranks) / len(ranks) if ranks else 999999,
                        'avg_click_share': sum(click_shares) / len(click_shares) if click_shares else 0,
                        'avg_conversion_share': sum(conversion_shares) / len(conversion_shares) if conversion_shares else 0,
                        'keywords': [i.get('search_term', '') for i in items[:10]],
                        'items': items,
                        'ai_generated': True
                    })
            if clusters:
                return sorted(clusters, key=lambda x: x['keyword_count'], reverse=True)
        except Exception as e:
            print(f"⚠️ AI 聚类失败，回退到本地词库: {e}")
    
    # ===== 本地词库聚类（回退） =====
    clusters = defaultdict(list)
    
    for item in non_brand:
        term = item.get('search_term', '')
        modifiers = extract_modifiers(term)
        
        for mod in modifiers:
            cat = get_modifier_category(mod)
            if cat != "其他":
                clusters[cat].append(item)
            else:
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
            'items': items,
            'ai_generated': False
        })
    
    result.sort(key=lambda x: x['keyword_count'], reverse=True)
    return result
