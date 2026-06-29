"""
评论挖掘模块
"""

from typing import Dict, Any, List
import pandas as pd
from collections import Counter, defaultdict
import re


POSITIVE_WORDS = {
    '好', '棒', '赞', '喜欢', '满意', '推荐', '值得', '不错', '优秀',
    ' amazing', 'great', 'good', 'excellent', 'perfect', 'best', 'love', 'like',
    'recommend', 'satisfied', 'happy', 'wonderful', 'awesome', 'fantastic'
}

NEGATIVE_WORDS = {
    '差', '坏', '烂', '失望', '遗憾', '后悔', '垃圾', '不行', '不好',
    ' bad', 'poor', 'terrible', 'awful', 'horrible', 'disappointed', 'regret',
    'waste', 'broken', 'defective', 'issue', 'problem'
}

MODIFIER_KEYWORDS = {
    "降噪": ["noise", "降噪", "安静", "耳压", "anc"],
    "防水": ["waterproof", "water", "防水", "防泼水", "ipx"],
    "快充": ["fast", "quick", "rapid", "快充", "闪充", "charging"],
    "无线": ["wireless", "bluetooth", "蓝牙", "无线", "连接"],
    "舒适": ["comfort", "舒适", "舒服", "柔软", "轻", "soft"],
    "耐用": ["durable", "耐用", "结实", "耐磨", "sturdy"],
    "便携": ["portable", "compact", "便携", "轻便", "折叠"],
    "音质": ["sound", "bass", "音质", "音效", "清晰", "audio"],
    "续航": ["battery", "续航", "耗电", "耐用", "电量"],
    "外观": ["design", "style", "外观", "颜值", "好看", "漂亮"],
}


def analyze_comments(review_df: pd.DataFrame, asin_df: pd.DataFrame = None) -> List[Dict[str, Any]]:
    """分析评论数据"""
    
    if review_df is None or review_df.empty:
        return []
    
    results = []
    
    for asin, group in review_df.groupby('asin'):
        if len(group) < 50:
            continue
        
        if len(group) > 500:
            depth = "⭐⭐⭐ 深度分析"
        elif len(group) > 200:
            depth = "⭐⭐ 标准分析"
        else:
            depth = "⭐ 快速扫描"
        
        texts = group['review_body'].astype(str).tolist()
        ratings = group['rating'].tolist()
        
        positive_count = 0
        negative_count = 0
        
        for text in texts:
            text_lower = text.lower()
            pos_score = sum(1 for w in POSITIVE_WORDS if w in text_lower)
            neg_score = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
        
        modifier_mentions = defaultdict(int)
        for text in texts:
            text_lower = text.lower()
            for modifier, keywords in MODIFIER_KEYWORDS.items():
                for kw in keywords:
                    if kw in text_lower:
                        modifier_mentions[modifier] += 1
                        break
        
        all_words = re.findall(r'[a-zA-Z\u4e00-\u9fa5]{2,}', ' '.join(texts).lower())
        word_counts = Counter(all_words)
        
        negative_texts = [t for t, r in zip(texts, ratings) if r <= 3]
        if negative_texts:
            neg_words = re.findall(r'[a-zA-Z\u4e00-\u9fa5]{2,}', ' '.join(negative_texts).lower())
            neg_counts = Counter(neg_words)
            top_pains = [w for w, c in neg_counts.most_common(10) if c > 2 and len(w) > 1]
        else:
            top_pains = []
        
        positive_texts = [t for t, r in zip(texts, ratings) if r >= 4]
        if positive_texts:
            pos_words = re.findall(r'[a-zA-Z\u4e00-\u9fa5]{2,}', ' '.join(positive_texts).lower())
            pos_counts = Counter(pos_words)
            top_praises = [w for w, c in pos_counts.most_common(10) if c > 2 and len(w) > 1]
        else:
            top_praises = []
        
        suggestions = generate_suggestions(modifier_mentions, top_pains, top_praises, len(group))
        
        results.append({
            'asin': asin,
            'review_count': len(group),
            'depth': depth,
            'avg_rating': round(sum(ratings) / len(ratings), 2),
            'positive_ratio': round(positive_count / len(group) * 100, 1) if group else 0,
            'top_modifiers': dict(modifier_mentions.most_common(5)),
            'top_pains': top_pains[:5],
            'top_praises': top_praises[:5],
            'suggestions': suggestions
        })
    
    return results


def generate_suggestions(modifier_mentions: dict, pains: list, praises: list, total: int) -> dict:
    """生成优化建议"""
    
    suggestions = {
        'product': [],
        'listing': [],
        'advertising': [],
        'urgent': []
    }
    
    total_mentions = sum(modifier_mentions.values()) if modifier_mentions else 1
    for modifier, count in modifier_mentions.items():
        ratio = count / total
        if ratio > 0.3:
            suggestions['product'].append(f"优化{modifier}功能，用户关注度高")
    
    if praises:
        suggestions['listing'].append(f"在标题/五点中突出: {', '.join(praises[:3])}")
    
    if pains:
        suggestions['advertising'].append(f"针对痛点'{pains[0]}'制作对比广告")
    
    if pains:
        suggestions['urgent'].append(f"重点关注: {', '.join(pains[:2])}")
    
    return suggestions
