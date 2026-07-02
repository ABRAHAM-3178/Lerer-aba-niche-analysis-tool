"""
ABA利基分析工具 v5.0 - 报告生成器（黄金三角收敛）
输出：产品定义报告（价格、人群、卖点）
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ProductDefinition:
    """黄金三角产品定义"""
    target_audience: str  # 目标人群
    strategic_price: str  # 战略定价
    core_usps: List[str]  # 核心差异化卖点
    solved_pain_points: List[str]  # 解决的痛点
    product_name: str  # 具体产品名称
    summary: str  # 一句话总结


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
        """
        生成产品定义报告
        
        Args:
            class_name: 类目名称
            price_gap_analysis: 价格带分析结果
            pain_points: 痛点列表
            attribute_opportunities: 属性机会矩阵
            trend_analysis: 趋势分析结果
        """
        # 1. 提取目标人群（从评论中反推）
        target_audience = self._infer_audience(pain_points, attribute_opportunities)
        
        # 2. 确定战略定价
        strategic_price = self._determine_price(price_gap_analysis)
        
        # 3. 提取核心卖点
        core_usps = self._extract_usps(pain_points, attribute_opportunities)
        
        # 4. 痛点清单
        solved_pain_points = [pp.keyword for pp in pain_points[:3] if pp.mention_rate > 0.05]
        
        # 5. 产品名称生成
        product_name = f"{class_name} 升级款" if core_usps else class_name
        
        # 6. 一句话总结
        summary = f"我们要为【{target_audience}】，提供一款定价在【{strategic_price}】，通过【{', '.join(core_usps[:2])}】解决【{solved_pain_points[0] if solved_pain_points else '核心痛点'}】的【{product_name}】。"
        
        return ProductDefinition(
            target_audience=target_audience,
            strategic_price=strategic_price,
            core_usps=core_usps,
            solved_pain_points=solved_pain_points,
            product_name=product_name,
            summary=summary
        )
    
    def _infer_audience(self, pain_points: List, attribute_opportunities: Dict) -> str:
        """从痛点中推断目标人群"""
        # 简版：从高频痛点反推
        audience_keywords = {
            "small": "小户型/紧凑空间用户",
            "large": "大户型/多人使用场景",
            "heavy": "重度使用者/工业场景",
            "light": "轻量使用/家庭场景",
            "budget": "价格敏感型用户",
            "premium": "品质追求型用户",
        }
        
        for pp in pain_points[:5]:
            for key, audience in audience_keywords.items():
                if key in pp.keyword.lower():
                    return audience
        
        return "大众消费市场"
    
    def _determine_price(self, price_gap_analysis: Dict) -> str:
        """确定战略定价"""
        gaps = price_gap_analysis.get("price_gaps", [])
        if gaps:
            # 取第一个价格断层
            gap = gaps[0]
            return f"${gap['start']:.0f}-${gap['end']:.0f}（空白价格带）"
        
        avg_price = price_gap_analysis.get("avg_price", 25)
        return f"${avg_price * 0.8:.0f}-${avg_price * 1.2:.0f}（主流价格带）"
    
    def _extract_usps(self, pain_points: List, attribute_opportunities: Dict) -> List[str]:
        """提取核心卖点"""
        usps = []
        
        # 从痛点反推卖点
        for pp in pain_points[:3]:
            if pp.mention_rate > 0.05:
                if "broken" in pp.keyword or "cracked" in pp.keyword:
                    usps.append("加固结构设计")
                elif "noise" in pp.keyword or "loud" in pp.keyword:
                    usps.append("静音升级")
                elif "unstable" in pp.keyword or "wobbly" in pp.keyword:
                    usps.append("防抖/稳定结构")
                elif "thin" in pp.keyword or "flimsy" in pp.keyword:
                    usps.append("加厚/加固材质")
                elif "assembly" in pp.keyword or "install" in pp.keyword:
                    usps.append("免工具/简易安装")
        
        # 从属性机会中提取
        top_attr = attribute_opportunities.get("top_opportunity", "")
        if top_attr and "尺寸" in attribute_opportunities:
            size = attribute_opportunities.get("尺寸", {}).get("top_values", [])
            if size:
                usps.append(f"{size[0]}大尺寸升级版")
        
        return list(set(usps))[:3] if usps else ["性价比平替"]
    
    def format_report_html(self, definition: ProductDefinition, 
                          details: Dict) -> str:
        """生成HTML格式的报告（用于Streamlit展示）"""
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
                <h4 style="color: #2d3748;">🚀 核心差异化卖点 (USP)</h4>
                <ul style="font-size: 15px; line-height: 1.8;">
                    {''.join([f'<li>✅ {usp}</li>' for usp in definition.core_usps])}
                </ul>
            </div>
            
            <div style="background: white; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <h4 style="color: #2d3748;">🔧 解决的痛点</h4>
                <ul style="font-size: 14px; color: #4a5568;">
                    {''.join([f'<li>🔹 {pain}' for pain in definition.solved_pain_points])}
                </ul>
            </div>
            
            <div style="background: #fefcbf; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #d69e2e; margin-top: 16px;">
                <span style="font-weight: 600;">📊 报告生成时间：</span>
                {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
        """
        return html
