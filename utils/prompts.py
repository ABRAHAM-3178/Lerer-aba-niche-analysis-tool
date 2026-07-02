"""
大模型提示词模板
"""

CLUSTERING_PROMPT = """
你是一个亚马逊选品分析专家。请分析以下关键词列表，将它们按【核心卖点/功能/场景】聚类。

## 规则
1. 每个卖点类别用一个简短的名字表示
2. 将每个关键词归入最匹配的卖点类别
3. 如果某个关键词不属于任何明显卖点，归入"其他"
4. 忽略品牌名，只看产品功能

## 关键词列表
{keywords}

## 输出格式
必须输出 JSON 格式：
{{
  "clusters": [
    {{"name": "降噪", "keywords": ["noise cancelling headphones", "ANC earbuds"]}}
  ]
}}
"""

COMMENT_ANALYSIS_PROMPT = """
你是一个产品经理。请分析以下用户评论，提取产品改进建议。

## 规则
1. 找出 Top 3 用户痛点
2. 找出 Top 3 用户好评
3. 针对痛点给出具体的产品改进建议
4. 针对好评给出 Listing 优化建议

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

## 输出要求
用专业、简洁的中文输出，重点说明：
1. 该市场当前的竞争态势
2. 进入建议（优先/谨慎/放弃）
3. 关键的差异化方向
"""


def build_clustering_messages(keywords: list) -> list:
    return [
        {"role": "system", "content": "你是一个亚马逊选品分析专家，擅长语义聚类。"},
        {"role": "user", "content": CLUSTERING_PROMPT.format(keywords=", ".join(keywords[:100]))}
    ]


def build_comment_messages(comments: list) -> list:
    return [
        {"role": "system", "content": "你是一个产品经理，擅长从用户反馈中挖掘洞察。"},
        {"role": "user", "content": COMMENT_ANALYSIS_PROMPT.format(comments="\n".join(comments[:30]))}
    ]


def build_summary_messages(data: dict) -> list:
    return [
        {"role": "system", "content": "你是一个亚马逊选品顾问，擅长总结和给出建议。"},
        {"role": "user", "content": REPORT_SUMMARY_PROMPT.format(
            market_name=data.get("name", "未知"),
            score=data.get("final_score", 0),
            grade=data.get("grade", "C"),
            keyword_count=data.get("keyword_count", 0),
            top_modifiers="、".join(data.get("keywords", [])[:3])
        )}
    ]
