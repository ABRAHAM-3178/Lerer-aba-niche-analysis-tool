"""
ABA利基分析工具 v5.0 - 报告生成器（黄金三角）
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ProductDefinition:
    target_audience: str
    strategic_price: str
    core_usps: List[str]
    solved_pain_points: List[str]
    product_name: str
    summary: str


class ReportGenerator:
    """生成黄金三角产品定义报告"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    def generate_product_definition_report(
        self,
        class_name: str,
        price_gap_analysis: Dict,
        pain_points: List,
        attribute_opportunities: Dict,
        trend_analysis: Dict
    ) -> ProductDefinition:
        """生成产品定义报告"""
        
        target_audience = self._infer_audience(pain_points, attribute_opportunities)
        strategic_price = self._determine_price(price_gap_analysis)
        core_usps = self._extract_usps(pain_points, attribute_opportunities)
        solved_pain_points = [pp.keyword for pp in pain_points[:3] if pp.mention_rate > 0.05] if pain_points else ["待发现"]
        product_name = f"{class_name} 升级款" if core_usps else class_name
        summary = f"我们要为【{target_audience}】，提供一款定价在【{strategic_price}】，通过【{', '.join(core_usps[:2]) if core_usps else '核心卖点'}】解决【{solved_pain_points[0] if solved_pain_points else '核心痛点'}】的【{product_name}】。"
        
        return ProductDefinition(
            target_audience=target_audience,
            strategic_price=strategic_price,
            core_usps=core_usps,
            solved_pain_points=solved_pain_points,
            product_name=product_name,
            summary=summary
        )
    
    def _infer_audience(self, pain_points: List, attribute_opportunities: Dict) -> str:
        audience_keywords = {
            "small": "小户型/紧凑空间用户",
            "large": "大户型/多人使用场景",
            "heavy": "重度使用者",
            "budget": "价格敏感型用户",
            "premium": "品质追求型用户",
        }
        for pp in pain_points[:5]:
            for key, audience in audience_keywords.items():
                if key in pp.keyword.lower():
                    return audience
        return "大众消费市场"
    
    def _determine_price(self, price_gap_analysis: Dict) -> str:
        avg_price = price_gap_analysis.get("avg_price", 25)
        if avg_price > 0:
            return f"${avg_price * 0.8:.0f}-${avg_price * 1.2:.0f}"
        return "待定"
    
    def _extract_usps(self, pain_points: List, attribute_opportunities: Dict) -> List[str]:
        usps = []
        for pp in pain_points[:3]:
            if pp.mention_rate > 0.05:
                if "broken" in pp.keyword or "cracked" in pp.keyword:
                    usps.append("加固结构设计")
                elif "noise" in pp.keyword or "loud" in pp.keyword:
                    usps.append("静音升级")
                elif "unstable" in pp.keyword or "wobbly" in pp.keyword:
                    usps.append("防抖稳定结构")
                elif "thin" in pp.keyword or "flimsy" in pp.keyword:
                    usps.append("加厚加固材质")
                elif "assembly" in pp.keyword or "install" in pp.keyword:
                    usps.append("免工具简易安装")
        return list(set(usps))[:3] if usps else ["性价比平替"]
    
    def format_report_html(self, definition: ProductDefinition, details: Dict) -> str:
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; background: #f5f7fa; border-radius: 12px;">
            
            <h2 style="color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px;">
                🎯 产品定义报告
            </h2>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 16px 0;">
                <h3 style="color: #2d3748;">📌 一句话产品定义</h3>
                <div style="background: #e8f0fe; padding: 16px; border-radius: 8px; font-size: 18px; font-weight: 500;">
                    {definition.summary}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div style="background: white; padding: 16px; border-radius: 8px;">
                    <h4 style="color: #2d3748;">👤 目标人群</h4>
                    <p style="font-size: 16px;">{definition.target_audience}</p>
                </div>
                <div style="background: white; padding: 16px; border-radius: 8px;">
                    <h4 style="color: #2d3748;">💰 战略定价</h4>
                    <p style="font-size: 16px; font-weight: 600; color: #1a73e8;">{definition.strategic_price}</p>
                </div>
            </div>
            
            <div style="background: white; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <h4 style="color: #2d3748;">🚀 核心差异化卖点</h4>
                <ul style="font-size: 15px; line-height: 1.8;">
                    {''.join([f'<li>✅ {usp}</li>' for usp in definition.core_usps])}
                </ul>
            </div>
            
            <div style="background: white; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <h4 style="color: #2d3748;">🔧 解决的痛点</h4>
                <ul style="font-size: 14px; color: #4a5568;">
                    {''.join([f'<li>🔹 {pain}</li>' for pain in definition.solved_pain_points])}
                </ul>
            </div>
            
            <div style="background: #fefcbf; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #d69e2e; margin-top: 16px;">
                <span style="font-weight: 600;">📊 报告生成时间：</span>
                {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
        """
        return html
