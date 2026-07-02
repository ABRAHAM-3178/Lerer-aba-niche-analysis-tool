"""
ABA利基分析工具 v5.0 - 数据加载模块（兼容v4.0）
"""

import pandas as pd
import os
from typing import Optional, Dict, Any


class DataLoader:
    """数据加载器"""
    
    @staticmethod
    def load_csv(file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """加载CSV文件"""
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding='gbk')
    
    @staticmethod
    def load_excel(file_path: str) -> pd.DataFrame:
        """加载Excel文件"""
        return pd.read_excel(file_path)
    
    @staticmethod
    def load_file(file_path: str) -> pd.DataFrame:
        """自动识别文件类型并加载"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return DataLoader.load_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            return DataLoader.load_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
