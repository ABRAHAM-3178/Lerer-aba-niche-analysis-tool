"""
ABA利基分析工具 v5.0 - 评论分析模块（增强版）
功能：1-3星差评痛点挖掘 + 提及率计算 + AI总结
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from collections import Counter
import re
from dataclasses import dataclass

@dataclass
class PainPoint:
    """痛点数据结构"""
    keyword: str
    mention_count: int
    mention_rate: float  # 提及率（提及次数/总评论数）
    sample_reviews: List[str]  # 代表性评论样本
    suggested_solution: Optional[str] = None  # AI建议的解决方案


class CommentAnalyzer:
    """评论分析器 - 专注于痛点挖掘"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        
        # 停用词：过滤掉主观情绪词
        self.stopwords = {
            "disappointed", "disappointing", "terrible", "awful", "horrible",
            "very", "really", "extremely", "absolutely", "completely",
            "so", "too", "much", "more", "less", "just", "even", "then", "than"
        }
    
    def extract_pain_points(self, reviews_df: pd.DataFrame, 
                           min_mentions: int = 3) -> List[PainPoint]:
        """
        从1-3星评论中提取痛点
        
        Args:
            reviews_df: 需包含 review_star, review_body 列
            min_mentions: 痛点的最低提及次数
        
        Returns:
            按提及率降序排列的痛点列表
        """
        # 筛选1-3星评论
        low_rating = reviews_df[reviews_df["review_star"] <= 3]
        
        if len(low_rating) == 0:
            return []
        
        # 提取所有评论正文
        bodies = low_rating["review_body"].dropna().tolist()
        total_comments = len(bodies)
        
        # 提取名词短语和动宾结构（简化版：用标点和关键词分割）
        pain_patterns = self._extract_patterns(bodies)
        
        # 统计提及次数
        pain_counts = Counter()
        for body in bodies:
            body_lower = body.lower()
            for pattern in pain_patterns:
                if pattern.lower() in body_lower:
                    pain_counts[pattern] += 1
        
        # 构建痛点列表
        pain_points = []
        for keyword, count in pain_counts.most_common(20):
            if count >= min_mentions:
                # 找到代表性评论
                sample_reviews = []
                for body in bodies:
                    if keyword.lower() in body.lower() and len(sample_reviews) < 3:
                        sample_reviews.append(body[:200] + "..." if len(body) > 200 else body)
                
                pain_points.append(PainPoint(
                    keyword=keyword,
                    mention_count=count,
                    mention_rate=count / total_comments if total_comments > 0 else 0,
                    sample_reviews=sample_reviews,
                    suggested_solution=None  # 后续调用AI生成
                ))
        
        return pain_points
    
    def _extract_patterns(self, bodies: List[str]) -> List[str]:
        """从评论中提取常见痛点模式"""
        patterns = []
        
        # 常见痛点关键词
        keywords = [
            # 物理缺陷
            "broken", "cracked", "bent", "wobbly", "unstable", "loose", 
            "damaged", "scratch", "dent", "chip", "rust", "corrosion",
            "thin", "flimsy", "cheap material", "low quality",
            # 功能问题
            "not work", "doesn't work", "failed", "stop working", "dead",
            "noise", "loud", "squeaky", "creaky", "clicking",
            "slow", "stuck", "jam", "blocked", "leak",
            # 配件问题
            "missing part", "missing screw", "wrong size", "wrong color",
            "hard to assemble", "difficult to install", "instructions unclear",
            # 舒适度/体验
            "uncomfortable", "not fit", "too small", "too large", "too heavy",
            "not stable", "tips over", "falls over",
        ]
        
        for keyword in keywords:
            patterns.append(keyword)
            patterns.append(f"it {keyword}")  # "it broke"
            patterns.append(f"was {keyword}")  # "was broken"
            patterns.append(f"is {keyword}")   # "is broken"
        
        return patterns
    
    def generate_ai_solutions(self, pain_points: List[PainPoint], 
                              ai_client, product_name: str = "该产品") -> List[PainPoint]:
        """调用AI为每个痛点生成改良建议"""
        for pp in pain_points:
            if pp.mention_rate < 0.05:  # 提及率低于5%的不需要AI建议
                continue
            
            prompt = f"""
            你是一位资深产品开发专家。以下是消费者对【{product_name}】的差评中提及的痛点：
            
            痛点：{pp.keyword}
            提及次数：{pp.mention_count}
            提及率：{pp.mention_rate:.1%}
            
            代表性评论样例：
            {chr(10).join(['- ' + s for s in pp.sample_reviews[:2]])}
            
            请给出2-3条具体的、可落地的产品改良建议（如：改用XX材质、增加XX结构、优化XX设计），
            每条建议控制在30字以内。
            """
            
            try:
                response = ai_client.chat(prompt, temperature=0.7)
                pp.suggested_solution = response.strip()
            except Exception as e:
                pp.suggested_solution = f"AI建议生成失败: {e}"
        
        return pain_points
