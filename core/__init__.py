
---

## 文件 4：`core/__init__.py`

```python
"""
ABA利基分析工具 - 核心模块
"""

from .parser import parse_aba_csv
from .clustering import semantic_clustering
from .scoring import calculate_10d_scores, assign_weight_level
from .trend import trend_verification
from .comment_analysis import analyze_comments
from .report_generator import generate_excel_report

__all__ = [
    "parse_aba_csv",
    "semantic_clustering",
    "calculate_10d_scores",
    "assign_weight_level",
    "trend_verification",
    "analyze_comments",
    "generate_excel_report"
]
