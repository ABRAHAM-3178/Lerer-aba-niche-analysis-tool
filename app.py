"""
ABA利基分析工具 v5.0 - 完整版
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
from core.comment_analysis import CommentAnalyzer
from core.trend import TrendAnalyzer
from core.report_generator import ReportGenerator
from utils.ai_client import create_deepseek_client

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
        ["✅ 路线一：我有明确方向", "❓ 路线二：探索蓝海类目"],
        help="路线一：已知类目，深度分析；路线二：未知方向，扫描蓝海"
    )
    
    st.divider()
    
    # 高级阈值调节
    with st.expander("🎛️ 高级阈值", expanded=False):
        st.caption("调节市场过滤器标准（路线二核心工具）")
        min_sales = st.number_input("月销量门槛", value=30000, step=5000)
        min_price = st.number_input("客单价门槛 ($)", value=20.0, step=5.0)
        max_reviews = st.number_input("评论壁垒上限", value=500, step=50)
        brand_concentration = st.slider("品牌垄断度上限", 0.1, 1.0, 0.6, 0.05)
    
    st.divider()
    st.caption("💡 数据来源：卖家精灵 / Jungle Scout / Helium 10")

# ==================== 主界面 ====================
st.title("🔍 ABA利基分析工具 v5.0")
st.markdown("*从数据到产品定义 —— AI 全程介入，输出可落地的开发指令*")

if st.session_state.ai_client is None:
    st.info("💡 建议在左侧侧边栏配置 DeepSeek API Key")
else:
    st.success("✅ AI 已就绪")

st.divider()

# ==================== 数据获取指南（完整版） ====================
with st.expander("📖 数据获取指南（必读）- 点击展开", expanded=False):
    st.markdown("""
    ### 🎯 你需要准备什么数据？
    
    根据你选择的路线，需要不同的数据：
    
    ---
    
    ## 📊 路线一：我有明确方向
    
    **你需要：** 目标类目的 Top 100 竞品数据（深度分析用）
    
    **推荐工具：卖家精灵 (SellerSprite)**
    
    **下载步骤：**
    1. 登录卖家精灵 → 「工具」→「查竞品」
    2. 输入目标类目关键词（如：standing desk）
    3. 点击「导出」→「导出当前列表」
    4. 确保包含字段：ASIN、Title、Price、Monthly Sales、Reviews
    
    **备选工具：** Jungle Scout、Helium 10（路径类似）
    
    ---
    
    ## 📊 路线二：探索蓝海类目
    
    **你需要：** 多个类目的 Top 10 汇总数据（广度扫描用）
    
    **方式一：卖家精灵导出多类目数据**
    1. 登录卖家精灵 → 「工具」→「选品精灵」→「类目挖掘」
    2. 查看各大类目下的Top商品数据
    3. 导出多个类目的汇总数据（含ASIN、价格、销量、评论数）
    4. 或者分别导出3-5个候选类目的Top 10数据合并成一个文件
    
    **方式二：使用类目列表（快速测试）**
    1. 从亚马逊BSR页面获取感兴趣的类目名称列表
    2. 手动整理成Excel，参考下面格式
    
    **方式三：BSR榜单扫描**
    1. 打开亚马逊 Best Sellers 页面
    2. 记录5-10个感兴趣的一级/二级类目
    3. 分别进入每个类目，复制Top 10的ASIN
    4. 用卖家精灵批量查询这些ASIN的数据
    
    ---
    
    ### ✅ 数据格式要求
    
    | 要求 | 说明 |
    |:---|:---|
    | 文件格式 | `.csv` 或 `.xlsx` |
    | 必要字段 | ASIN、Title、Price、Monthly Sales、Review Count |
    
    ### 💬 评论数据（可选，两条路线都需要）
    
    从卖家精灵点击ASIN → 评论分析 → 导出评论
    包含：Review Star、Review Body
    
    ---
    
    ### 🚀 快速决策：我需要走哪条路线？
    
    | 你的状态 | 推荐路线 | 需要的数据 |
    |:---|:---|:---|
    | 我知道要卖什么类目 | 路线一 | 该类目Top 100数据 |
    | 我完全不知道卖什么 | 路线二 | 5-10个类目的Top 10汇总数据 |
    | 我有几个候选类目在犹豫 | 路线二 | 这些候选类目的Top 10汇总数据 |
    
    ---
    
    ### 📋 卖家精灵导出字段清单（必须勾选）
    
    | 字段名 | 说明 | 是否必须 |
    |:---|:---|:---:|
    | ASIN | 商品唯一标识 | ✅ 必须 |
    | Title / 商品标题 | 完整标题 | ✅ 必须 |
    | Price / 价格 | 当前售价 | ✅ 必须 |
    | Monthly Sales / 月销量 | 近30天销量 | ✅ 必须 |
    | Reviews / 评论数 | 总评论数 | ✅ 必须 |
    | Rating / 评分 | 平均星级 | ⭐ 强烈推荐 |
    | Parent ASIN | 父体ASIN | ⭐ 推荐 |
    | Category / 类目 | 所在类目 | ⭐ 推荐 |
    
    ### 📅 历史趋势数据（进阶分析）
    
    如需分析销量趋势和市场生命周期，在卖家精灵详情页：
    1. 找到「销量趋势」图表
    2. 切换为「近12个月」
    3. 点击「导出数据」
    4. 确保包含：年月、销量
    
    ### ❓ 常见问题
    
    **Q: 没有卖家精灵账号怎么办？**
    A: 可使用 Jungle Scout 或 Helium 10 替代导出，字段要求相同。
    
    **Q: 导出的列名和工具要求的不一样？**
    A: 工具内置了 AI 智能列名映射，会自动识别不同工具的列名。
    
    **Q: 一定要上传评论数据吗？**
    A: 不是必须的，但强烈推荐。差评痛点是产品差异化的核心来源。
    
    """)

st.divider()

# ==================== 数据上传 ====================
st.subheader("📤 上传数据文件")

# 根据路线显示不同的上传说明
if "路线二" in route:
    st.info("""
    **📌 路线二数据要求：** 上传 **多个类目的 Top 10 汇总数据**
    
    数据应包含不同的类目/产品线，用于扫描对比哪个类目最有潜力。
    
    **示例数据格式：**
    | ASIN | Title | Price | Monthly Sales | Review Count | Category |
    |------|-------|-------|---------------|--------------|----------|
    | B0XXX | ... | $25.99 | 5000 | 320 | Pet Supplies |
    | B0YYY | ... | $39.99 | 3500 | 180 | Office Products |
    
    > 💡 如果只有单个类目的数据，请切换到【路线一】使用
    """)
else:
    st.info("""
    **📌 路线一数据要求：** 上传 **目标类目的 Top 100 竞品数据**
    
    数据应来自同一个细分类目，用于深度分析该市场的价格带、属性机会、痛点等。
    
    > 💡 如果想对比多个类目，请切换到【路线二】使用
    """)

col1, col2 = st.columns(2)

with col1:
    sales_file = st.file_uploader(
        "📊 竞品销量/价格快照",
        type=["csv", "xlsx"],
        help="路线一：单类目Top 100数据；路线二：多类目Top 10汇总数据"
    )

with col2:
    review_file = st.file_uploader(
        "💬 竞品评论数据（可选）",
        type=["csv", "xlsx"],
        help="用于痛点挖掘"
    )

# ==================== 数据处理流水线 ====================
if sales_file is not None:
    st.divider()
    st.subheader("🔄 数据流水线")
    
    # Step 1: 读取文件
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
    
    # Step 2: AI列名映射
    with st.status("🤖 AI 列名映射...", expanded=True) as status:
        try:
            mapper = AIColumnMapper()
            mapping_result = mapper.map_columns(df_raw)
            st.session_state.mapping_result = mapping_result
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
    
    # Step 3: 属性提取与标准化
    with st.status("🏷️ 属性提取与标准化...", expanded=True) as status:
        try:
            normalizer = AttributeNormalizer("config.yaml")
            if "title" in df_mapped.columns:
                df_processed = normalizer.normalize_df_attributes(df_mapped, "title")
                attr_summary = normalizer.get_attribute_summary(df_processed)
                st.session_state.df_processed = df_processed
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
    
    if "路线二" in route:
        # ===== 路线二：市场准入过滤器 =====
        st.subheader("🔍 市场准入过滤器")
        st.caption("正在扫描上传数据中的多个类目/产品，找出最有潜力的方向...")
        
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
            st.metric(
                label=f"{'✅' if indicator.passed else '❌'} {indicator.name}",
                value=indicator.message,
                delta="达标" if indicator.passed else "需调整"
            )
        
        if not result.passed:
            st.warning("🔴 该数据未通过准入过滤，建议：\n1. 扩大类目范围重新上传\n2. 或调整侧边栏阈值")
        else:
            st.success("🎯 发现蓝海机会！建议切换到【路线一】对该方向进行深度分析")
    
    else:
        # ===== 路线一：深度竞品分析 =====
        st.subheader("🔍 深度竞品分析")
        st.caption("正在对目标类目进行深度分析...")
        
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
                    
                    review_mapper = AIColumnMapper()
                    review_mapping = review_mapper.map_columns(reviews_df)
                    reviews_mapped = review_mapper.apply_mapping(reviews_df, review_mapping)
                    
                    analyzer = CommentAnalyzer(st.session_state.ai_client)
                    pain_points = analyzer.extract_pain_points(reviews_mapped, min_mentions=3)
                    st.session_state.pain_points = pain_points
                    
                    status.update(label=f"✅ 发现 {len(pain_points)} 个痛点", state="complete")
                except Exception as e:
                    st.error(f"❌ 分析失败: {e}")
                    st.stop()
            
            if pain_points:
                pain_data = []
                for pp in pain_points[:10]:
                    pain_data.append({
                        "痛点": pp.keyword,
                        "提及次数": pp.mention_count,
                        "提及率": f"{pp.mention_rate:.1%}",
                        "代表评论": pp.sample_reviews[0][:80] + "..." if pp.sample_reviews else "",
                    })
                
                st.dataframe(pd.DataFrame(pain_data), use_container_width=True)
                
                if st.session_state.ai_client and st.button("🤖 AI生成解决方案", use_container_width=True):
                    with st.spinner("AI 正在生成建议..."):
                        for pp in pain_points[:5]:
                            if pp.mention_rate > 0.05:
                                solutions = st.session_state.ai_client.generate_solutions(
                                    pain_point=pp.keyword,
                                    product_name="该类目产品"
                                )
                                pp.suggested_solution = "; ".join(solutions) if solutions else None
                    
                    st.write("#### 💡 AI 改良建议")
                    for pp in pain_points[:5]:
                        if pp.suggested_solution:
                            st.info(f"**{pp.keyword}** (提及率 {pp.mention_rate:.1%})\n→ {pp.suggested_solution}")
            else:
                st.info("未发现明显痛点，或评论数量不足")
        
        # 3. 趋势分析
        st.write("### 📈 趋势分析")
        st.caption("需要上传包含多个月份/季度历史数据的文件才能进行趋势分析")
        
        date_cols = [c for c in df_processed.columns if c.startswith("202") or c.startswith("20")]
        if date_cols:
            with st.status("📊 分析趋势...", expanded=True) as status:
                try:
                    analyzer = TrendAnalyzer()
                    df_melted = df_processed.melt(
                        id_vars=[c for c in df_processed.columns if c not in date_cols],
                        value_vars=date_cols,
                        var_name="date",
                        value_name="sales"
                    )
                    
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
                price_gap_analysis = {
                    "avg_price": df_processed["price"].mean() if "price" in df_processed.columns else 0
                }
                
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
                
                report_gen = ReportGenerator(st.session_state.ai_client)
                definition = report_gen.generate_product_definition_report(
                    class_name="该类目",
                    price_gap_analysis=price_gap_analysis,
                    pain_points=st.session_state.pain_points,
                    attribute_opportunities=attribute_opportunities,
                    trend_analysis={}
                )
                
                html_report = report_gen.format_report_html(definition, {})
                st.markdown(html_report, unsafe_allow_html=True)

# ==================== 页脚 ====================
st.divider()
st.caption("🔍 ABA利基分析工具 v5.0 | 产品开发决策引擎 | 数据驱动 · AI赋能")
