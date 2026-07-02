"""
ABA利基分析工具 v5.0 - 解析器模块（兼容v4.0）
"""

import re
from typing import Dict, List, Optional


class Parser:
    """数据解析器"""
    
    @staticmethod
    def extract_brand(title: str) -> Optional[str]:
        """从标题提取品牌"""
        patterns = [
            r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',
            r'by\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1).strip()
        return None
    
    @staticmethod
    def extract_dimension(title: str) -> Optional[str]:
        """从标题提取尺寸"""
        pattern = r'(\d{2})\s*(?:x\s*\d{2})?\s*(?:-inch|inch|in|\"|寸)'
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return f"{match.group(1)}寸"
        return None
    
    @staticmethod
    def extract_color(title: str, color_mapping: Dict[str, str] = None) -> Optional[str]:
        """从标题提取颜色"""
        if color_mapping:
            for pattern, standard in color_mapping.items():
                if re.search(pattern, title, re.IGNORECASE):
                    return standard
        
        colors = ['black', 'white', 'brown', 'walnut', 'oak', 'gray', 'grey', 'blue', 'red', 'green']
        for color in colors:
            if re.search(rf'\b{color}\b', title, re.IGNORECASE):
                return color
        return None
