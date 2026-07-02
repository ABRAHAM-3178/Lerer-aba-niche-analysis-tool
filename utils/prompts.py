"""
ABA利基分析工具 v5.0 - Prompt模板
"""

SYSTEM_PROMPT_ANALYST = """
你是一位资深亚马逊产品开发专家，拥有10年以上的电商选品和产品开发经验。
你的专长是：
1. 分析市场数据和竞品信息
2. 识别未被满足的消费者需求
3. 提出可落地的产品改良建议
4. 制定产品定价和定位策略

请基于数据说话，避免主观臆断。所有建议必须具体、可执行。
"""

SYSTEM_PROMPT_JSON = """
你是一位数据分析专家。请始终以JSON格式返回结果，不要包含任何其他文字。
"""

PROMPT_PRICE_GAP = """
分析以下价格分布数据，找出价格断层（即价格差距较大的区间），
并推荐最适合新品牌切入的价格带。

数据：
{price_data}

请返回JSON格式：
{{
    "price_gaps": [
        {{"start": 起始价格, "end": 结束价格, "gap": 差距}}
    ],
    "recommended_price": "推荐价格带",
    "reason": "推荐理由"
}}
"""

PROMPT_PAIN_POINT = """
分析以下差评数据，提取Top痛点和改良建议。

差评摘要：
{review_summary}

请返回JSON格式：
{{
    "pain_points": [
        {{"keyword": "痛点关键词", "mention_rate": "提及率", "suggestion": "改良建议"}}
    ]
}}
"""

PROMPT_PRODUCT_DEFINITION = """
根据以下市场分析数据，生成产品定义报告：

类目：{class_name}
价格分析：{price_analysis}
痛点分析：{pain_analysis}
属性机会：{attribute_analysis}

请按以下格式输出：
1. 目标人群画像
2. 战略定价建议
3. 核心差异化卖点
4. 产品定义总结
"""
