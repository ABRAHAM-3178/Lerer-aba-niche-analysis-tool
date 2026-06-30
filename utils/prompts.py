"""
大模型提示词模板
"""

CLUSTERING_PROMPT = """
你是一个亚马逊选品分析专家。请分析以下关键词列表，将它们按【核心卖点/功能/场景】聚类。

## 规则
1. 每个卖点类别用一个简短的名字表示（如：降噪、防水、便携、大容量、智能、人体工学、环保、设计感）
2. 将每个关键词归入最匹配的卖点类别
3. 如果一个关键词包含多个卖点，归入最主要的那个
4. 如果某个关键词不属于任何明显卖点，归入"其他"
5. 如果出现明显的品牌名（如 Sony、Anker），忽略品牌，只看产品功能

## 关键词列表
{keywords}

## 输出格式
必须输出 JSON 格式，结构如下：
{{
  "clusters": [
    {{
      "name": "降噪",
      "keywords": ["noise cancelling headphones", "ANC earbuds"],
      "avg_rank": 1250,
      "keyword_count": 2
    }}
  ]
}}
"""

COMMENT_ANALYSIS_PROMPT = """
你是一个产品经理。请分析以下用户评论，提取产品改进建议。

## 规则
1. 找出 Top 3 用户痛点（负面提及最多的点）
2. 找出 Top 3 用户好评（正面提及最多的点）
3. 针对痛点给出具体的产品改进建议
4. 针对好评给出 Listing 优化建议（如何放大这些优势）

## 评论内容
{comments}

## 输出格式
必须输出 JSON 格式：
{{
  "pains": ["痛点1", "痛点2", "痛点3"],
  "praises": ["好评1", "好评2", "好评3"],
  "product_suggestions": ["改进建议1", "改进建议2"],
  "listing_suggestions": ["优化建议1", "优化建议2"]
}}
"""

REPORT_SUMMARY_PROMPT = """
你是一个亚马逊选品顾问。请根据以下分析数据，生成一段 200 字以内的总结建议。

## 分析数据
- 市场名称: {market_name}
- 综合评分: {score} 分 ({grade}级)
- 关键词数: {keyword_count}
- 主要卖点: {top_modifiers}
- 核心竞争品牌: {top_brands}

## 输出要求
用专业、简洁的中文输出，重点说明：
1. 该市场当前的竞争态势
2. 进入建议（优先/谨慎/放弃）
3. 关键的差异化方向
"""


def build_clustering_messages(keywords: list) -> list:
    """构建聚类提示词"""
    return [
        {"role": "system", "content": "你是一个亚马逊选品分析专家，擅长语义聚类。"},
        {"role": "user", "content": CLUSTERING_PROMPT.format(
            keywords=", ".join(keywords[:100])
        )}
    ]


def build_comment_messages(comments: list) -> list:
    """构建评论分析提示词"""
    return [
        {"role": "system", "content": "你是一个产品经理，擅长从用户反馈中挖掘洞察。"},
        {"role": "user", "content": COMMENT_ANALYSIS_PROMPT.format(
            comments="\n".join(comments[:30])
        )}
    ]


def build_summary_messages(data: dict) -> list:
    """构建报告摘要提示词"""
    return [
        {"role": "system", "content": "你是一个亚马逊选品顾问，擅长总结和给出建议。"},
        {"role": "user", "content": REPORT_SUMMARY_PROMPT.format(
            market_name=data.get("name", "未知"),
            score=data.get("final_score", 0),
            grade=data.get("grade", "C"),
            keyword_count=data.get("keyword_count", 0),
            top_modifiers="、".join(data.get("keywords", [])[:3]),
            top_brands="、".join([])
        )}
    ]
  
DATA_CLEANING_PROMPT = """
你是一个数据分析专家，擅长清洗亚马逊ABA数据。

## 当前数据信息
列名: {columns}
样本数据: {sample_data}

## 任务
1. 识别每一列的实际含义（搜索词、排名、品牌、ASIN、点击份额、转化份额等）
2. 输出列名映射关系（原始列名 → 标准列名）
3. 识别异常值并给出处理建议

## 输出格式（必须 JSON）
{{
  "column_mapping": {{
    "原始列名1": "search_term",
    "原始列名2": "search_frequency_rank"
  }},
  "data_cleaning": {{
    "列名1": "strip",
    "列名2": "convert_float"
  }},
  "summary": "清洗摘要"
}}
"""

MODIFIER_DISCOVERY_PROMPT = """
你是一个产品卖点分析专家。

## 关键词列表
{keywords}

## 任务
分析这些关键词，找出其中的核心卖点/功能，将相似的关键词归类。

## 输出格式（必须 JSON）
{{
  "modifiers": {{
    "卖点名称1": ["关键词1", "关键词2"],
    "卖点名称2": ["关键词3", "关键词4"]
  }},
  "summary": "发现摘要"
}}
"""
