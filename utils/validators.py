"""
文件校验模块
"""

import pandas as pd
from typing import Dict, List, Tuple


def validate_file(df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, str]:
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return False, f"缺少必需列: {', '.join(missing)}"
    if df.empty:
        return False, "文件为空"
    return True, "校验通过"


def validate_all_files(files: Dict[str, pd.DataFrame]) -> Dict[str, Tuple[bool, str]]:
    results = {}
    validations = {
        'aba': ['Search Term', 'Search Frequency Rank'],
        'keyword': ['keyword', 'monthly_search_volume'],
        'asin': ['asin', 'keyword'],
        'review': ['asin', 'review_body'],
        'sif': ['keyword'],
        'trend': ['asin', 'modifier']
    }
    for key, df in files.items():
        if key in validations:
            results[key] = validate_file(df, validations[key])
    return results
