"""
ABA利基分析工具 v5.0 - 10维评分模块（兼容v4.0）
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class ScoringEngine:
    """10维评分引擎"""
    
    DIMENSIONS = [
        "市场规模",
        "转化潜力",
        "竞争强度",
        "成长性",
        "利润空间",
        "品牌垄断",
        "新品存活率",
        "卖点接受度",
        "价格弹性",
        "季节性"
    ]
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.scores = {}
    
    def calculate_all(self) -> Dict[str, float]:
        """计算所有维度评分（0-100）"""
        self.scores = {
            "市场规模": self._score_market_size(),
            "转化潜力": self._score_conversion(),
            "竞争强度": self._score_competition(),
            "成长性": self._score_growth(),
            "利润空间": self._score_profit(),
            "品牌垄断": self._score_brand_concentration(),
            "新品存活率": self._score_new_product_survival(),
            "卖点接受度": self._score_usp_acceptance(),
            "价格弹性": self._score_price_elasticity(),
            "季节性": self._score_seasonality(),
        }
        return self.scores
    
    def _score_market_size(self) -> float:
        total_sales = self.df["monthly_sales"].sum() if "monthly_sales" in self.df.columns else 0
        return min(100, total_sales / 1000)
    
    def _score_conversion(self) -> float:
        avg_rating = self.df["rating"].mean() if "rating" in self.df.columns else 0
        return avg_rating * 20
    
    def _score_competition(self) -> float:
        review_count = self.df["review_count"].mean() if "review_count" in self.df.columns else 0
        return max(0, 100 - min(100, review_count / 10))
    
    def _score_growth(self) -> float:
        return 50
    
    def _score_profit(self) -> float:
        avg_price = self.df["price"].mean() if "price" in self.df.columns else 0
        return min(100, avg_price * 2)
    
    def _score_brand_concentration(self) -> float:
        return 50
    
    def _score_new_product_survival(self) -> float:
        return 50
    
    def _score_usp_acceptance(self) -> float:
        return 50
    
    def _score_price_elasticity(self) -> float:
        return 50
    
    def _score_seasonality(self) -> float:
        return 50
    
    def get_summary(self) -> Dict[str, Any]:
        """获取评分摘要"""
        if not self.scores:
            self.calculate_all()
        
        return {
            "scores": self.scores,
            "total": sum(self.scores.values()),
            "average": sum(self.scores.values()) / len(self.scores),
            "top_dimensions": sorted(self.scores.items(), key=lambda x: x[1], reverse=True)[:3],
            "bottom_dimensions": sorted(self.scores.items(), key=lambda x: x[1])[:3],
        }
