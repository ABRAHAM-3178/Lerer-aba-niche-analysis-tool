"""
ABA利基分析工具 v5.0 - 数据验证器
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


class DataValidator:
    """数据验证器"""
    
    REQUIRED_COLUMNS = ["asin", "title", "price", "monthly_sales", "review_count"]
    
    @classmethod
    def validate(cls, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """验证DataFrame是否包含必要列"""
        missing = []
        for col in cls.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing.append(col)
        
        if missing:
            return False, [f"缺少必要列: {', '.join(missing)}"]
        
        # 检查空值比例
        warnings = []
        for col in cls.REQUIRED_COLUMNS:
            null_pct = df[col].isnull().sum() / len(df)
            if null_pct > 0.3:
                warnings.append(f"列 '{col}' 空值比例 {null_pct:.1%}，建议检查数据质量")
        
        return True, warnings
    
    @classmethod
    def clean_price(cls, series: pd.Series) -> pd.Series:
        """清理价格列"""
        return series.astype(str).str.replace(r'[$,€,¥]', '', regex=True).str.strip()
    
    @classmethod
    def clean_numeric(cls, series: pd.Series) -> pd.Series:
        """清理数字列"""
        return pd.to_numeric(series, errors='coerce')
