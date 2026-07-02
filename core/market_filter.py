"""
ABA利基分析工具 v5.0 - 市场准入过滤器（路线二）
"""

import yaml
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FilterResult:
    name: str
    value: float
    threshold: float
    passed: bool
    message: str


@dataclass
class MarketFilterResult:
    passed: bool
    indicators: List[FilterResult]
    summary: str
    recommendation: str


class MarketFilter:
    """市场准入过滤器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        self.config = config.get("market_filter", {})
        self.thresholds = {
            "min_monthly_sales": self.config.get("min_monthly_sales", 30000),
            "min_avg_price": self.config.get("min_avg_price", 20.0),
            "max_avg_review_count": self.config.get("max_avg_review_count", 500),
            "max_brand_concentration": self.config.get("max_brand_concentration", 0.60),
        }
    
    def filter_class(self, df: pd.DataFrame) -> MarketFilterResult:
        """执行市场过滤"""
        indicators = []
        
        top_100_sales = df["monthly_sales"].sum() if "monthly_sales" in df.columns else 0
        passed_1 = top_100_sales >= self.thresholds["min_monthly_sales"]
        indicators.append(FilterResult(
            name="市场容积",
            value=top_100_sales,
            threshold=self.thresholds["min_monthly_sales"],
            passed=passed_1,
            message=f"Top 100月销量总和: {top_100_sales:,.0f}件"
        ))
        
        avg_price = df["price"].mean() if "price" in df.columns else 0
        passed_2 = avg_price >= self.thresholds["min_avg_price"]
        indicators.append(FilterResult(
            name="客单价",
            value=avg_price,
            threshold=self.thresholds["min_avg_price"],
            passed=passed_2,
            message=f"平均客单价: ${avg_price:.2f}"
        ))
        
        avg_reviews = df["review_count"].mean() if "review_count" in df.columns else 0
        passed_3 = avg_reviews <= self.thresholds["max_avg_review_count"]
        indicators.append(FilterResult(
            name="评论壁垒",
            value=avg_reviews,
            threshold=self.thresholds["max_avg_review_count"],
            passed=passed_3,
            message=f"平均评论数: {avg_reviews:.0f}"
        ))
        
        if "brand" in df.columns:
            brand_sales = df.groupby("brand")["monthly_sales"].sum().sort_values(ascending=False)
            top_10_brand_sales = brand_sales.head(10).sum()
            brand_concentration = top_10_brand_sales / df["monthly_sales"].sum() if df["monthly_sales"].sum() > 0 else 1.0
        else:
            brand_concentration = 0.5
        passed_4 = brand_concentration <= self.thresholds["max_brand_concentration"]
        indicators.append(FilterResult(
            name="品牌垄断度",
            value=brand_concentration,
            threshold=self.thresholds["max_brand_concentration"],
            passed=passed_4,
            message=f"Top 10品牌市占率: {brand_concentration:.1%}"
        ))
        
        all_passed = all([i.passed for i in indicators])
        if all_passed:
            recommendation = "✅ 准入 - 该市场符合蓝海/偏蓝海特征，建议进入路线一深度分析"
        else:
            failed_names = [i.name for i in indicators if not i.passed]
            recommendation = f"❌ 淘汰 - 以下指标未达标: {', '.join(failed_names)}"
        
        return MarketFilterResult(
            passed=all_passed,
            indicators=indicators,
            summary="所有指标均已达标" if all_passed else f"有 {len([i for i in indicators if not i.passed])} 项指标未达标",
            recommendation=recommendation
        )
    
    def update_thresholds(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.thresholds:
                self.thresholds[key] = value
