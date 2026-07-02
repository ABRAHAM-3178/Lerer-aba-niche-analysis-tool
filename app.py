"""
ABA利基分析工具 v5.0 - 完整版（修复列名重复问题）
产品开发决策引擎：从数据到产品定义，AI全程介入
核心特性：AI驱动的智能数据清洗
"""

import streamlit as st
import pandas as pd
import yaml
import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块（确保这些文件存在于 core/ 目录）
from utils.ai_client import create_deepseek_client, AIClient
from core.market_filter import MarketFilter
from core.trend import TrendAnalyzer
from core.report_generator import ReportGenerator

# ========== 工具函数：确保列名唯一 ==========
def ensure_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    """检查并修复重复列名，添加后缀 _1, _2 等"""
    cols = df.columns.tolist()
    seen = {}
    new_cols = []
    for col in cols:
        if col not in seen:
            seen[col] = 0
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
    df.columns = new_cols
    return df


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="ABA利基分析工具 v5.0",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 会话状态 ====================
if "ai_client" not in st.session_state:
    st.session_state.ai_client = None
if "df_processed" not in st.session_state:
    st.session_state.df_processed = None
if "pain_points" not in st.session_state:
    st.session_state.pain_points = []

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("🔍 ABA利基分析")
    st.caption("v5.0 · AI驱动的数据清洗与分析")
    st.divider()
    
    with st.expander("🤖 AI 配置", expanded=True):
        api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
        if st.button("连接 AI", use_container_width=True):
            if api_key:
                try:
                    st.session_state.ai_client = create_deepseek_client(api_key=api_key)
                    st.success("✅ AI 已连接")
                except Exception as e:
                    st.error(f"连接失败: {e}")
            else:
                st.warning("请输入 API Key")
    
    if st.session_state.ai_client:
        st.success("AI 就绪")
    else:
        st.warning("请配置 API Key")
    
    st.divider()
    route = st.radio(
        "📋 选择分析模式",
        ["✅ 路线一：我有明确方向", "❓ 路线二：探索蓝海类目"]
    )
    st.divider()
    
    with st.expander("🎛️ 高级阈值", expanded=False):
        min_sales = st.number_input("月销量门槛", value=30000, step=5000)
        min_price = st.number_input("客单价门槛 ($)", value=20.0, step=5.0)
        max_reviews = st.number_input("评论壁垒上限", value=500, step=50)
        brand_concentration = st.slider("品牌垄断度上限", 0.1, 1.0, 0.6, 0.05)
    
    st.caption("💡 AI 自动识别：列名映射、属性提取、数据标准化")


# ==================== AI 智能清洗函数 ====================

def ai_detect_columns(ai_client: AIClient, df: pd.DataFrame) -> Dict[str, str]:
    """AI识别列名含义，返回映射字典"""
    sample_data = df.head(3).to_dict(orient='records')
    column_names = df.columns.tolist()
    
    prompt = f"""
    你是数据清洗专家。分析以下表格，识别每一列的含义。
    列名列表：{column_names}
    数据样例（前3行）：{json.dumps(sample_data, ensure_ascii=False, indent=2)[:3000]}

    请映射到标准字段：asin, parent_asin, title, price, monthly_sales, monthly_revenue,
    review_count, rating, bsr_rank, category, review_date, review_star, review_body,
    review_title, verified_purchase, keyword, search_volume, unknown。

    返回JSON：{{"mapping": {{"原始列名": "标准字段名"}} }}
    """
    try:
        response = ai_client.chat_json(prompt, temperature=0.1)
        return response.get("mapping", {})
    except Exception as e:
        st.error(f"AI列名识别失败: {e}")
        return {}


def ai_extract_attributes(ai_client: AIClient, titles: List[str]) -> List[Dict]:
    """AI从标题中提取属性"""
    sample_titles = titles[:50]
    prompt = f"""
    你是数据标注专家。从以下商品标题中提取属性（尺寸、颜色、材质、款式）。
    颜色标准化：Black→黑色，White→白色，Light Walnut→浅胡桃色，Dark Walnut→深胡桃色，
    Rustic Brown→棕色，Oak→橡木色。

    标题列表：{json.dumps(sample_titles, ensure_ascii=False, indent=2)[:4000]}

    返回JSON：{{"results": [{{"title": "原标题", "尺寸": "...", "颜色": "...", "材质": "...", "款式": "..."}}]}}
    """
    try:
        response = ai_client.chat_json(prompt, temperature=0.2)
        return response.get("results", [])
    except Exception as e:
        st.error(f"AI属性提取失败: {e}")
        return []


def ai_detect_data_type(ai_client: AIClient, df: pd.DataFrame) -> Dict:
    """AI判断数据类型（单类目深度 vs 多类目广度）"""
    sample = df.head(10).to_dict(orient='records')
    prompt = f"""
    判断以下数据是「单类目深度数据」还是「多类目广度数据」。
    数据样例：{json.dumps(sample, ensure_ascii=False, indent=2)[:3000]}

    返回JSON：{{"data_type": "single_category"或"multi_category", "category_name": "...", "categories": [...], "confidence": 0.0-1.0, "reasoning": "..."}}
    """
    try:
        return ai_client.chat_json(prompt, temperature=0.2)
    except Exception as e:
        st.error(f"AI数据类型判断失败: {e}")
        return {"data_type": "unknown"}


def ai_normalize_values(ai_client: AIClient, df: pd.DataFrame, column: str) -> Dict:
    """AI标准化某一列的值"""
    unique_values = df[column].dropna().unique().tolist()
    prompt = f"""
    标准化以下{column}列的值，合并相似项。
    原始值：{json.dumps(unique_values, ensure_ascii=False, indent=2)[:2000]}
    返回JSON：{{"mapping": {{"原始值": "标准化值"}}}}
    """
    try:
        response = ai_client.chat_json(prompt, temperature=0.1)
        return response.get("mapping", {})
    except Exception as e:
        st.error(f"AI标准化失败: {e}")
        return {}


# ==================== 主界面 ====================
st.title("🔍 ABA利基分析工具 v5.0")
st.markdown("*AI 驱动的智能数据清洗 —— 上传任何格式的数据，AI 自动识别、提取、标准化*")

if st.session_state.ai_client is None:
    st.warning("⚠️ 请先在左侧侧边栏配置 DeepSeek API Key")
else:
    st.success("✅ AI 已就绪，可以开始数据清洗")

st.divider()

with st.expander("📖 数据获取指南（必读）- 点击展开", expanded=False):
    st.markdown("""
    ### 🎯 AI 能帮你做什么？
    上传任意来源的数据表格，AI 会自动：
    1. **识别每一列的含义**（不管列名是什么语言）
    2. **从标题中提取属性**（尺寸、颜色、材质、款式）
    3. **标准化数据值**（"Light Walnut" → "浅胡桃色"）
    4. **判断数据类型**（单类目深度 vs 多类目广度）

    ### 📊 支持的数据来源
    | 工具 | 导出路径 |
    |:---|:---|
    | 卖家精灵 | 工具 → 查竞品 → 导出 |
    | Jungle Scout | Extension → Export |
    | Helium 10 | Tools → Black Box → Export |

    ### ✅ 必要字段
    商品标题（用于属性提取）、价格、月销量、评论数、ASIN（推荐）
    """)

st.divider()

st.subheader("📤 上传数据文件")
if "路线二" in route:
    st.info("📌 路线二：上传多个类目的 Top 10-20 汇总数据（用于扫描蓝海）")
else:
    st.info("📌 路线一：上传目标类目的 Top 50-100 竞品数据（用于深度分析）")

col1, col2 = st.columns(2)
with col1:
    sales_file = st.file_uploader("📊 竞品数据文件", type=["csv", "xlsx"])
with col2:
    review_file = st.file_uploader("💬 评论数据文件（可选）", type=["csv", "xlsx"])

# ==================== AI 智能清洗流程 ====================
if sales_file is not None and st.session_state.ai_client is not None:
    st.divider()
    st.subheader("🤖 AI 智能数据清洗")
    
    # 读取文件
    try:
        if sales_file.name.endswith('.csv'):
            df_raw = pd.read_csv(sales_file)
        else:
            df_raw = pd.read_excel(sales_file)
        st.info(f"📄 已读取：{len(df_raw)} 行，{len(df_raw.columns)} 列")
    except Exception as e:
        st.error(f"❌ 文件读取失败: {e}")
        st.stop()
    
    # ---- Step 1: AI 列名映射 ----
    with st.status("🔍 Step 1: AI 识别列名...", expanded=True) as status:
        mapping = ai_detect_columns(st.session_state.ai_client, df_raw)
        if mapping:
            rename_map = {k: v for k, v in mapping.items() if v and v != "unknown"}
            df_mapped = df_raw.rename(columns=rename_map)
            # 确保列名唯一
            df_mapped = ensure_unique_columns(df_mapped)
            status.update(label=f"✅ 识别了 {len(rename_map)} 列", state="complete")
            with st.expander("📋 列名映射结果"):
                st.json(mapping)
        else:
            df_mapped = df_raw.copy()
            df_mapped = ensure_unique_columns(df_mapped)
            status.update(label="⚠️ 列名识别失败，使用原始列名", state="complete")
    
    # ---- Step 2: AI 数据类型判断 ----
    with st.status("🧠 Step 2: AI 分析数据类型...", expanded=True) as status:
        data_type_info = ai_detect_data_type(st.session_state.ai_client, df_mapped)
        status.update(label=f"✅ 判断完成：{data_type_info.get('data_type', 'unknown')}", state="complete")
        with st.expander("📋 数据类型分析"):
            st.json(data_type_info)
    
    # ---- Step 3: AI 属性提取 ----
    # 查找标题列
    title_col = None
    for col in df_mapped.columns:
        if "title" in col.lower() or "标题" in col:
            title_col = col
            break
    if title_col:
        with st.status("🏷️ Step 3: AI 提取属性（尺寸/颜色/材质）...", expanded=True) as status:
            titles = df_mapped[title_col].dropna().tolist()
            attr_results = ai_extract_attributes(st.session_state.ai_client, titles)
            if attr_results:
                attr_df = pd.DataFrame(attr_results)
                # 合并到主数据框
                for attr_col in ["尺寸", "颜色", "材质", "款式"]:
                    if attr_col in attr_df.columns:
                        new_col = f"AI_{attr_col}"
                        df_mapped[new_col] = None
                        for i, row in attr_df.iterrows():
                            if i < len(df_mapped):
                                df_mapped.loc[i, new_col] = row.get(attr_col)
                df_mapped = ensure_unique_columns(df_mapped)
                status.update(label=f"✅ 提取了 {len(attr_results)} 条属性", state="complete")
                with st.expander("📋 属性提取样例"):
                    st.dataframe(attr_df.head(10))
            else:
                status.update(label="⚠️ 属性提取失败", state="complete")
    
    # ---- Step 4: AI 标准化颜色 ----
    color_cols = [c for c in df_mapped.columns if "颜色" in c or "color" in c.lower()]
    if color_cols:
        with st.status("🎨 Step 4: AI 标准化颜色值...", expanded=True) as status:
            color_col = color_cols[0]
            color_mapping = ai_normalize_values(st.session_state.ai_client, df_mapped, color_col)
            if color_mapping:
                df_mapped[f"{color_col}_标准化"] = df_mapped[color_col].map(lambda x: color_mapping.get(x, x))
                df_mapped = ensure_unique_columns(df_mapped)
                status.update(label=f"✅ 标准化了 {len(color_mapping)} 个颜色值", state="complete")
                with st.expander("📋 颜色标准化映射"):
                    st.json(color_mapping)
            else:
                status.update(label="⚠️ 颜色标准化失败", state="complete")
    
    # ---- 保存结果 ----
    st.session_state.df_processed = df_mapped
    
    st.success("✅ AI 数据清洗完成！")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("原始列数", len(df_raw.columns))
    with col2:
        st.metric("处理后列数", len(df_mapped.columns))
    
    with st.expander("📊 查看清洗后的数据"):
        # 再次确保列名唯一，并显示前20行
        display_df = ensure_unique_columns(df_mapped.head(20))
        st.dataframe(display_df, use_container_width=True)


# ==================== 路线分析 ====================
if st.session_state.df_processed is not None:
    st.divider()
    df = st.session_state.df_processed
    
    if "路线二" in route:
        st.subheader("🔍 蓝海类目扫描")
        # 尝试显示类目分布
        category_col = None
        for col in df.columns:
            if "category" in col.lower() or "类目" in col:
                category_col = col
                break
        if category_col:
            counts = df[category_col].value_counts()
            st.bar_chart(counts.head(10))
        
        # 运行市场过滤器
        try:
            filter = MarketFilter("config.yaml")
            filter.update_thresholds(
                min_monthly_sales=min_sales,
                min_avg_price=min_price,
                max_avg_review_count=max_reviews,
                max_brand_concentration=brand_concentration
            )
            if "price" in df.columns and "monthly_sales" in df.columns and "review_count" in df.columns:
                result = filter.filter_class(df)
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.success("✅ 市场准入") if result.passed else st.error("❌ 市场淘汰")
                with col2:
                    st.write(result.recommendation)
                for indicator in result.indicators:
                    st.metric(
                        label=f"{'✅' if indicator.passed else '❌'} {indicator.name}",
                        value=indicator.message,
                        delta="达标" if indicator.passed else "需调整"
                    )
        except Exception as e:
            st.warning(f"市场过滤跳过: {e}")
    
    else:
        st.subheader("🔍 深度竞品分析")
        
        # 价格带分析
        if "price" in df.columns:
            prices = df["price"].dropna()
            if len(prices) > 5:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最低价", f"${prices.min():.0f}")
                col2.metric("中位数", f"${prices.median():.0f}")
                col3.metric("75分位", f"${prices.quantile(0.75):.0f}")
                col4.metric("最高价", f"${prices.max():.0f}")
        
        # 属性分布
        for attr in ["AI_尺寸", "AI_颜色", "AI_材质", "AI_款式"]:
            if attr in df.columns:
                counts = df[attr].dropna().value_counts()
                if len(counts) > 0:
                    st.write(f"### 📊 {attr.replace('AI_', '')}分布")
                    st.dataframe(pd.DataFrame({"值": counts.index[:10], "出现次数": counts.values[:10]}), use_container_width=True)
        
        # 生成报告按钮
        st.divider()
        if st.button("🚀 生成产品定义报告", type="primary", use_container_width=True):
            st.subheader("📄 产品定义报告")
            with st.spinner("AI 正在生成报告..."):
                price_gap_analysis = {"avg_price": df["price"].mean() if "price" in df.columns else 0}
                attribute_opportunities = {}
                if "AI_尺寸" in df.columns:
                    sizes = df["AI_尺寸"].dropna().value_counts()
                    if len(sizes) > 0:
                        attribute_opportunities["尺寸"] = {"top_values": sizes.index[:3].tolist()}
                if "AI_颜色" in df.columns:
                    colors = df["AI_颜色"].dropna().value_counts()
                    if len(colors) > 0:
                        attribute_opportunities["颜色"] = {"top_values": colors.index[:3].tolist()}
                
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
st.caption("🔍 ABA利基分析工具 v5.0 | AI驱动数据清洗 | 数据驱动 · AI赋能")
