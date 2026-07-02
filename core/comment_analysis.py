"""
ABA利基分析工具 v5.0 - 评论分析模块（痛点挖掘）
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import Counter
import re
from dataclasses import dataclass


@dataclass
class PainPoint:
    keyword: str
    mention_count: int
    mention_rate: float
    sample_reviews: List[str]
    suggested_solution: Optional[str] = None


class CommentAnalyzer:
    """评论分析器 - 专注于痛点挖掘"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    def extract_pain_points(self, reviews_df: pd.DataFrame, min_mentions: int = 3) -> List[PainPoint]:
        """从1-3星评论中提取痛点"""
        if "review_star" in reviews_df.columns:
            low_rating = reviews_df[reviews_df["review_star"] <= 3]
        else:
            low_rating = reviews_df
        
        if len(low_rating) == 0:
            return []
        
        bodies = low_rating["review_body"].dropna().tolist()
        total_comments = len(bodies)
        
        if total_comments == 0:
            return []
        
        pain_patterns = self._extract_patterns(bodies)
        
        pain_counts = Counter()
        for body in bodies:
            body_lower = body.lower()
            for pattern in pain_patterns:
                if pattern.lower() in body_lower:
                    pain_counts[pattern] += 1
        
        pain_points = []
        for keyword, count in pain_counts.most_common(20):
            if count >= min_mentions:
                sample_reviews = []
                for body in bodies:
                    if keyword.lower() in body.lower() and len(sample_reviews) < 3:
                        sample_reviews.append(body[:200] + "..." if len(body) > 200 else body)
                
                pain_points.append(PainPoint(
                    keyword=keyword,
                    mention_count=count,
                    mention_rate=count / total_comments if total_comments > 0 else 0,
                    sample_reviews=sample_reviews,
                    suggested_solution=None
                ))
        
        return pain_points
    
    def _extract_patterns(self, bodies: List[str]) -> List[str]:
        """提取常见痛点模式"""
        keywords = [
            "broken", "cracked", "bent", "wobbly", "unstable", "loose",
            "damaged", "scratch", "dent", "chip", "rust", "corrosion",
            "thin", "flimsy", "cheap material", "low quality",
            "not work", "doesn't work", "failed", "stop working", "dead",
            "noise", "loud", "squeaky", "creaky", "clicking",
            "slow", "stuck", "jam", "blocked", "leak",
            "missing part", "missing screw", "wrong size", "wrong color",
            "hard to assemble", "difficult to install", "instructions unclear",
            "uncomfortable", "not fit", "too small", "too large", "too heavy",
            "not stable", "tips over", "falls over",
        ]
        
        patterns = []
        for keyword in keywords:
            patterns.append(keyword)
            patterns.append(f"it {keyword}")
            patterns.append(f"was {keyword}")
            patterns.append(f"is {keyword}")
        
        return patterns
