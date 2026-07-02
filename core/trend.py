"""
ABA利基分析工具 v5.0 - 趋势分析
功能：计算季度环比（QoQ）、判断市场生命周期
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, growth_threshold: float = 0.15, decline_threshold: float = -0.05, stable_threshold: float = 0.05):
        self.growth_threshold = growth_threshold
        self.decline_threshold = decline_threshold
        self.stable_threshold = stable_threshold
    
    def calculate_qoq(self, series: pd.Series) -> pd.Series:
        """计算季度环比增长率"""
        return series.pct_change() * 100
    
    def classify_trend(self, qoq_values: List[float]) -> str:
        """
        根据连续季度的QoQ判断趋势类型
        - "红利期": 连续2个季度增长 > 15%
        - "衰退期": 连续2个季度下滑 > 5%
        - "常青款": 波动在 ±5% 以内
        - "波动期": 其他情况
        """
        if len(qoq_values) < 2:
            return "数据不足"
        
        last_two = qoq_values[-2:]
        if all(v > self.growth_threshold * 100 for v in last_two):
            return "红利期（高速增长）"
        elif all(v < self.decline_threshold * 100 for v in last_two):
            return "衰退期（持续下滑）"
        elif all(abs(v) < self.stable_threshold * 100 for v in last_two):
            return "常青款（稳定市场）"
        else:
            return "波动期（需谨慎）"
    
    def analyze_sales_trend(self, df: pd.DataFrame, date_col: str, sales_col: str, group_col: Optional[str] = None) -> Dict:
        """
        分析销量趋势
        
        Args:
            df: DataFrame
            date_col: 日期列名（如 "2025-01"）
            sales_col: 销量列名
            group_col: 分组列（如属性值），None则整体分析
        
        Returns:
            {
                "trend_type": str,
                "qoq_values": list,
                "forecast": str,
                "details": dict
            }
        """
        # 按日期排序
        df_sorted = df.sort_values(date_col).copy()
        
        if group_col and group_col in df.columns:
            # 分组分析
            results = {}
            for group, group_df in df_sorted.groupby(group_col):
                monthly = group_df.groupby(date_col)[sales_col].sum()
                qoq = self.calculate_qoq(monthly)
                trend_type = self.classify_trend(qoq.dropna().tolist())
                results[group] = {
                    "trend_type": trend_type,
                    "qoq_values": qoq.dropna().tolist(),
                    "latest_value": monthly.iloc[-1] if len(monthly) > 0 else None
                }
            return {"grouped": results}
        else:
            # 整体分析
            monthly = df_sorted.groupby(date_col)[sales_col].sum()
            qoq = self.calculate_qoq(monthly)
            trend_type = self.classify_trend(qoq.dropna().tolist())
            return {
                "trend_type": trend_type,
                "qoq_values": qoq.dropna().tolist(),
                "latest_value": monthly.iloc[-1] if len(monthly) > 0 else None,
                "last_4_quarters": monthly.tail(4).to_dict()
            }
    
    def cross_validate_with_aba(self, sales_qoq: List[float], aba_qoq: List[float]) -> Dict:
        """
        交叉验证销量趋势与ABA搜索趋势是否一致
        """
        if len(sales_qoq) != len(aba_qoq) or len(sales_qoq) < 2:
            return {"status": "数据不足", "message": "请提供至少2个季度的数据"}
        
        # 计算方向一致性
        sales_directions = [1 if v > 0 else (-1 if v < 0 else 0) for v in sales_qoq[-2:]]
        aba_directions = [1 if v > 0 else (-1 if v < 0 else 0) for v in aba_qoq[-2:]]
        
        consistent = sum(1 for s, a in zip(sales_directions, aba_directions) if s == a)
        
        if consistent == 2:
            status = "✅ 趋势一致（高置信度）"
            message = "销量与搜索量趋势同步，市场需求真实可靠"
        elif consistent == 1:
            status = "⚠️ 趋势部分一致（中等置信度）"
            message = "建议结合其他数据（如竞品动作）进一步验证"
        else:
            status = "❌ 趋势背离（低置信度）"
            message = "销量上涨但搜索量未增长，可能由于促销或库存变动，需警惕"
        
        return {"status": status, "message": message, "consistency_score": consistent / 2}
