"""
ABA利基分析工具 v5.0 - 动态属性识别与标准化模块
功能：从标题中提取尺寸、颜色等属性，并进行标准化映射
"""

import re
import yaml
import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import Counter
from dataclasses import dataclass, field

@dataclass
class AttributeExtractionResult:
    """属性提取结果"""
    attribute_type: str  # 如: "尺寸", "颜色", "材质"
    raw_value: str
    normalized_value: str
    confidence: float


class AttributeNormalizer:
    """属性识别与标准化引擎"""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.color_mappings = config.get("color_mapping", [])
        self._compile_regex_patterns()
        
        # 动态属性缓存
        self._attribute_cache = {}
        
    def _compile_regex_patterns(self):
        """编译颜色映射的正则表达式"""
        for mapping in self.color_mappings:
            mapping["compiled_regex"] = re.compile(mapping["regex"], re.IGNORECASE)
    
    def extract_dimensions(self, title: str) -> List[str]:
        """从标题中提取尺寸信息"""
        patterns = [
            r'(\d{2})\s*(?:x\s*\d{2})?\s*(?:-inch|inch|in|\"|寸)',  # 48 inch, 48", 48寸
            r'(\d{2})\s*[x×]\s*(\d{2})',  # 48 x 24
            r'(\d{2}\.\d{1})\s*[x×]',  # 47.2 x
        ]
        
        dimensions = []
        for pattern in patterns:
            matches = re.findall(pattern, title, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # 提取第一个数字作为尺寸
                    for m in match:
                        if m and m.isdigit() and int(m) >= 20:
                            dimensions.append(f"{m}寸")
                else:
                    if match.isdigit() and int(match) >= 20:
                        dimensions.append(f"{match}寸")
        
        return list(set(dimensions))
    
    def extract_colors(self, title: str) -> List[str]:
        """从标题中提取并标准化颜色"""
        extracted_colors = []
        
        for mapping in self.color_mappings:
            if mapping["compiled_regex"].search(title):
                extracted_colors.append(mapping["standard"])
        
        return list(set(extracted_colors))
    
    def extract_attributes(self, title: str) -> Dict[str, List[str]]:
        """从标题中提取所有属性（尺寸、颜色、材质等）"""
        result = {
            "尺寸": self.extract_dimensions(title),
            "颜色": self.extract_colors(title),
        }
        
        # 尝试提取材质
        material_patterns = r'(?i)(?:solid wood|wood|metal|aluminum|steel|glass|plastic|fabric|leather|mesh|carbon fiber)'
        materials = re.findall(material_patterns, title)
        if materials:
            result["材质"] = list(set(materials))
        
        # 尝试提取风格/款式
        style_patterns = r'(?i)(?:u shaped|l shaped|corner|standing|adjustable|gaming|ergonomic|reversible)'
        styles = re.findall(style_patterns, title)
        if styles:
            result["款式"] = list(set(styles))
        
        return result
    
    def normalize_df_attributes(self, df: pd.DataFrame, title_column: str = "title") -> pd.DataFrame:
        """批量处理DataFrame，提取并标准化所有标题中的属性"""
        if title_column not in df.columns:
            return df
        
        # 提取属性
        df["_extracted_attributes"] = df[title_column].apply(self.extract_attributes)
        
        # 将提取的属性展开为独立列
        attribute_columns = ["尺寸", "颜色", "材质", "款式"]
        for attr in attribute_columns:
            df[f"attr_{attr}"] = df["_extracted_attributes"].apply(
                lambda x: ", ".join(x.get(attr, [])) if x.get(attr) else None
            )
        
        # 对于颜色，保留标准化后的第一个值（优先）
        df["attr_颜色_标准"] = df["_extracted_attributes"].apply(
            lambda x: x.get("颜色", [""])[0] if x.get("颜色") else None
        )
        
        # 对于尺寸，保留标准化后的第一个值
        df["attr_尺寸_标准"] = df["_extracted_attributes"].apply(
            lambda x: x.get("尺寸", [""])[0] if x.get("尺寸") else None
        )
        
        return df
    
    def get_attribute_summary(self, df: pd.DataFrame) -> Dict:
        """生成属性汇总统计"""
        summary = {}
        
        for attr in ["尺寸", "颜色", "材质", "款式"]:
            col = f"attr_{attr}"
            if col in df.columns:
                counts = df[col].value_counts().head(10).to_dict()
                summary[attr] = {
                    "top_values": counts,
                    "unique_count": df[col].nunique(),
                    "coverage": (df[col].notna().sum() / len(df)) * 100
                }
        
        return summary
