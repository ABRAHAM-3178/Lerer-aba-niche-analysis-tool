"""
ABA利基分析工具 v2.0
全手动、零API依赖的亚马逊ABA关键词利基分析工具
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from datetime import datetime

from core.parser import parse_aba_csv
from core.clustering import semantic_clustering
from core.scoring import calculate_10d_scores
from core.trend import trend_verification
from core.comment_analysis import analyze_comments
from core.report_generator import generate_excel_report

# 页面配置
st.set_page_config(
    page_title="ABA利基分析工具 v2.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a5276;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-indicator {
        display: flex;
        justify-content: space-between;
        padding: 1rem 2rem;
        background-color: #f0f3f5;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .step-active {
        background-color: #1a5276;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    .step-inactive {
        background-color: #d5d8dc;
        color: #5d6d7e;
        padding: 0.3rem 1rem;
        border-radius: 20px;
    }
    .file-upload-box {
        border: 2px dashed #85c1e9;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f7f9fa;
    }
    .file-upload-box-valid {
        border-color: #28b463;
        background-color: #eafaf1;
    }
    .score-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
    }
    .badge-s {
        background-color: #27ae60;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-weight: 700;
    }
    .badge-a {
        background-color: #2e86c1;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-weight: 700;
    }
    .badge-b {
        background-color: #f39c12;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-weight: 700;
    }
    .badge-c {
        background-color: #e67e22;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-weight: 700;
    }
    .badge-d {
        background-color: #e74c3c;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ============ 初始化 Session State ============
if "step" not in st.session_state:
    st.session_state.step = 1
if "project_name" not in st.session_state:
    st.session_state.project_name = ""
if "category" not in st.session_state:
    st.session_state.category = ""
if "date_range" not in st.session_state:
    st.session_state.date_range = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

# ============ 侧边栏 ============
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/amazon.png", width=50)
    st.markdown("### 📊 分析进度")
    steps = ["1. 项目设置", "2. 上传ABA", "3. 补充数据", "4. 预览校验", "5. 执行分析"]
    for i, step_name in enumerate(steps, 1):
        if i == st.session_state.step:
            st.markdown(f"🔵 **{step_name}**")
        elif i < st.session_state.step:
            st.markdown(f"✅ {step_name}")
        else:
            st.markdown(f"⬜ {step_name}")
    
    st.divider()
    st.caption("💡 提示：所有数据仅在本地处理，不会上传到任何服务器")
    st.caption(f"📅 版本: v2.0 | {datetime.now().strftime('%Y-%m-%d')}")

# ============ 主界面 ============
st.markdown('<p class="main-header">🚀 ABA利基分析工具 v2.0</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">全手动·零API依赖·6维度选品报告</p>', unsafe_allow_html=True)

# ============================================================
# STEP 1: 项目设置
# ============================================================
if st.session_state.step == 1:
    st.markdown("### ⚙️ Step 1: 项目设置")
    st.markdown("请填写本次分析的基本信息")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input(
                "📌 项目名称 *",
                value=st.session_state.project_name,
                placeholder="例：2026-06 无线耳机市场调研",
                help="建议包含日期和品类，便于后续查找"
            )
            if project_name:
                st.session_state.project_name = project_name
        
        with col2:
            category = st.text_input(
                "📂 目标类目 *",
                value=st.session_state.category,
                placeholder="例：电子产品 - 耳机",
                help="填写你正在调研的类目"
            )
            if category:
                st.session_state.category = category
        
        date_range = st.date_input(
            "📅 数据时间范围",
            value=st.session_state.date_range if st.session_state.date_range else [],
            help="仅用于报告标注，不影响分析结果"
        )
        if date_range:
            st.session_state.date_range = date_range
    
    st.info("📌 项目名称和目标类目为必填项，将显示在报告封面")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if not st.session_state.project_name:
                st.error("请填写项目名称")
            elif not st.session_state.category:
                st.error("请填写目标类目")
            else:
                st.session_state.step = 2
                st.rerun()

# ============================================================
# STEP 2: 上传ABA数据
# ============================================================
elif st.session_state.step == 2:
    st.markdown("### 📂 Step 2: 上传ABA原始数据")
    st.markdown("上传亚马逊品牌分析导出的 **Top Search Terms** CSV 文件")
    
    st.markdown("""
    <div style="background-color: #eaf2f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
    <b>📋 文件要求：</b><br>
    • 必须包含列：Search Term, Search Frequency Rank, Click Share, Conversion Share<br>
    • 支持 UTF-8 编码的 CSV 格式<br>
    • 建议导出最近一周的数据
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "选择 ABA CSV 文件",
        type=["csv"],
        key="aba_upload",
        help="从亚马逊品牌分析导出的 Top Search Terms 报告"
    )
    
    if uploaded is not None:
        st.session_state.uploaded_files["aba"] = uploaded
        try:
            df = pd.read_csv(uploaded)
            st.success(f"✅ 已上传: {uploaded.name} ({len(df)} 行)")
            with st.expander("📊 数据预览"):
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"列名: {', '.join(df.columns.tolist())}")
        except Exception as e:
            st.error(f"❌ 读取文件失败: {e}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if "aba" not in st.session_state.uploaded_files:
                st.error("请上传ABA CSV文件")
            else:
                st.session_state.step = 3
                st.rerun()

# ============================================================
# STEP 3: 上传补充数据
# ============================================================
elif st.session_state.step == 3:
    st.markdown("### 📂 Step 3: 上传补充数据文件")
    st.markdown("上传从卖家精灵、Sif等工具导出的补充数据")
    
    st.info("""
    **📌 文件说明：**
    - ✅ **必填**：关键词数据表、ASIN数据表
    - ⚠️ **条件必填**：评论数据表（当ASIN评论数>200时必须提供）
    - ⬜ **可选**：Sif流量词表、趋势验证表
    """)
    
    file_configs = {
        "keyword": {
            "label": "📊 关键词数据表 *",
            "help": "卖家精灵导出的关键词深度数据",
            "required": True
        },
        "asin": {
            "label": "📦 ASIN数据表 *",
            "help": "卖家精灵导出的ASIN详情数据",
            "required": True
        },
        "review": {
            "label": "💬 评论数据表",
            "help": "评论数>200的ASIN需提供",
            "required": False
        },
        "sif": {
            "label": "🔗 Sif流量词表",
            "help": "Sif反查流量词结果",
            "required": False
        },
        "trend": {
            "label": "📈 趋势验证表",
            "help": "销量/价格变化数据",
            "required": False
        }
    }
    
    cols = st.columns(2)
    for idx, (key, config) in enumerate(file_configs.items()):
        with cols[idx % 2]:
            uploaded = st.file_uploader(
                config["label"],
                type=["csv"],
                key=f"upload_{key}",
                help=config["help"]
            )
            if uploaded is not None:
                st.session_state.uploaded_files[key] = uploaded
                try:
                    df = pd.read_csv(uploaded)
                    st.success(f"✅ 已上传: {uploaded.name} ({len(df)} 行)")
                except:
                    st.error("❌ 文件格式错误")
            else:
                if key in st.session_state.uploaded_files:
                    del st.session_state.uploaded_files[key]
    
    missing = []
    if "keyword" not in st.session_state.uploaded_files:
        missing.append("关键词数据表")
    if "asin" not in st.session_state.uploaded_files:
        missing.append("ASIN数据表")
    
    if missing:
        st.warning(f"⚠️ 请上传: {', '.join(missing)}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if "keyword" not in st.session_state.uploaded_files:
                st.error("请上传关键词数据表")
            elif "asin" not in st.session_state.uploaded_files:
                st.error("请上传ASIN数据表")
            else:
                st.session_state.step = 4
                st.rerun()

# ============================================================
# STEP 4: 数据预览与校验
# ============================================================
elif st.session_state.step == 4:
    st.markdown("### 🔍 Step 4: 数据预览与校验")
    st.markdown("检查已上传文件的数据完整性")
    
    for key, file in st.session_state.uploaded_files.items():
        try:
            df = pd.read_csv(file)
            cols = df.columns.tolist()
            status = "✅" if len(df) > 0 else "⚠️"
            st.markdown(f"{status} **{key}**: {file.name} ({len(df)} 行, {len(cols)} 列)")
        except:
            st.markdown(f"❌ **{key}**: 读取失败")
    
    st.divider()
    st.markdown("#### 📋 数据完整性检查")
    
    validation_results = []
    
    if "aba" in st.session_state.uploaded_files:
        df = pd.read_csv(st.session_state.uploaded_files["aba"])
        required_aba = ["Search Term", "Search Frequency Rank"]
        missing_aba = [c for c in required_aba if c not in df.columns]
        if missing_aba:
            validation_results.append(("❌ ABA文件", f"缺少列: {missing_aba}"))
        else:
            validation_results.append(("✅ ABA文件", f"结构完整，{len(df)}行数据"))
    
    if "keyword" in st.session_state.uploaded_files:
        df = pd.read_csv(st.session_state.uploaded_files["keyword"])
        required_kw = ["keyword", "monthly_search_volume"]
        missing_kw = [c for c in required_kw if c not in df.columns]
        if missing_kw:
            validation_results.append(("❌ 关键词表", f"缺少列: {missing_kw}"))
        else:
            validation_results.append(("✅ 关键词表", f"结构完整，{len(df)}行数据"))
    
    if "asin" in st.session_state.uploaded_files:
        df = pd.read_csv(st.session_state.uploaded_files["asin"])
        required_asin = ["asin", "keyword"]
        missing_asin = [c for c in required_asin if c not in df.columns]
        if missing_asin:
            validation_results.append(("❌ ASIN表", f"缺少列: {missing_asin}"))
        else:
            validation_results.append(("✅ ASIN表", f"结构完整，{len(df)}行数据"))
    
    for status, msg in validation_results:
        st.write(f"{status} {msg}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("🚀 开始分析", type="primary", use_container_width=True):
            with st.spinner("正在分析中，请稍候..."):
                try:
                    result = run_full_analysis(
                        st.session_state.uploaded_files,
                        st.session_state.project_name,
                        st.session_state.category,
                        st.session_state.date_range
                    )
                    st.session_state.analysis_result = result
                    st.session_state.analysis_complete = True
                    st.session_state.step = 5
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 分析失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# ============================================================
# STEP 5: 执行分析 & 下载报告
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
            top_grade = result.get("top_grade", "N/A")
            st.metric("最高推荐等级", top_grade)
        
        st.markdown("#### 🏆 Top 推荐细分市场")
        if "top_markets" in result:
            for i, market in enumerate(result["top_markets"][:3]):
                grade_badge = {
                    "S": "badge-s", "A": "badge-a", "B": "badge-b", 
                    "C": "badge-c", "D": "badge-d"
                }.get(market.get("grade", "D"), "badge-d")
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; background-color:#f8f9fa; padding:0.8rem 1.2rem; border-radius:8px; margin-bottom:0.5rem;">
                    <span>#{i+1} <b>{market.get('name', 'N/A')}</b></span>
                    <span>综合分: {market.get('score', 0):.2f}</span>
                    <span class="{grade_badge}">{market.get('grade', 'N/A')}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
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
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 重新分析"):
                st.session_state.step = 1
                st.session_state.analysis_complete = False
                st.session_state.analysis_result = None
                st.rerun()
        with col2:
            if st.button("🏠 回到首页"):
                st.session_state.step = 1
                st.session_state.analysis_complete = False
                st.session_state.analysis_result = None
                st.rerun()
        
    else:
        st.error("分析结果丢失，请重新执行分析")
        if st.button("重新开始"):
            st.session_state.step = 1
            st.rerun()


# ============================================================
# 核心分析函数
# ============================================================
def run_full_analysis(uploaded_files, project_name, category, date_range):
    """执行完整的分析流程"""
    
    data = {}
    for key, file in uploaded_files.items():
        if file is not None:
            data[key] = pd.read_csv(file)
    
    aba_result = parse_aba_csv(data.get("aba"))
    clusters = semantic_clustering(aba_result, category)
    
    from core.scoring import assign_weight_level
    total_keywords = aba_result.get("total_keywords", 1)
    for cluster in clusters:
        cluster["weight_level"] = assign_weight_level(cluster.get("avg_rank", 99999), total_keywords)
    
    scored_markets = []
    for cluster in clusters:
        scores = calculate_10d_scores(
            cluster, 
            data.get("keyword"), 
            data.get("asin"),
            data.get("trend")
        )
        scored_markets.append(scores)
    
    if "trend" in data:
        for market in scored_markets:
            market["trend_result"] = trend_verification(market, data.get("trend"))
    
    comment_insights = []
    if "review" in data:
        comment_insights = analyze_comments(data.get("review"), data.get("asin"))
    
    excel_data = generate_excel_report(
        scored_markets,
        data,
        comment_insights,
        project_name,
        category,
        date_range
    )
    
    return {
        "market_count": len(scored_markets),
        "keyword_count": len(aba_result.get("non_brand_keywords", [])),
        "asin_count": len(data.get("asin", [])),
        "top_grade": scored_markets[0].get("grade", "N/A") if scored_markets else "N/A",
        "top_markets": scored_markets[:5],
        "excel_data": excel_data
    }


if __name__ == "__main__":
    pass
