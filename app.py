"""
ABA利基分析工具 v4.0 - AI全流程选品顾问
支持：路径A（类目驱动）+ 路径B（产品驱动）
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

from core.parser import parse_aba_csv
from core.clustering import semantic_clustering
from core.scoring import calculate_10d_scores, assign_weight_level
from core.trend import trend_verification
from core.comment_analysis import analyze_comments
from core.report_generator import generate_excel_report
from core.data_loader import load_keyword_history, load_product_history

# ============ 页面配置 ============
st.set_page_config(
    page_title="ABA利基分析工具 v4.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CSS ============
st.markdown("""
<style>
    .main-header { font-size: 2.8rem; font-weight: 700; color: #1a5276; text-align: center; padding: 1rem 0; }
    .sub-header { font-size: 1.2rem; color: #2c3e50; text-align: center; margin-bottom: 2rem; }
    .path-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        border: 2px solid #e9ecef;
        cursor: pointer;
        transition: all 0.3s;
        height: 100%;
    }
    .path-card:hover { border-color: #1a5276; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .path-card.selected { border-color: #1a5276; background-color: #eaf2f8; }
    .path-card .icon { font-size: 2.5rem; }
    .path-card .title { font-size: 1.3rem; font-weight: 600; margin: 0.5rem 0; }
    .path-card .desc { color: #5d6d7e; font-size: 0.95rem; }
    .badge-s { background-color: #27ae60; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-a { background-color: #2e86c1; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-b { background-color: #f39c12; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-c { background-color: #e67e22; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-d { background-color: #e74c3c; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .data-legend { background-color: #f0f3f5; padding: 0.8rem 1.2rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #1a5276; }
    .data-legend table { width: 100%; font-size: 0.9rem; }
    .data-legend td { padding: 0.2rem 0.8rem 0.2rem 0; }
    .data-legend .field-name { font-weight: 600; color: #1a5276; }
    .data-legend .field-desc { color: #2c3e50; }
    .data-legend .field-meaning { color: #7f8c8d; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ============ Session State 初始化 ============
if "step" not in st.session_state:
    st.session_state.step = 0
if "path" not in st.session_state:
    st.session_state.path = None
if "project_name" not in st.session_state:
    st.session_state.project_name = ""
if "category" not in st.session_state:
    st.session_state.category = ""
if "product_keyword" not in st.session_state:
    st.session_state.product_keyword = ""
if "date_range" not in st.session_state:
    st.session_state.date_range = []
if "merged_keywords" not in st.session_state:
    st.session_state.merged_keywords = None
if "merged_asins" not in st.session_state:
    st.session_state.merged_asins = None
if "aba_preview" not in st.session_state:
    st.session_state.aba_preview = None
if "aba_raw" not in st.session_state:
    st.session_state.aba_raw = None
if "mapped_dfs" not in st.session_state:
    st.session_state.mapped_dfs = {}
if "uploaded_file_names" not in st.session_state:
    st.session_state.uploaded_file_names = {}
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "hist_keyword_df" not in st.session_state:
    st.session_state.hist_keyword_df = None
if "hist_asin_df" not in st.session_state:
    st.session_state.hist_asin_df = None
if "hist_trend_df" not in st.session_state:
    st.session_state.hist_trend_df = None
# AI 配置
if "ai_enabled" not in st.session_state:
    st.session_state.ai_enabled = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "deepseek-chat"
if "base_url" not in st.session_state:
    st.session_state.base_url = "https://api.deepseek.com/v1"

# ============ 辅助函数 ============
def show_data_legend():
    st.markdown("""
    <div class="data-legend">
        <b>📖 字段商业解读</b>
        <table>
            <tr><td><span class="field-name">🔴 ABA排名</span></td><td><span class="field-desc">搜索频率排名（数字越小搜索量越大）</span></td><td><span class="field-meaning">≤ 10,000 = 高流量 | ≤ 50,000 = 中流量 | >50,000 = 低流量</span></td></tr>
            <tr><td><span class="field-name">📈 点击份额(%)</span></td><td><span class="field-desc">Top1 ASIN 在该搜索词下获得的点击占比</span></td><td><span class="field-meaning">越高 → 头部垄断越强 → 进入难度越大</span></td></tr>
            <tr><td><span class="field-name">🔄 转化份额(%)</span></td><td><span class="field-desc">Top1 ASIN 在该搜索词下获得的订单占比</span></td><td><span class="field-meaning">越高 → 头部变现能力越强 → 竞争越激烈</span></td></tr>
            <tr><td><span class="field-name">📦 关联ASIN数</span></td><td><span class="field-desc">该关键词下出现的不同 ASIN 数量</span></td><td><span class="field-meaning">越多 → 市场越分散 → 蓝海机会越大</span></td></tr>
        </table>
        <i>💡 平均点击份额评级：&lt;5% 低垄断 ✅ | 5%~10% 中等 ⚠️ | &gt;10% 高垄断 ❌</i>
    </div>
    """, unsafe_allow_html=True)

# ============ 路径选择界面 (Step 0) ============
if st.session_state.step == 0:
    st.markdown('<p class="main-header">🚀 ABA利基分析工具 v4.0</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">选择您的选品路径，AI 将全程引导您完成分析</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="path-card">
            <div class="icon">📊</div>
            <div class="title">路径 A：类目驱动</div>
            <div class="desc">先从类目入手，分析市场机会，再决定做什么产品</div>
            <div style="margin-top:0.8rem;color:#2c3e50;font-size:0.9rem;">
                ✅ 适合：新手、数据驱动型<br>
                ✅ 风险较低，有数据支撑<br>
                ✅ 先看市场，再定产品
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择路径 A →", key="path_a", use_container_width=True):
            st.session_state.path = 'A'
            st.session_state.step = 1
            st.rerun()

    with col2:
        st.markdown("""
        <div class="path-card">
            <div class="icon">🏭</div>
            <div class="title">路径 B：产品驱动</div>
            <div class="desc">先从供应链/产品优势出发，验证市场需求，再确定类目</div>
            <div style="margin-top:0.8rem;color:#2c3e50;font-size:0.9rem;">
                ✅ 适合：工厂型、产品驱动型<br>
                ✅ 发挥供应链优势<br>
                ✅ 先定产品，再找市场
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择路径 B →", key="path_b", use_container_width=True):
            st.session_state.path = 'B'
            st.session_state.step = 1
            st.rerun()

    st.markdown("---")
    st.markdown("💡 **不确定选哪个？** 如果您有供应链资源，选 B；如果您想先看市场机会，选 A。")

# ============ 侧边栏 ============
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/amazon.png", width=50)
    st.markdown("### 📊 分析进度")
    steps_label = ["0. 选择路径", "1. 项目设置", "2. 上传ABA", "3. 补充数据", "4. 预览校验", "5. 执行分析"]
    for i, label in enumerate(steps_label):
        if i == st.session_state.step:
            st.markdown(f"🔵 **{label}**")
        elif i < st.session_state.step:
            st.markdown(f"✅ {label}")
        else:
            st.markdown(f"⬜ {label}")
    
    st.divider()
    
    st.markdown("### 🤖 AI 智能分析")
    st.caption("启用AI可获得更精准的数据清洗、聚类和洞察")
    
    default_api_key = ""
    default_base_url = "https://api.deepseek.com/v1"
    default_model = "deepseek-chat"
    try:
        default_api_key = st.secrets.get("OPENAI_API_KEY", "")
        default_base_url = st.secrets.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        default_model = st.secrets.get("MODEL_NAME", "deepseek-chat")
    except:
        pass
    
    current_key = st.session_state.api_key or default_api_key
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=current_key,
        placeholder="sk-...",
        key="api_key_input"
    )
    current_model = st.session_state.model or default_model
    model_choice = st.selectbox(
        "模型",
        ["deepseek-chat", "deepseek-reasoner", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "qwen-plus"],
        index=0,
        key="model_choice"
    )
    if model_choice != st.session_state.model:
        st.session_state.model = model_choice
    current_url = st.session_state.base_url or default_base_url
    base_url = st.text_input(
        "API Base URL",
        value=current_url,
        placeholder="https://api.deepseek.com/v1",
        key="base_url_input"
    )
    
    if api_key:
        st.session_state.ai_enabled = True
        st.session_state.api_key = api_key
        st.session_state.model = model_choice
        st.session_state.base_url = base_url
        st.success("✅ AI 已启用")
    else:
        st.session_state.ai_enabled = False
        st.info("💡 AI 未启用，使用本地逻辑")
    
    st.divider()
    st.caption(f"📅 v4.0 | {datetime.now().strftime('%Y-%m-%d')}")

# ============ 主界面 ============
if st.session_state.step >= 1:
    st.markdown('<p class="main-header">🚀 ABA利基分析工具 v4.0</p>', unsafe_allow_html=True)
    if st.session_state.path == 'A':
        st.markdown('<p class="sub-header">路径 A：类目驱动 — 先看市场，再定产品</p>', unsafe_allow_html=True)
    elif st.session_state.path == 'B':
        st.markdown('<p class="sub-header">路径 B：产品驱动 — 先有产品，再找市场</p>', unsafe_allow_html=True)

# ============================================================
# STEP 1: 项目设置
# ============================================================
if st.session_state.step == 1:
    st.markdown("### ⚙️ Step 1: 项目设置")
    
    if st.session_state.path == 'A':
        st.markdown("您选择了 **类目驱动** 路径。请填写以下信息：")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input("📌 项目名称 *", value=st.session_state.project_name, placeholder="例：2026-06 耳机市场调研")
                if project_name:
                    st.session_state.project_name = project_name
            with col2:
                category_input = st.text_input("📂 目标类目 *", value=st.session_state.category, placeholder="例：电子产品 > 耳机")
                if category_input:
                    st.session_state.category = category_input
            date_range = st.date_input("📅 数据时间范围", value=st.session_state.date_range if st.session_state.date_range else [])
            if date_range:
                st.session_state.date_range = date_range
        st.info("💡 如果您不确定类目，可以先输入大类，AI 会帮您细化。")
    
    else:
        st.markdown("您选择了 **产品驱动** 路径。请描述您的产品优势：")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input("📌 项目名称 *", value=st.session_state.project_name, placeholder="例：2026-06 环保瑜伽垫")
                if project_name:
                    st.session_state.project_name = project_name
            with col2:
                product_keyword = st.text_input("🏷️ 核心产品词 *", value=st.session_state.product_keyword, placeholder="例：eco friendly yoga mat")
                if product_keyword:
                    st.session_state.product_keyword = product_keyword
                    st.session_state.category = "待AI识别"
            date_range = st.date_input("📅 数据时间范围", value=st.session_state.date_range if st.session_state.date_range else [])
            if date_range:
                st.session_state.date_range = date_range
        st.info("💡 输入核心产品词后，AI 将自动搜索相关关键词并推荐最佳类目。")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if not st.session_state.project_name:
                st.error("请填写项目名称")
            elif st.session_state.path == 'A' and not st.session_state.category:
                st.error("请输入目标类目")
            elif st.session_state.path == 'B' and not st.session_state.product_keyword:
                st.error("请输入核心产品词")
            else:
                st.session_state.step = 2
                st.rerun()

# ============================================================
# STEP 2: 上传ABA数据
# ============================================================
elif st.session_state.step == 2:
    st.markdown("### 📂 Step 2: 上传ABA原始数据")
    
    if st.session_state.path == 'A':
        st.markdown(f"上传 **{st.session_state.category}** 类目的 Top Search Terms 文件")
        st.markdown("""
        <div style="background-color: #eaf2f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <b>📋 建议：</b><br>
        • 导出 Top 100-200 个非品牌词<br>
        • 选择最近完整周的数据<br>
        • 导出格式：CSV（简易视图）
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"上传与 **{st.session_state.product_keyword}** 相关的 ABA 数据")
        st.markdown("""
        <div style="background-color: #eaf2f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <b>📋 建议：</b><br>
        • 导出该核心词及其长尾变体的数据<br>
        • 选择最近4周的数据（观察趋势）<br>
        • 导出格式：CSV（简易视图）
        </div>
        """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "选择 ABA 文件",
        type=["csv", "xlsx", "xls"],
        key="aba_upload"
    )

    if uploaded is not None:
        try:
            file_bytes = uploaded.getvalue()
            file_extension = uploaded.name.split('.')[-1].lower()
            skip_rows = 0
            try:
                content = file_bytes.decode('utf-8', errors='ignore')
                first_line = content.splitlines()[0] if content.splitlines() else ""
                if '报告范围' in first_line or '选择年份' in first_line:
                    skip_rows = 1
            except:
                pass
            
            if file_extension == 'csv':
                try:
                    df = pd.read_csv(uploaded, skiprows=skip_rows, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded.seek(0)
                    df = pd.read_csv(uploaded, skiprows=skip_rows, encoding='gbk')
            else:
                uploaded.seek(0)
                df = pd.read_excel(uploaded, skiprows=skip_rows, engine='openpyxl')
            
            st.success(f"✅ 文件读取成功: {uploaded.name} ({len(df)} 行)")
            
            from core.parser import parse_aba_csv
            from core.clustering import semantic_clustering
            
            with st.spinner("正在解析ABA数据..."):
                use_ai = st.session_state.ai_enabled
                api_key = st.session_state.api_key if use_ai else None
                model = st.session_state.model if use_ai else None
                base_url = st.session_state.base_url if use_ai else None
                
                aba_result = parse_aba_csv(df)
                st.session_state.aba_raw = aba_result
                
                clusters = semantic_clustering(
                    aba_result, 
                    st.session_state.category,
                    use_ai=use_ai,
                    api_key=api_key,
                    model=model,
                    base_url=base_url
                )
            
            st.markdown("---")
            st.markdown("### 📊 Step 2 数据面板：调研候选清单")
            
            show_data_legend()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 总关键词数", aba_result.get("total_keywords", 0))
            with col2:
                st.metric("🔍 非品牌词数", aba_result.get("non_brand_count", 0))
            with col3:
                st.metric("🏷️ 品牌词数", aba_result.get("brand_count", 0))
            with col4:
                avg_click = aba_result.get("avg_click_share", 0)
                st.metric("📈 平均点击份额", f"{avg_click:.2f}%" if avg_click else "N/A")
            
            st.markdown("---")
            st.markdown("#### 🔍 需要调研的关键词（Top 20）")
            top_non_brand = aba_result.get("non_brand_keywords", [])[:20]
            if top_non_brand:
                keyword_data = []
                for i, item in enumerate(top_non_brand, 1):
                    rank = item.get("search_frequency_rank")
                    weight = "🔴 高权重" if rank and rank <= 10000 else ("🟡 中权重" if rank and rank <= 50000 else "🟢 低权重")
                    keyword_data.append({
                        "序号": i,
                        "关键词": item.get("search_term", ""),
                        "ABA排名": rank if rank else "N/A",
                        "权重": weight,
                        "点击份额(%)": item.get("click_share", ""),
                        "转化份额(%)": item.get("conversion_share", "")
                    })
                st.dataframe(pd.DataFrame(keyword_data), use_container_width=True, hide_index=True)
                keyword_list = "\n".join([item.get("search_term", "") for item in top_non_brand[:20]])
                st.download_button(
                    label="📋 复制关键词列表 (Top 20)",
                    data=keyword_list,
                    file_name="keywords_top20.txt",
                    mime="text/plain"
                )
            
            st.markdown("---")
            st.markdown("#### 📦 需要调研的 ASIN（Top 10）")
            top_asins = aba_result.get("top_asins", [])[:10]
            if top_asins:
                asin_data = []
                for i, (asin, count) in enumerate(top_asins, 1):
                    asin_data.append({"序号": i, "ASIN": asin, "出现频次": count})
                st.dataframe(pd.DataFrame(asin_data), use_container_width=True, hide_index=True)
                asin_list = "\n".join([asin for asin, _ in top_asins[:10]])
                st.download_button(
                    label="📋 复制ASIN列表 (Top 10)",
                    data=asin_list,
                    file_name="asins_top10.txt",
                    mime="text/plain"
                )
            
            st.markdown("---")
            st.markdown("#### 📂 初步识别的细分市场")
            if clusters:
                for cluster in clusters[:5]:
                    ai_tag = " 🤖" if cluster.get("ai_generated") else ""
                    with st.expander(f"📁 {cluster['name']}{ai_tag} ({cluster['keyword_count']}个关键词)"):
                        st.write(f"**平均ABA排名**: {cluster['avg_rank']:.0f}")
                        st.write(f"**平均点击份额**: {cluster['avg_click_share']:.2f}%")
                        st.write(f"**示例关键词**: {', '.join(cluster['keywords'][:5])}")
            else:
                st.info("未识别出明显聚类，可继续上传补充数据后重新分析")
            
            st.session_state.aba_preview = {
                "total_keywords": aba_result.get("total_keywords", 0),
                "top_non_brand": top_non_brand,
                "top_asins": top_asins,
                "clusters": clusters
            }
            st.session_state.uploaded_file_names["aba"] = uploaded.name
            
        except Exception as e:
            st.error(f"❌ 读取文件失败: {e}")
            import traceback
            st.code(traceback.format_exc())

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if "aba" not in st.session_state.uploaded_file_names:
                st.error("请上传ABA文件")
            else:
                st.session_state.step = 3
                st.rerun()

# ============================================================
# STEP 3: 上传补充数据
# ============================================================
elif st.session_state.step == 3:
    st.markdown("### 📂 Step 3: 上传补充数据文件")
    st.markdown("上传从卖家精灵、Sif等工具导出的深度数据，AI 将自动清洗和绑定")

    if st.session_state.aba_preview:
        with st.expander("📋 当前需要调研的关键词 (Top 20)", expanded=False):
            top_words = [item.get("search_term", "") for item in st.session_state.aba_preview.get("top_non_brand", [])[:20]]
            st.write(", ".join(top_words))
        with st.expander("📦 当前需要调研的 ASIN (Top 10)", expanded=False):
            top_asins = [asin for asin, _ in st.session_state.aba_preview.get("top_asins", [])[:10]]
            st.write(", ".join(top_asins))

    st.info("""
    **📌 AI 会自动处理：**
    1. 识别多Sheet Excel，提取最新月份数据
    2. 智能绑定 ASIN 与关键词（从标题提取核心词）
    3. 清洗异常值、补全缺失字段
    4. 生成关键词数据表、ASIN数据表、趋势验证表
    """)

    st.markdown("#### 卖家精灵历史数据（推荐）")
    hist_cols = st.columns(2)
    with hist_cols[0]:
        hist_keyword_file = st.file_uploader("关键词历史 (KeywordHistory-*.xlsx)", type=["xlsx", "xls"], key="hist_kw")
        if hist_keyword_file is not None:
            with st.spinner("正在解析关键词历史..."):
                try:
                    df_kw = load_keyword_history(hist_keyword_file)
                    if df_kw is not None and not df_kw.empty:
                        st.session_state.hist_keyword_df = df_kw
                        st.success(f"✅ 解析成功，共 {len(df_kw)} 个关键词")
                        st.dataframe(df_kw.head(3))
                    else:
                        st.error("解析失败，请检查文件格式")
                except Exception as e:
                    st.error(f"解析失败: {e}")
    with hist_cols[1]:
        hist_product_file = st.file_uploader("产品历史 (product-*-sales-*.xlsx)", type=["xlsx", "xls"], key="hist_prod")
        if hist_product_file is not None:
            with st.spinner("正在解析产品历史..."):
                try:
                    df_asin, df_trend, df_price = load_product_history(hist_product_file)
                    if df_asin is not None and not df_asin.empty:
                        st.session_state.hist_asin_df = df_asin
                        st.session_state.hist_trend_df = df_trend
                        st.success(f"✅ 解析成功，共 {len(df_asin)} 个ASIN")
                        st.dataframe(df_asin.head(3))
                    else:
                        st.error("解析失败，请检查文件格式")
                except Exception as e:
                    st.error(f"解析失败: {e}")

    st.markdown("#### 标准数据表（备选，如没有历史数据）")
    st.caption("如果上传了历史数据，以下内容将自动生成，无需手动上传")
    file_configs = {
        "keyword": {"label": "📊 关键词数据表", "help": "卖家精灵导出的关键词深度数据"},
        "asin": {"label": "📦 ASIN数据表", "help": "卖家精灵导出的ASIN详情数据"},
        "review": {"label": "💬 评论数据表", "help": "评论数>200的ASIN需提供"},
        "sif": {"label": "🔗 Sif流量词表", "help": "Sif反查流量词结果"},
        "trend": {"label": "📈 趋势验证表", "help": "销量/价格变化数据"}
    }
    cols = st.columns(2)
    for idx, (key, config) in enumerate(file_configs.items()):
        with cols[idx % 2]:
            uploaded = st.file_uploader(config["label"], type=["csv","xlsx","xls"], key=f"upload_{key}", help=config["help"])
            if uploaded is not None:
                st.session_state.uploaded_file_names[key] = uploaded.name
                try:
                    ext = uploaded.name.split('.')[-1].lower()
                    if ext == 'csv':
                        try:
                            df = pd.read_csv(uploaded, encoding='utf-8')
                        except:
                            uploaded.seek(0)
                            df = pd.read_csv(uploaded, encoding='gbk')
                    else:
                        uploaded.seek(0)
                        df = pd.read_excel(uploaded, engine='openpyxl')
                    st.session_state.mapped_dfs[key] = df
                    st.success(f"✅ 已上传: {uploaded.name} ({len(df)} 行)")
                except Exception as e:
                    st.error(f"❌ 读取失败: {e}")

    has_hist = ('hist_keyword_df' in st.session_state and st.session_state.hist_keyword_df is not None) or \
               ('hist_asin_df' in st.session_state and st.session_state.hist_asin_df is not None)
    has_std = ('keyword' in st.session_state.mapped_dfs and 'asin' in st.session_state.mapped_dfs)
    
    if not has_hist and not has_std:
        st.warning("⚠️ 请上传关键词历史或标准关键词表，以及ASIN历史或标准ASIN表")
    elif has_hist and not has_std:
        st.info("✅ 已上传历史数据，将自动生成关键词和ASIN表")
    elif has_std and not has_hist:
        st.info("✅ 已上传标准数据表，将直接使用")
    else:
        st.info("✅ 同时拥有历史数据和标准数据，将优先使用历史数据（更丰富）")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if not has_hist and not has_std:
                st.error("请至少上传历史数据或标准数据表")
            else:
                st.session_state.step = 4
                st.rerun()

# ============================================================
# STEP 4: 预览校验
# ============================================================
elif st.session_state.step == 4:
    st.markdown("### 🔍 Step 4: 数据预览与校验")
    
    st.markdown("#### 📂 已加载数据文件")
    for key, name in st.session_state.uploaded_file_names.items():
        st.markdown(f"✅ **{key}**: {name}")
    
    if 'hist_keyword_df' in st.session_state and st.session_state.hist_keyword_df is not None:
        st.markdown("#### 📊 关键词数据（来自历史）")
        st.dataframe(st.session_state.hist_keyword_df.head(5))
        st.caption(f"共 {len(st.session_state.hist_keyword_df)} 个关键词")
    
    if 'hist_asin_df' in st.session_state and st.session_state.hist_asin_df is not None:
        st.markdown("#### 📦 ASIN数据（来自历史）")
        st.dataframe(st.session_state.hist_asin_df.head(5))
        st.caption(f"共 {len(st.session_state.hist_asin_df)} 个ASIN")
    
    if 'keyword' in st.session_state.mapped_dfs:
        st.markdown("#### 📊 关键词数据（标准表）")
        st.dataframe(st.session_state.mapped_dfs['keyword'].head(5))
    if 'asin' in st.session_state.mapped_dfs:
        st.markdown("#### 📦 ASIN数据（标准表）")
        st.dataframe(st.session_state.mapped_dfs['asin'].head(5))

    st.divider()
    st.markdown("#### 📋 数据完整性检查")
    issues = []
    if 'hist_keyword_df' in st.session_state and st.session_state.hist_keyword_df is not None:
        df = st.session_state.hist_keyword_df
        if 'keyword' not in df.columns or 'monthly_search_volume' not in df.columns:
            issues.append("关键词历史缺少必需字段（keyword 或 monthly_search_volume）")
    if 'hist_asin_df' in st.session_state and st.session_state.hist_asin_df is not None:
        df = st.session_state.hist_asin_df
        if 'asin' not in df.columns or 'price' not in df.columns:
            issues.append("ASIN历史缺少必需字段（asin 或 price）")
    if issues:
        for issue in issues:
            st.warning(f"⚠️ {issue}")
    else:
        st.success("✅ 数据完整性检查通过")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("🚀 开始分析", type="primary", use_container_width=True):
            with st.spinner("正在执行分析..."):
                try:
                    if 'hist_keyword_df' in st.session_state and st.session_state.hist_keyword_df is not None:
                        keyword_df = st.session_state.hist_keyword_df
                    elif 'keyword' in st.session_state.mapped_dfs:
                        keyword_df = st.session_state.mapped_dfs['keyword']
                    else:
                        keyword_df = None
                    
                    if 'hist_asin_df' in st.session_state and st.session_state.hist_asin_df is not None:
                        asin_df = st.session_state.hist_asin_df
                    elif 'asin' in st.session_state.mapped_dfs:
                        asin_df = st.session_state.mapped_dfs['asin']
                    else:
                        asin_df = None
                    
                    if 'hist_trend_df' in st.session_state and st.session_state.hist_trend_df is not None:
                        trend_df = st.session_state.hist_trend_df
                    elif 'trend' in st.session_state.mapped_dfs:
                        trend_df = st.session_state.mapped_dfs['trend']
                    else:
                        trend_df = None
                    
                    if 'review' in st.session_state.mapped_dfs:
                        review_df = st.session_state.mapped_dfs['review']
                    else:
                        review_df = None
                    
                    aba_result = st.session_state.aba_raw if 'aba_raw' in st.session_state else None
                    
                    use_ai = st.session_state.ai_enabled
                    api_key = st.session_state.api_key if use_ai else None
                    model = st.session_state.model if use_ai else None
                    base_url = st.session_state.base_url if use_ai else None
                    
                    if aba_result:
                        clusters = semantic_clustering(
                            aba_result,
                            st.session_state.category,
                            use_ai=use_ai,
                            api_key=api_key,
                            model=model,
                            base_url=base_url
                        )
                    else:
                        clusters = []
                    
                    total_keywords = aba_result.get("total_keywords", 1) if aba_result else 1
                    for cluster in clusters:
                        cluster["weight_level"] = assign_weight_level(
                            cluster.get("avg_rank", 999999),
                            total_keywords
                        )
                    
                    scored_markets = []
                    for cluster in clusters:
                        scores = calculate_10d_scores(
                            cluster,
                            keyword_df,
                            asin_df,
                            trend_df
                        )
                        scored_markets.append(scores)
                    
                    if trend_df is not None:
                        for market in scored_markets:
                            market["trend_result"] = trend_verification(market, trend_df)
                    
                    comment_insights = []
                    if review_df is not None:
                        comment_insights = analyze_comments(
                            review_df,
                            asin_df,
                            use_ai=use_ai,
                            api_key=api_key,
                            model=model,
                            base_url=base_url
                        )
                    
                    excel_data = generate_excel_report(
                        scored_markets,
                        {"keyword": keyword_df, "asin": asin_df, "trend": trend_df, "review": review_df},
                        comment_insights,
                        st.session_state.project_name,
                        st.session_state.category,
                        st.session_state.date_range,
                        use_ai=use_ai,
                        api_key=api_key,
                        model=model,
                        base_url=base_url
                    )
                    
                    st.session_state.analysis_result = {
                        "market_count": len(scored_markets),
                        "keyword_count": len(aba_result.get("non_brand_keywords", [])) if aba_result else 0,
                        "asin_count": len(asin_df) if asin_df is not None else 0,
                        "top_grade": scored_markets[0].get("grade", "N/A") if scored_markets else "N/A",
                        "top_markets": scored_markets[:5],
                        "excel_data": excel_data
                    }
                    st.session_state.analysis_complete = True
                    st.session_state.step = 5
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 分析失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# ============================================================
# STEP 5: 完成
# ============================================================
elif st.session_state.step == 5:
    st.markdown("### 🎉 Step 5: 分析完成！")
    
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
        st.markdown("#### 📊 分析摘要")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("细分市场数", result.get("market_count", 0))
        with col2:
            st.metric("关键词总数", result.get("keyword_count", 0))
        with col3:
            st.metric("ASIN总数", result.get("asin_count", 0))
        with col4:
            st.metric("最高推荐等级", result.get("top_grade", "N/A"))
        
        st.markdown("#### 🏆 Top 推荐细分市场")
        if "top_markets" in result:
            for i, market in enumerate(result["top_markets"][:3]):
                grade_badge = {
                    "S": "badge-s", "A": "badge-a", "B": "badge-b",
                    "C": "badge-c", "D": "badge-d"
                }.get(market.get("grade", "D"), "badge-d")
                st.markdown(f"""
                <div style="background-color:#f8f9fa; padding:0.8rem 1.2rem; border-radius:8px; margin-bottom:0.5rem;">
                    <span>#{i+1} <b>{market.get('name', 'N/A')}</b></span>
                    <span style="float:right;">综合分: {market.get('final_score', 0):.2f}  <span class="{grade_badge}">{market.get('grade', 'N/A')}</span></span>
                </div>
                """, unsafe_allow_html=True)
                if market.get("ai_summary"):
                    st.info(f"💡 {market['ai_summary']}")
        
        st.divider()
        col1, col2 = st.columns([2,1])
        with col1:
            st.success("✅ 分析完成！点击下方按钮下载报告")
        with col2:
            if "excel_data" in result:
                st.download_button(
                    label="📥 下载 Excel 报告",
                    data=result["excel_data"],
                    file_name=f"{st.session_state.project_name}_利基分析报告.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
        
        if st.button("🔄 重新分析"):
            st.session_state.step = 0
            st.session_state.path = None
            st.session_state.analysis_complete = False
            st.session_state.analysis_result = None
            st.rerun()
    else:
        st.error("分析结果丢失，请重新执行分析")
        if st.button("重新开始"):
            st.session_state.step = 0
            st.rerun()
