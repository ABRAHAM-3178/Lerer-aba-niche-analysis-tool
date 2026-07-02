"""
ABA利基分析工具 v5.0 - Streamlit主界面
双轨：路线一（已知方向）+ 路线二（未知方向）
"""

import streamlit as st
import pandas as pd
import yaml

# 导入核心模块
from core.column_mapper import AIColumnMapper, ColumnMappingResult
from core.attribute_normalizer import AttributeNormalizer
from core.market_filter import MarketFilter, MarketFilterResult
from core.comment_analysis import CommentAnalyzer
from core.trend import TrendAnalyzer  # 你原有的趋势分析
from core.report_generator import ReportGenerator
from utils.ai_client import AIClient

# 页面配置
st.set_page_config(
    page_title="ABA利基分析工具 v5.0",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 ABA利基分析工具 v5.0")
st.markdown("*产品开发决策引擎：从数据到产品定义，AI全程介入*")

# ==================== 侧边栏：模式选择 ====================
with st.sidebar:
    st.header("⚙️ 分析模式")
    
    route = st.radio(
        "选择你的状态",
        [
            "✅ 路线一：我有明确类目/方向",
            "❓ 路线二：我完全不知道卖什么"
        ],
        help="路线一用于深度分析已知方向；路线二用于扫描蓝海类目"
    )
    
    st.divider()
    
    # 高级阈值调节
    with st.expander("🎛️ 高级阈值调节"):
        st.caption("调节市场过滤器的判定标准（仅路线二生效）")
        min_sales = st.number_input("月销量门槛", value=30000, step=5000)
        min_price = st.number_input("客单价门槛 ($)", value=20.0, step=5.0)
        max_reviews = st.number_input("评论壁垒", value=500, step=50)
        max_brand_concentration = st.slider("品牌垄断度上限", 0.1, 1.0, 0.6, 0.05)

# ==================== 主区域 ====================

# ---- 数据上传 ----
st.subheader("📤 上传数据文件")
st.caption("支持卖家精灵 / Jungle Scout / Helium 10 导出的CSV/Excel文件")

col1, col2 = st.columns(2)

with col1:
    sales_file = st.file_uploader(
        "竞品销量/价格快照",
        type=["csv", "xlsx"],
        help="包含ASIN、Title、价格、月销量、评论数等字段"
    )

with col2:
    review_file = st.file_uploader(
        "竞品评论数据（可选）",
        type=["csv", "xlsx"],
        help="包含ASIN、评论星级、评论正文等字段，用于痛点挖掘"
    )

# ---- AI列名映射 ----
if sales_file is not None:
    st.divider()
    st.subheader("🤖 AI智能列名映射")
    
    # 读取文件
    if sales_file.name.endswith('.csv'):
        df_raw = pd.read_csv(sales_file)
    else:
        df_raw = pd.read_excel(sales_file)
    
    st.info(f"✅ 已读取文件：{sales_file.name}，共 {len(df_raw)} 行，{len(df_raw.columns)} 列")
    
    # 调用列名映射
    mapper = AIColumnMapper()
    mapping_result = mapper.map_columns(df_raw)
    mapping_summary = mapper.get_mapping_summary(mapping_result)
    
    # 展示映射结果
    with st.expander("📋 查看列名映射详情"):
        mapping_df = pd.DataFrame(mapping_summary["mapping_table"])
        st.dataframe(mapping_df, use_container_width=True)
        
        st.caption(f"自动映射: {mapping_summary['auto_mapped']} | 需确认: {mapping_summary['needs_confirmation']} | 未识别: {mapping_summary['unmapped']}")
    
    # 应用映射
    df_mapped = mapper.apply_mapping(df_raw, mapping_result)
    
    # ---- 数据清洗与属性提取 ----
    st.subheader("🧹 数据清洗 & 属性提取")
    
    # 标准化
    normalizer = AttributeNormalizer("config.yaml")
    
    if "title" in df_mapped.columns:
        df_processed = normalizer.normalize_df_attributes(df_mapped, "title")
        attr_summary = normalizer.get_attribute_summary(df_processed)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("识别到的属性维度", len([k for k, v in attr_summary.items() if v["unique_count"] > 0]))
        with col2:
            st.metric("有效数据行数", len(df_processed))
        
        with st.expander("📊 属性分布预览"):
            for attr, data in attr_summary.items():
                if data["unique_count"] > 0:
                    st.write(f"**{attr}** (共{data['unique_count']}种值，覆盖率{data['coverage']:.1f}%)")
                    st.write(pd.DataFrame(list(data["top_values"].items()), columns=["值", "出现次数"]))
    
    # ---- 路线分流 ----
    st.divider()
    
    if "❓ 路线二：我完全不知道卖什么" in route:
        st.subheader("🔍 市场准入过滤器（路线二）")
        
        filter = MarketFilter("config.yaml")
        # 更新用户调节的阈值
        filter.update_thresholds(
            min_monthly_sales=min_sales,
            min_avg_price=min_price,
            max_avg_review_count=max_reviews,
            max_brand_concentration=max_brand_concentration
        )
        
        result = filter.filter_class(df_processed)
        
        # 展示结果
        col1, col2 = st.columns([1, 2])
        with col1:
            if result.passed:
                st.success("✅ 市场准入")
            else:
                st.error("❌ 市场淘汰")
        
        with col2:
            st.write(result.recommendation)
        
        # 详细指标
        for indicator in result.indicators:
            status = "✅" if indicator.passed else "❌"
            st.metric(
                label=f"{status} {indicator.name}",
                value=indicator.message,
                delta="达标" if indicator.passed else f"需 ≥ {indicator.threshold}"
            )
        
        if not result.passed:
            st.warning("🔴 该市场未通过准入过滤，建议切换类目。")
            st.stop()
    
    else:
        st.subheader("🔍 深度竞品分析（路线一）")
        
        # ---- 价格带分析 ----
        st.write("### 💰 价格带分析")
        if "price" in df_processed.columns:
            prices = df_processed["price"].dropna()
            if len(prices) > 0:
                price_stats = {
                    "min": prices.min(),
                    "max": prices.max(),
                    "mean": prices.mean(),
                    "median": prices.median(),
                    "q25": prices.quantile(0.25),
                    "q75": prices.quantile(0.75),
                }
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最低价", f"${price_stats['min']:.0f}")
                col2.metric("25分位", f"${price_stats['q25']:.0f}")
                col3.metric("中位数", f"${price_stats['median']:.0f}")
                col4.metric("75分位", f"${price_stats['q75']:.0f}")
                
                # 检测价格断层
                sorted_prices = sorted(prices)
                gaps = []
                for i in range(1, len(sorted_prices)):
                    diff = sorted_prices[i] - sorted_prices[i-1]
                    if diff > sorted_prices[i-1] * 0.2:  # 价差>20%视为断层
                        gaps.append({
                            "start": sorted_prices[i-1],
                            "end": sorted_prices[i],
                            "diff": diff,
                            "diff_pct": diff / sorted_prices[i-1] * 100
                        })
                
                if gaps:
                    st.success(f"💰 发现 {len(gaps)} 个价格断层，最高断层差价 ${gaps[0]['diff']:.0f}")
                    st.write(pd.DataFrame(gaps))
                else:
                    st.info("未发现明显价格断层，市场定价较为连续")
        
        # ---- 痛点挖掘 ----
        if review_file is not None:
            st.write("### 🔧 差评痛点挖掘")
            
            # 读取评论
            if review_file.name.endswith('.csv'):
                reviews_df = pd.read_csv(review_file)
            else:
                reviews_df = pd.read_excel(review_file)
            
            # 映射评论列
            review_mapping = mapper.map_columns(reviews_df)
            reviews_mapped = mapper.apply_mapping(reviews_df, review_mapping)
            
            # 分析痛点
            analyzer = CommentAnalyzer()
            pain_points = analyzer.extract_pain_points(reviews_mapped, min_mentions=3)
            
            if pain_points:
                st.write(f"🔍 发现 {len(pain_points)} 个痛点（提及率 > 5% 的已高亮）")
                
                pain_data = []
                for pp in pain_points[:10]:
                    pain_data.append({
                        "痛点": pp.keyword,
                        "提及次数": pp.mention_count,
                        "提及率": f"{pp.mention_rate:.1%}",
                        "代表评论": pp.sample_reviews[0][:80] + "..." if pp.sample_reviews else "",
                    })
                
                st.dataframe(pd.DataFrame(pain_data), use_container_width=True)
            else:
                st.info("未发现明显痛点，或评论数量不足")
        
        # ---- 趋势分析 ----
        st.write("### 📈 趋势分析")
        
        # 这里调用你原有的trend.py逻辑
        # st.write("（趋势分析功能调用原有模块）")
        
        # 简单的趋势判断
        if "monthly_sales" in df_processed.columns:
            # 按时间分组（如果有日期列）
            st.info("💡 趋势分析需要按月/季度的数据支持，请确保上传了历史数据。")
        
        # ---- 生成报告 ----
        st.divider()
        if st.button("🚀 生成产品定义报告", type="primary"):
            st.write("### 📄 产品定义报告")
            
            # 准备数据
            price_gap_analysis = {"avg_price": df_processed["price"].mean() if "price" in df_processed.columns else 0}
            
            # 获取痛点
            pain_points = []
            if review_file is not None:
                # 重新提取痛点为list
                pass
            
            # 属性机会
            attribute_opportunities = {}
            if "attr_尺寸_标准" in df_processed.columns:
                sizes = df_processed["attr_尺寸_标准"].dropna().value_counts()
                if len(sizes) > 0:
                    attribute_opportunities["尺寸"] = {"top_values": sizes.index[:3].tolist()}
            
            # 生成报告
            report_gen = ReportGenerator()
            # 此处需传入实际的AI客户端，当前使用占位
            definition = report_gen.generate_product_definition_report(
                class_name="该类目",
                price_gap_analysis=price_gap_analysis,
                pain_points=[],
                attribute_opportunities=attribute_opportunities,
                trend_analysis={}
            )
            
            # 显示HTML报告
            html_report = report_gen.format_report_html(definition, {})
            st.markdown(html_report, unsafe_allow_html=True)

# ---- 页脚 ----
st.divider()
st.caption("ABA利基分析工具 v5.0 | 产品开发决策引擎 | 数据驱动 · AI赋能")
