"""
ABA利基分析工具 v5.0 - AI智能列名映射模块
功能：自动识别用户上传文件的列名，映射到系统标准字段
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

# 标准字段库 - 与数据模型一一对应
STANDARD_FIELDS = {
    "asin": {"keywords": ["asin", "商品编码", "amazon standard identification number", "亚马逊编码", "商品id"]},
    "parent_asin": {"keywords": ["parent asin", "父体asin", "父asin", "父商品编码", "parent"]},
    "title": {"keywords": ["title", "商品标题", "标题", "product title", "listing name", "product name"]},
    "price": {"keywords": ["price", "价格", "售价", "客单价", "unit price", "sale price", "current price"]},
    "monthly_sales": {"keywords": ["monthly sales", "月销量", "销量", "sales volume", "月销售量", "qty", "销售量"]},
    "monthly_revenue": {"keywords": ["monthly revenue", "月销售额", "销售额", "revenue", "gmv", "sales revenue"]},
    "review_count": {"keywords": ["review count", "评论数", "评价数", "rating count", "留评数", "total reviews"]},
    "rating": {"keywords": ["rating", "评分", "星级", "平均分", "average rating", "star rating"]},
    "bsr_rank": {"keywords": ["bsr", "排名", "类目排名", "best seller rank", "rank", "畅销排名"]},
    "category": {"keywords": ["category", "类目", "品类", "分类", "node", "类目节点"]},
    "review_date": {"keywords": ["review date", "评论日期", "日期", "date", "posted on"]},
    "review_star": {"keywords": ["star", "星级", "评分", "rating score", "评价分数"]},
    "review_body": {"keywords": ["review body", "评论内容", "正文", "content", "评价内容", "comment"]},
    "review_title": {"keywords": ["review title", "评论标题", "标题", "subject"]},
    "verified_purchase": {"keywords": ["verified", "vp", "验证购买", "真实购买", "verified purchase"]},
    "keyword": {"keywords": ["keyword", "关键词", "搜索词", "search term", "查询词"]},
    "search_volume": {"keywords": ["search volume", "搜索量", "搜索热度", "volume", "搜索次数"]},
    "traffic_share": {"keywords": ["traffic share", "流量占比", "流量份额", "share", "占比"]},
    "rank_position": {"keywords": ["rank", "排名位置", "自然排名", "organic rank", "position"]},
    "asin_source": {"keywords": ["asin source", "来源asin", "竞品asin", "source"]},
}


@dataclass
class ColumnMappingResult:
    """列名映射结果"""
    user_column: str
    standard_field: Optional[str]
    confidence: float
    needs_confirmation: bool


class AIColumnMapper:
    """AI驱动的列名映射器"""
    
    def __init__(self, similarity_threshold: float = 0.8, confirm_threshold: float = 0.5):
        self.similarity_threshold = similarity_threshold
        self.confirm_threshold = confirm_threshold
        self.standard_fields = STANDARD_FIELDS
    
    def _calculate_similarity(self, user_col: str, standard_col: str) -> float:
        """计算用户列名与标准字段的相似度"""
        user_col_lower = user_col.lower().strip()
        standard_col_lower = standard_col.lower().strip()
        
        # 1. 精确匹配
        if user_col_lower == standard_col_lower:
            return 1.0
        
        # 2. 关键词匹配（标准字段的keywords）
        std_info = self.standard_fields.get(standard_col_lower, {})
        for keyword in std_info.get("keywords", []):
            if keyword in user_col_lower:
                return 0.95
        
        # 3. 模糊匹配
        ratio = SequenceMatcher(None, user_col_lower, standard_col_lower).ratio()
        if ratio > 0.7:
            return ratio
        
        return 0.0
    
    def map_columns(self, df: pd.DataFrame) -> Dict[str, ColumnMappingResult]:
        """映射DataFrame的所有列名"""
        results = {}
        user_columns = df.columns.tolist()
        
        # 构建标准字段列表（用于候选匹配）
        standard_names = list(self.standard_fields.keys())
        
        for user_col in user_columns:
            best_match = None
            best_score = 0.0
            
            for std_col in standard_names:
                score = self._calculate_similarity(user_col, std_col)
                if score > best_score:
                    best_score = score
                    best_match = std_col
            
            if best_match and best_score >= self.similarity_threshold:
                needs_confirm = False
            elif best_match and best_score >= self.confirm_threshold:
                needs_confirm = True
            else:
                best_match = None
                needs_confirm = True
            
            results[user_col] = ColumnMappingResult(
                user_column=user_col,
                standard_field=best_match,
                confidence=best_score,
                needs_confirmation=needs_confirm
            )
        
        return results
    
    def apply_mapping(self, df: pd.DataFrame, mapping: Dict[str, ColumnMappingResult]) -> pd.DataFrame:
        """应用列名映射，重命名DataFrame列"""
        rename_map = {}
        for user_col, result in mapping.items():
            if result.standard_field and not result.needs_confirmation:
                rename_map[user_col] = result.standard_field
        
        if rename_map:
            return df.rename(columns=rename_map)
        return df
    
    def get_mapping_summary(self, mapping: Dict[str, ColumnMappingResult]) -> Dict:
        """生成映射摘要，用于界面展示"""
        summary = {
            "total_columns": len(mapping),
            "auto_mapped": 0,
            "needs_confirmation": 0,
            "unmapped": 0,
            "mapping_table": []
        }
        
        for result in mapping.values():
            if result.standard_field and not result.needs_confirmation:
                summary["auto_mapped"] += 1
            elif result.standard_field and result.needs_confirmation:
                summary["needs_confirmation"] += 1
            else:
                summary["unmapped"] += 1
            
            summary["mapping_table"].append({
                "user_column": result.user_column,
                "mapped_to": result.standard_field or "未识别",
                "confidence": f"{result.confidence:.0%}",
                "status": "✅ 已自动映射" if (result.standard_field and not result.needs_confirmation) else ("⚠️ 需确认" if result.standard_field else "❌ 未识别")
            })
        
        return summary
