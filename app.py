"""
ABA利基分析工具 v5.0 - 完整版
产品开发决策引擎：从数据到产品定义，AI全程介入
核心特性：AI驱动的智能数据清洗（列名映射、属性提取、数据标准化）
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

# 将项目根目录加入路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from utils.ai_client import create_deepseek_client, AIClient
from core.market_filter import MarketFilter
from core.trend import TrendAnalyzer
from core.report_generator import ReportGenerator

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
if "cleaning_report" not in st.session_state:
    st.session_state.cleaning_report = None
if "pain_points" not in st.session_state:
    st.session_state.pain_points = []
if "step" not in st.session_state:
    st.session_state.step = "upload"  # upload | cleaning | mapping | analyzing | done

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("🔍 ABA利基分析")
    st.caption("v5.0 · AI驱动的数据清洗与分析")
    
    st.divider()
    
    # AI配置
    with st.expander("🤖 AI 配置", expanded=True):
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
    
    # 显示连接状态
    if st.session_state.ai_client:
        st.success("AI 就绪")
    else:
        st.warning("请配置 API Key")
    
    st.divider()
    
    # 模式选择
    route = st.radio(
        "📋 选择分析模式",
        ["✅ 路线一：我有明确方向", "❓ 路线二：探索蓝海类目"],
        help="路线一：已知类目，深度分析；路线二：未知方向，扫描蓝海"
    )
    
    st.divider()
    
    with st.expander("🎛️ 高级阈值", expanded=False):
        min_sales = st.number_input("月销量门槛", value=30000, step=5000)
        min_price = st.number_input("客单价门槛 ($)", value=20.0, step=5.0)
        max_reviews = st.number_input("评论壁垒上限", value=500, step=50)
        brand_concentration = st.slider("品牌垄断度上限", 0.1, 1.0, 0.6, 0.05)
    
    st.divider()
    st.caption("💡 AI 自动识别：列名映射、属性提取、数据标准化")


# ==================== AI 智能清洗函数 ====================

def ai_detect_columns(ai_client: AIClient, df: pd.DataFrame) -> Dict[str, str]:
    """使用AI识别每一列的含义，返回列名映射"""
    
    # 取前3行和列名作为样本
    sample_data = df.head(3).to_dict(orient='records')
    column_names = df.columns.tolist()
    
    prompt = f"""
    你是一位数据清洗专家。请分析以下表格数据，识别每一列的含义。

    列名列表：{column_names}

    数据样例（前3行）：
    {json.dumps(sample_data, ensure_ascii=False, indent=2)[:3000]}

    请识别每一列的含义，映射到以下标准字段之一：
    - asin: 商品唯一标识（10位字母数字组合，通常以B0开头）
    - parent_asin: 父体ASIN
    - title: 商品标题/名称
    - price: 售价（数字，可能带$符号）
    - monthly_sales: 月销量（数字）
    - monthly_revenue: 月销售额（数字）
    - review_count: 评论数（数字）
    - rating: 平均评分（1-5之间的数字）
    - bsr_rank: Best Seller排名
    - category: 类目名称
    - review_date: 评论日期
    - review_star: 评论星级（1-5）
    - review_body: 评论正文
    - review_title: 评论标题
    - verified_purchase: 是否验证购买
    - keyword: 关键词
    - search_volume: 搜索量
    - unknown: 无法识别

    请返回JSON格式：
    {{
        "mapping": {{
            "原始列名1": "标准字段名1",
            "原始列名2": "标准字段名2"
        }},
        "notes": "任何观察说明"
    }}
    """

    try:
        response = ai_client.chat_json(prompt, temperature=0.1)
        mapping = response.get("mapping", {})
        return mapping
    except Exception as e:
        st.error(f"AI列名识别失败: {e}")
        return {}


def ai_extract_attributes(ai_client: AIClient, titles: List[str]) -> Dict[str, Dict]:
    """使用AI从标题中批量提取属性（尺寸、颜色、材质等）"""
    
    # 取前50个标题，避免Token超限
    sample_titles = titles[:50]
    
    prompt = f"""
    你是一位数据标注专家。请从以下商品标题中提取关键属性。

    商品标题列表（共{len(sample_titles)}个）：
    {json.dumps(sample_titles, ensure_ascii=False, indent=2)[:4000]}

    请为每个标题提取以下属性（如果有）：
    1. 尺寸（如：48寸、55寸、63寸、Large、XL等）
    2. 颜色（如：黑色、白色、棕色、浅胡桃色等）
    3. 材质（如：木材、金属、玻璃、塑料等）
    4. 款式/类型（如：L形、U形、升降、电竞等）

    同时，请对颜色进行标准化：
    - Black / Pure Black / Carbon Fiber Black → 黑色
    - White / Pure White / Soft White → 白色
    - Light Walnut / Walnut / Natural → 浅胡桃色
    - Dark Walnut / Black Walnut → 深胡桃色
    - Rustic Brown / Vintage Brown / Brown → 棕色
    - Oak / Natural Oak → 橡木色

    请返回JSON格式：
    {{
        "results": [
            {{
                "title": "原标题",
                "尺寸": "提取的值",
                "颜色": "标准化后的颜色",
                "材质": "提取的材质",
                "款式": "提取的款式"
            }}
        ],
        "color_standardization_notes": "颜色标准化的说明"
    }}
    """

    try:
        response = ai_client.chat_json(prompt, temperature=0.2)
        results = response.get("results", [])
        return results
    except Exception as e:
        st.error(f"AI属性提取失败: {e}")
        return []


def ai_detect_data_type(ai_client: AIClient, df: pd.DataFrame) -> Dict:
    """使用AI判断数据是路线一（单类目深度）还是路线二（多类目广度）"""
    
    sample = df.head(10).to_dict(orient='records')
    
    prompt = f"""
    你是一位数据分析专家。请判断以下数据属于哪种类型：

    数据样例（前10行）：
    {json.dumps(sample, ensure_ascii=False, indent=2)[:3000]}

    请判断：
    1. 这是「单类目深度数据」还是「多类目广度数据」？
       - 单类目深度：所有商品属于同一个细分类目（如都是升降桌），数据量大（50-100行）
       - 多类目广度：商品来自多个不同类目（如宠物用品、办公家具、电子产品混合），数据量小（10-30行）

    2. 如果是单类目深度数据，识别出该类目名称
    3. 如果是多类目广度数据，列出涉及的类目列表

    返回JSON格式：
    {{
        "data_type": "single_category" 或 "multi_category",
        "category_name": "类目名称（如果是单类目）",
        "categories": ["类目1", "类目2"]（如果是多类目）,
        "confidence": 0.0-1.0,
        "reasoning": "判断理由"
    }}
    """

    try:
        response = ai_client.chat_json(prompt, temperature=0.2)
        return response
    except Exception as e:
        st.error(f"AI数据类型判断失败: {e}")
        return {"data_type": "unknown"}


def ai_normalize_values(ai_client: AIClient, df: pd.DataFrame, column: str) -> Dict:
    """使用AI标准化某一列的值（如颜色标准化）"""
    
    unique_values = df[column].dropna().unique().tolist()
    
    prompt = f"""
    你是一位数据标准化专家。请对以下{column}列的值进行标准化。

    原始值列表：
    {json.dumps(unique_values, ensure_ascii=False, indent=2)[:2000]}

    请将相似的值合并为标准值。
    例如：["Black", "Pure Black", "Carbon Fiber Black", "Black Top"] → 全部标准化为 "黑色"
          ["Light Walnut", "Walnut", "Natural"] → "浅胡桃色"
          ["48 inch", "48in", "48 x 24"] → "48寸"

    返回JSON格式：
    {{
        "mapping": {{
            "原始值1": "标准化值1",
            "原始值2": "标准化值2"
        }},
        "notes": "标准化的说明"
    }}
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

# ==================== 数据获取指南 ====================
with st.expander("📖 数据获取指南（必读）- 点击展开", expanded=False):
    st.markdown("""
    ### 🎯 AI 能帮你做什么？

    上传任意来源的数据表格，AI 会自动：
    1. **识别每一列的含义**（不管列名是什么语言）
    2. **从标题中提取属性**（尺寸、颜色、材质、款式）
    3. **标准化数据值**（"Light Walnut" → "浅胡桃色"）
    4. **判断数据类型**（单类目深度 vs 多类目广度）

    ### 📊 支持的数据来源

    | 工具 | 导出路径 | 说明 |
    |:---|:---|:---|
    | 卖家精灵 | 工具 → 查竞品 → 导出 | 最推荐 |
    | Jungle Scout | Extension → Export | 需要插件 |
    | Helium 10 | Tools → Black Box → Export | 需订阅 |
    | Amazon BSR | 手动复制 | 备选方案 |

    ### ✅ 必要字段

    确保数据包含这些列（列名不限，AI自动识别）：
    - 商品标题（用于属性提取）
    - 价格
    - 月销量
    - 评论数
    - ASIN（强烈推荐）

    ### 💬 评论数据（可选）

    如需痛点挖掘，请额外上传评论数据：
    - 评论星级
    - 评论正文
    """)

st.divider()

# ==================== 数据上传 ====================
st.subheader("📤 上传数据文件")

# 根据路线显示不同的上传说明
if "路线二" in route:
    st.info("""
    **📌 路线二：上传多个类目的 Top 10-20 汇总数据**
    - 用于扫描对比哪个类目最有潜力
    - 数据应包含不同的产品线
    - AI 会自动识别和分类
    """)
else:
    st.info("""
    **📌 路线一：上传目标类目的 Top 50-100 竞品数据**
    - 用于深度分析该类目
    - 数据应来自同一个细分类目
    - AI 会自动识别类目名称
    """)

col1, col2 = st.columns(2)

with col1:
    sales_file = st.file_uploader(
        "📊 竞品数据文件",
        type=["csv", "xlsx"],
        help="AI 会自动识别列名和数据格式"
    )

with col2:
    review_file = st.file_uploader(
        "💬 评论数据文件（可选）",
        type=["csv", "xlsx"],
        help="用于痛点挖掘"
    )

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
            # 应用映射
            rename_map = {k: v for k, v in mapping.items() if v and v != "unknown"}
            df_mapped = df_raw.rename(columns=rename_map)
            status.update(label=f"✅ 识别了 {len(rename_map)} 列", state="complete")
            
            # 显示映射结果
            with st.expander("📋 列名映射结果"):
                st.json(mapping)
        else:
            df_mapped = df_raw
            status.update(label="⚠️ 列名识别失败，使用原始列名", state="complete")
    
    # ---- Step 2: AI 数据类型判断 ----
    with st.status("🧠 Step 2: AI 分析数据类型...", expanded=True) as status:
        data_type_info = ai_detect_data_type(st.session_state.ai_client, df_mapped)
        status.update(label=f"✅ 判断完成：{data_type_info.get('data_type', 'unknown')}", state="complete")
        with st.expander("📋 数据类型分析"):
            st.json(data_type_info)
    
    # ---- Step 3: AI 属性提取 ----
    if "title" in df_mapped.columns or any("title" in c.lower() for c in df_mapped.columns):
        with st.status("🏷️ Step 3: AI 提取属性（尺寸/颜色/材质）...", expanded=True) as status:
            # 获取标题列
            title_col = None
            for col in df_mapped.columns:
                if "title" in col.lower() or "标题" in col:
                    title_col = col
                    break
            
            if title_col:
                titles = df_mapped[title_col].dropna().tolist()
                attr_results = ai_extract_attributes(st.session_state.ai_client, titles)
                
                if attr_results:
                    # 将提取的属性合并到DataFrame
                    attr_df = pd.DataFrame(attr_results)
                    # 合并
                    df_with_attrs = df_mapped.copy()
                    # 如果有索引列，匹配合并
                    for attr_col in ["尺寸", "颜色", "材质", "款式"]:
                        if attr_col in attr_df.columns:
                            df_with_attrs[f"AI_{attr_col}"] = None
                            # 简单匹配：按顺序填充
                            for i, row in attr_df.iterrows():
                                if i < len(df_with_attrs):
                                    df_with_attrs.loc[i, f"AI_{attr_col}"] = row.get(attr_col)
                    
                    df_mapped = df_with_attrs
                    status.update(label=f"✅ 提取了 {len(attr_results)} 条属性", state="complete")
                    with st.expander("📋 属性提取样例"):
                        st.dataframe(attr_df.head(10))
                else:
                    status.update(label="⚠️ 属性提取失败", state="complete")
            else:
                status.update(label="⚠️ 未找到标题列，跳过属性提取", state="complete")
    else:
        st.info("未找到标题列，跳过属性提取")
    
    # ---- Step 4: AI 标准化 ----
    # 检测是否有颜色列需要标准化
    color_cols = [c for c in df_mapped.columns if "颜色" in c or "color" in c.lower() or "颜色" in c]
    if color_cols:
        with st.status("🎨 Step 4: AI 标准化颜色值...", expanded=True) as status:
            color_col = color_cols[0]
            color_mapping = ai_normalize_values(st.session_state.ai_client, df_mapped, color_col)
            if color_mapping:
                df_mapped[f"{color_col}_标准化"] = df_mapped[color_col].map(lambda x: color_mapping.get(x, x))
                status.update(label=f"✅ 标准化了 {len(color_mapping)} 个颜色值", state="complete")
                with st.expander("📋 颜色标准化映射"):
                    st.json(color_mapping)
            else:
                status.update(label="⚠️ 颜色标准化失败", state="complete")
    
    # ---- 保存处理结果 ----
    st.session_state.df_processed = df_mapped
    
    # ---- 展示清洗报告 ----
    st.success("✅ AI 数据清洗完成！")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("原始列数", len(df_raw.columns))
    with col2:
        st.metric("处理后列数", len(df_mapped.columns))
    
    with st.expander("📊 查看清洗后的数据"):
        st.dataframe(df_mapped.head(20), use_container_width=True)

# ==================== 路线分析 ====================
if st.session_state.df_processed is not None:
    st.divider()
    df = st.session_state.df_processed
    
    if "路线二" in route:
        # ===== 路线二：市场扫描 =====
        st.subheader("🔍 蓝海类目扫描")
        st.caption("AI 正在分析数据中的类目分布...")
        
        # 检查是否有AI提取的类目信息
        if "category" in df.columns or any("类目" in c for c in df.columns):
            category_col = "category" if "category" in df.columns else [c for c in df.columns if "类目" in c][0]
            category_counts = df[category_col].value_counts()
            st.write("**类目分布：**")
            st.bar_chart(category_counts.head(10))
        
        # 运行市场过滤器
        try:
            filter = MarketFilter("config.yaml")
            filter.update_thresholds(
                min_monthly_sales=min_sales,
                min_avg_price=min_price,
                max_avg_review_count=max_reviews,
                max_brand_concentration=brand_concentration
            )
            
            # 检查是否有必要字段
            if "price" in df.columns and "monthly_sales" in df.columns and "review_count" in df.columns:
                result = filter.filter_class(df)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    if result.passed:
                        st.success("✅ 市场准入")
                    else:
                        st.error("❌ 市场淘汰")
                with col2:
                    st.write(result.recommendation)
                
                for indicator in result.indicators:
                    st.metric(
                        label=f"{'✅' if indicator.passed else '❌'} {indicator.name}",
                        value=indicator.message,
                        delta="达标" if indicator.passed else "需调整"
                    )
            else:
                st.warning("数据缺少必要字段（price、monthly_sales、review_count），无法运行过滤器")
        except Exception as e:
            st.warning(f"市场过滤跳过: {e}")
    
    else:
        # ===== 路线一：深度分析 =====
        st.subheader("🔍 深度竞品分析")
        
        # 1. 价格带分析
        st.write("### 💰 价格带分析")
        if "price" in df.columns:
            prices = df["price"].dropna()
            if len(prices) > 5:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最低价", f"${prices.min():.0f}")
                col2.metric("中位数", f"${prices.median():.0f}")
                col3.metric("75分位", f"${prices.quantile(0.75):.0f}")
                col4.metric("最高价", f"${prices.max():.0f}")
                
                # 检测价格断层
                sorted_prices = sorted(prices)
                gaps = []
                for i in range(1, len(sorted_prices)):
                    diff = sorted_prices[i] - sorted_prices[i-1]
                    if diff > sorted_prices[i-1] * 0.2:
                        gaps.append({
                            "断层起始": f"${sorted_prices[i-1]:.0f}",
                            "断层结束": f"${sorted_prices[i]:.0f}",
                            "差价": f"${diff:.0f}"
                        })
                if gaps:
                    st.success(f"💰 发现 {len(gaps)} 个价格断层")
                    st.dataframe(pd.DataFrame(gaps[:5]), use_container_width=True)
        
        # 2. 属性分布
        attr_cols = ["AI_尺寸", "AI_颜色", "AI_材质", "AI_款式"]
        for attr in attr_cols:
            if attr in df.columns:
                counts = df[attr].dropna().value_counts()
                if len(counts) > 0:
                    st.write(f"### 📊 {attr.replace('AI_', '')}分布")
                    st.dataframe(pd.DataFrame({
                        "值": counts.index[:10],
                        "出现次数": counts.values[:10]
                    }), use_container_width=True)
    
    # ==================== 生成报告 ====================
    if "路线一" in route:
        st.divider()
        
        if st.button("🚀 生成产品定义报告", type="primary", use_container_width=True):
            st.subheader("📄 产品定义报告")
            
            with st.spinner("AI 正在生成报告..."):
                # 准备数据
                price_gap_analysis = {
                    "avg_price": df["price"].mean() if "price" in df.columns else 0
                }
                
                attribute_opportunities = {}
                if "AI_尺寸" in df.columns:
                    sizes = df["AI_尺寸"].dropna().value_counts()
                    if len(sizes) > 0:
                        attribute_opportunities["尺寸"] = {
                            "top_values": sizes.index[:3].tolist()
                        }
                if "AI_颜色" in df.columns:
                    colors = df["AI_颜色"].dropna().value_counts()
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
st.caption("🔍 ABA利基分析工具 v5.0 | AI驱动数据清洗 | 数据驱动 · AI赋能")
