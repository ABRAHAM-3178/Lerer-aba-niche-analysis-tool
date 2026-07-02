"""
ABA利基分析工具 v5.0 - Streamlit 主界面
产品开发决策引擎：从数据到产品定义，AI全程介入
"""

import streamlit as st
import pandas as pd
import yaml
import os
import sys
from datetime import datetime

# 将项目根目录加入路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from core.column_mapper import AIColumnMapper
from core.attribute_normalizer import AttributeNormalizer
from core.market_filter import MarketFilter
from core.comment_analysis import CommentAnalyzer, PainPoint
from core.trend import TrendAnalyzer
from core.report_generator import ReportGenerator
from utils.ai_client import create_deepseek_client, AIClient

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="ABA利基分析工具 v5.0",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 会话状态初始化 ====================
if "ai_client" not in st.session_state:
    st.session_state.ai_client = None

if "df_processed" not in st.session_state:
    st.session_state.df_processed = None

if "mapping_result" not in st.session_state:
    st.session_state.mapping_result = None

if "pain_points" not in st.session_state:
    st.session_state.pain_points = []

if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

# ==================== 侧边栏 ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/idea.png", width=60)
    st.title("🔍 ABA利基分析")
    st.caption("v5.0 · 产品开发决策引擎")
    
    st.divider()
    
    # AI配置
    with st.expander("🤖 AI 配置", expanded=False):
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            placeholder="sk-...",
            help="从 platform.deepseek.com 获取"
        )
        if st.button("连接 AI", use_container_width=True):
            if api_key:
                try:
                    st.session_state.ai_client = create_deepseek_client(api_key=api_key)
                    st.success("✅ AI 已连接")
                except Exception as e:
                    st.error(f"连接失败: {e}")
            else:
                st.warning("请输入 API Key")
    
    st.divider()
    
    # 模式选择
    route = st.radio(
        "📋 选择分析模式",
        [
            "✅ 路线一：我有明确方向",
            "❓ 路线二：探索蓝海类目"
        ],
        help="路线一用于深度分析已知类目；路线二用于扫描蓝海市场"
    )
    
    st.divider()
    
    # 高级阈值调节
    with st.expander("🎛️ 高级阈值", expanded=False):
        st.caption("仅路线二生效，调节市场过滤器标准")
        min_sales = st.number_input("月销量门槛", value=30000, step=5000, help="Top 100月销量总和")
        min_price = st.number_input("客单价门槛 ($)", value=20.0, step=5.0)
        max_reviews = st.number_input("评论壁垒上限", value=500, step=50, help="Top 10平均评论数")
        brand_concentration = st.slider("品牌垄断度上限", 0.1, 1.0, 0.6, 0.05)
    
    st.divider()
    st.caption("💡 数据来源：卖家精灵 / Jungle Scout / Helium 10")

# ==================== 主界面 ====================
st.title("🔍 ABA利基分析工具 v5.0")
st.markdown("*从数据到产品定义 —— AI 全程介入，输出可落地的开发指令*")

# 检查AI连接状态
if st.session_state.ai_client is None:
    st.warning("⚠️ 请先在左侧侧边栏配置 DeepSeek API Key")

st.divider()

# ==================== 数据上传 ====================
st.subheader("📤 上传数据文件")

col1, col2 = st.columns(2)

with col1:
    sales_file = st.file_uploader(
        "📊 竞品销量/价格快照",
        type=["csv", "xlsx"],
        help="必须包含：ASIN、Title、价格、月销量、评论数"
    )

with col2:
    review_file = st.file_uploader(
        "💬 竞品评论数据（可选）",
        type=["csv", "xlsx"],
        help="用于痛点挖掘，包含：ASIN、评论星级、评论正文"
    )

# ==================== 数据处理 ====================
if sales_file is not None:
    st.divider()
    st.subheader("🔄 数据流水线")
    
    # ----- Step 1: 读取文件 -----
    with st.status("📂 读取数据文件...", expanded=True) as status:
        try:
            if sales_file.name.endswith('.csv'):
                df_raw = pd.read_csv(sales_file)
            else:
                df_raw = pd.read_excel(sales_file)
            
            status.update(label=f"✅ 已读取：{len(df_raw)} 行，{len(df_raw.columns)} 列", state="complete")
        except Exception as e:
            st.error(f"❌ 读取失败: {e}")
            st.stop()
    
    # ----- Step 2: AI列名映射 -----
    with st.status("🤖 AI 列名映射...", expanded=True) as status:
        try:
            mapper = AIColumnMapper()
            mapping_result = mapper.map_columns(df_raw)
            st.session_state.mapping_result = mapping_result
            
            # 应用映射
            df_mapped = mapper.apply_mapping(df_raw, mapping_result)
            mapping_summary = mapper.get_mapping_summary(mapping_result)
            
            status.update(label=f"✅ 映射完成：自动映射 {mapping_summary['auto_mapped']} 列", state="complete")
        except Exception as e:
            st.error(f"❌ 映射失败: {e}")
            st.stop()
    
    # 显示映射详情
    with st.expander("📋 查看列名映射详情"):
        mapping_summary = mapper.get_mapping_summary(mapping_result)
        mapping_df = pd.DataFrame(mapping_summary["mapping_table"])
        st.dataframe(mapping_df, use_container_width=True)
        st.caption(f"✅ 自动映射: {mapping_summary['auto_mapped']} | ⚠️ 需确认: {mapping_summary['needs_confirmation']} | ❌ 未识别: {mapping_summary['unmapped']}")
    
    # ----- Step 3: 属性提取与标准化 -----
    with st.status("🏷️ 属性提取与标准化...", expanded=True) as status:
        try:
            normalizer = AttributeNormalizer("config.yaml")
            
            if "title" in df_mapped.columns:
                df_processed = normalizer.normalize_df_attributes(df_mapped, "title")
                attr_summary = normalizer.get_attribute_summary(df_processed)
                st.session_state.df_processed = df_processed
                
                # 显示属性统计
                attr_count = len([k for k, v in attr_summary.items() if v["unique_count"] > 0])
                status.update(label=f"✅ 识别到 {attr_count} 个属性维度", state="complete")
            else:
                st.warning("⚠️ 数据中缺少 'title' 列，跳过属性提取")
                df_processed = df_mapped
                st.session_state.df_processed = df_processed
                status.update(label="⚠️ 未找到标题列，跳过属性提取", state="complete")
                
        except Exception as e:
            st.error(f"❌ 属性提取失败: {e}")
            st.stop()
    
    # 显示属性分布
    if "attr_尺寸_标准" in df_processed.columns or "attr_颜色_标准" in df_processed.columns:
        with st.expander("📊 属性分布预览"):
            for attr in ["尺寸", "颜色", "材质", "款式"]:
                col_name = f"attr_{attr}"
                if col_name in df_processed.columns:
                    counts = df_processed[col_name].dropna().value_counts()
                    if len(counts) > 0:
                        st.write(f"**{attr}** (共 {len(counts)} 种值)")
                        st.write(pd.DataFrame({
                            "值": counts.index[:10],
                            "出现次数": counts.values[:10]
                        }))
                        st.caption(f"覆盖率: {(df_processed[col_name].notna().sum() / len(df_processed)) * 100:.1f}%")
    
    # ==================== 路线分流 ====================
    st.divider()
    
    if "❓ 路线二：探索蓝海类目" in route:
        # ----- 路线二：市场准入过滤器 -----
        st.subheader("🔍 市场准入过滤器")
        
        with st.status("📊 运行市场过滤...", expanded=True) as status:
            try:
                filter = MarketFilter("config.yaml")
                filter.update_thresholds(
                    min_monthly_sales=min_sales,
                    min_avg_price=min_price,
                    max_avg_review_count=max_reviews,
                    max_brand_concentration=brand_concentration
                )
                
                result = filter.filter_class(df_processed)
                
                status.update(label="✅ 过滤完成", state="complete")
            except Exception as e:
                st.error(f"❌ 过滤失败: {e}")
                st.stop()
        
        # 显示结果
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
            status_icon = "✅" if indicator.passed else "❌"
            st.metric(
                label=f"{status_icon} {indicator.name}",
                value=indicator.message,
                delta="达标" if indicator.passed else f"需 ≥ {indicator.threshold}" if "≥" in indicator.message else f"需 ≤ {indicator.threshold}"
            )
        
        if not result.passed:
            st.warning("🔴 该市场未通过准入过滤，建议切换类目或调整阈值")
            st.stop()
        else:
            st.success("🎯 该市场符合蓝海特征，建议进入路线一深度分析")
            st.info("💡 如需深度分析，请切换至【路线一】模式")
    
    else:
        # ----- 路线一：深度竞品分析 -----
        st.subheader("🔍 深度竞品分析")
        
        # 1. 价格带分析
        st.write("### 💰 价格带分析")
        if "price" in df_processed.columns:
            prices = df_processed["price"].dropna()
            if len(prices) > 5:
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
                    if diff > sorted_prices[i-1] * 0.2:
                        gaps.append({
                            "断层起始": f"${sorted_prices[i-1]:.0f}",
                            "断层结束": f"${sorted_prices[i]:.0f}",
                            "差价": f"${diff:.0f}",
                            "涨幅": f"{diff / sorted_prices[i-1] * 100:.0f}%"
                        })
                
                if gaps:
                    st.success(f"💰 发现 {len(gaps)} 个价格断层")
                    st.dataframe(pd.DataFrame(gaps[:5]), use_container_width=True)
                else:
                    st.info("未发现明显价格断层，市场定价较为连续")
        
        # 2. 评论痛点挖掘
        if review_file is not None:
            st.write("### 🔧 差评痛点挖掘")
            
            with st.status("📖 分析评论数据...", expanded=True) as status:
                try:
                    if review_file.name.endswith('.csv'):
                        reviews_df = pd.read_csv(review_file)
                    else:
                        reviews_df = pd.read_excel(review_file)
                    
                    # 映射评论列
                    review_mapper = AIColumnMapper()
                    review_mapping = review_mapper.map_columns(reviews_df)
                    reviews_mapped = review_mapper.apply_mapping(reviews_df, review_mapping)
                    
                    # 分析痛点
                    analyzer = CommentAnalyzer(st.session_state.ai_client)
                    pain_points = analyzer.extract_pain_points(reviews_mapped, min_mentions=3)
                    st.session_state.pain_points = pain_points
                    
                    status.update(label=f"✅ 发现 {len(pain_points)} 个痛点", state="complete")
                except Exception as e:
                    st.error(f"❌ 分析失败: {e}")
                    st.stop()
            
            if pain_points:
                # 显示痛点列表
                pain_data = []
                for pp in pain_points[:10]:
                    pain_data.append({
                        "痛点": pp.keyword,
                        "提及次数": pp.mention_count,
                        "提及率": f"{pp.mention_rate:.1%}",
                        "代表评论": pp.sample_reviews[0][:80] + "..." if pp.sample_reviews else "",
                    })
                
                st.dataframe(pd.DataFrame(pain_data), use_container_width=True)
                
                # AI生成解决方案
                if st.session_state.ai_client and st.button("🤖 AI生成解决方案", use_container_width=True):
                    with st.spinner("AI 正在生成建议..."):
                        for pp in pain_points[:5]:
                            if pp.mention_rate > 0.05:
                                solutions = st.session_state.ai_client.generate_solutions(
                                    pain_point=pp.keyword,
                                    product_name="该类目产品"
                                )
                                pp.suggested_solution = "; ".join(solutions) if solutions else None
                    
                    # 显示带建议的痛点
                    st.write("#### 💡 AI 改良建议")
                    for pp in pain_points[:5]:
                        if pp.suggested_solution:
                            st.info(f"**{pp.keyword}** (提及率 {pp.mention_rate:.1%})\n→ {pp.suggested_solution}")
            else:
                st.info("未发现明显痛点，或评论数量不足")
        
        # 3. 趋势分析
        st.write("### 📈 趋势分析")
        st.caption("需要上传包含多个月份/季度历史数据的文件才能进行趋势分析")
        
        # 检查是否有时间序列数据
        date_cols = [c for c in df_processed.columns if c.startswith("202") or c.startswith("20")]
        if date_cols:
            with st.status("📊 分析趋势...", expanded=True) as status:
                try:
                    analyzer = TrendAnalyzer()
                    # 将数据转换为长格式
                    df_melted = df_processed.melt(
                        id_vars=[c for c in df_processed.columns if c not in date_cols],
                        value_vars=date_cols,
                        var_name="date",
                        value_name="sales"
                    )
                    
                    # 如果有属性列，按属性分组分析
                    if "attr_尺寸_标准" in df_processed.columns:
                        result = analyzer.analyze_sales_trend(
                            df_melted, "date", "sales", "attr_尺寸_标准"
                        )
                        if "grouped" in result:
                            st.write("**各尺寸趋势**")
                            trend_data = []
                            for group, info in result["grouped"].items():
                                trend_data.append({
                                    "属性": group,
                                    "趋势": info["trend_type"],
                                    "最新销量": info["latest_value"] if info["latest_value"] else 0
                                })
                            st.dataframe(pd.DataFrame(trend_data), use_container_width=True)
                    else:
                        result = analyzer.analyze_sales_trend(
                            df_melted, "date", "sales", None
                        )
                        st.metric("整体趋势", result.get("trend_type", "数据不足"))
                    
                    status.update(label="✅ 趋势分析完成", state="complete")
                except Exception as e:
                    st.warning(f"趋势分析跳过: {e}")
        else:
            st.info("📅 未检测到日期列，请上传包含月度历史数据的文件")
        
        # ==================== 生成报告 ====================
        st.divider()
        
        if st.button("🚀 生成产品定义报告", type="primary", use_container_width=True):
            st.subheader("📄 产品定义报告")
            
            with st.spinner("AI 正在生成报告..."):
                # 准备数据
                price_gap_analysis = {
                    "avg_price": df_processed["price"].mean() if "price" in df_processed.columns else 0
                }
                
                # 属性机会
                attribute_opportunities = {}
                if "attr_尺寸_标准" in df_processed.columns:
                    sizes = df_processed["attr_尺寸_标准"].dropna().value_counts()
                    if len(sizes) > 0:
                        attribute_opportunities["尺寸"] = {
                            "top_values": sizes.index[:3].tolist(),
                            "top_opportunity": sizes.index[0] if len(sizes) > 0 else ""
                        }
                
                if "attr_颜色_标准" in df_processed.columns:
                    colors = df_processed["attr_颜色_标准"].dropna().value_counts()
                    if len(colors) > 0:
                        attribute_opportunities["颜色"] = {
                            "top_values": colors.index[:3].tolist()
                        }
                
                # 生成报告
                report_gen = ReportGenerator(st.session_state.ai_client)
                definition = report_gen.generate_product_definition_report(
                    class_name="该类目",
                    price_gap_analysis=price_gap_analysis,
                    pain_points=st.session_state.pain_points,
                    attribute_opportunities=attribute_opportunities,
                    trend_analysis={}
                )
                
                # 显示HTML报告
                html_report = report_gen.format_report_html(definition, {})
                st.markdown(html_report, unsafe_allow_html=True)

# ==================== 页脚 ====================
st.divider()
st.caption("🔍 ABA利基分析工具 v5.0 | 产品开发决策引擎 | 数据驱动 · AI赋能")
st.caption("📌 如有问题，请检查：1) 数据文件格式 2) API Key 配置 3) config.yaml 是否存在")
