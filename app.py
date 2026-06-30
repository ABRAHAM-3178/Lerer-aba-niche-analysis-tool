"""
ABA利基分析工具 v3.0 - 多文件合并版
支持上传2-5个ABA文件，合并分析，输出Top20关键词和Top10 ASIN
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io

from core.parser import parse_aba_csv

# ============ 页面配置 ============
st.set_page_config(
    page_title="ABA利基分析工具 v3.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ 自定义CSS ============
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
    .badge-s { background-color: #27ae60; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-a { background-color: #2e86c1; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-b { background-color: #f39c12; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-c { background-color: #e67e22; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .badge-d { background-color: #e74c3c; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-weight: 700; }
    .stApp { background-color: #f8f9fa; }
    .block-container { padding-top: 2rem; }
    .data-legend {
        background-color: #f0f3f5;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1a5276;
    }
    .data-legend table {
        width: 100%;
        font-size: 0.9rem;
    }
    .data-legend td {
        padding: 0.2rem 0.8rem 0.2rem 0;
    }
    .data-legend .field-name {
        font-weight: 600;
        color: #1a5276;
    }
    .data-legend .field-desc {
        color: #2c3e50;
    }
    .data-legend .field-meaning {
        color: #7f8c8d;
        font-size: 0.85rem;
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
if "merged_keywords" not in st.session_state:
    st.session_state.merged_keywords = None
if "merged_asins" not in st.session_state:
    st.session_state.merged_asins = None
if "aba_preview" not in st.session_state:
    st.session_state.aba_preview = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

# ============ 字段图例 ============
def show_data_legend():
    st.markdown("""
    <div class="data-legend">
        <b>📖 字段商业解读</b>
        <table>
            <tr>
                <td><span class="field-name">🔴 ABA排名</span></td>
                <td><span class="field-desc">搜索频率排名（数字越小搜索量越大）</span></td>
                <td><span class="field-meaning">≤ 10,000 = 高流量 | ≤ 50,000 = 中流量 | >50,000 = 低流量</span></td>
            </tr>
            <tr>
                <td><span class="field-name">📈 点击份额(%)</span></td>
                <td><span class="field-desc">Top1 ASIN 在该搜索词下获得的点击占比</span></td>
                <td><span class="field-meaning">越高 → 头部垄断越强 → 进入难度越大</span></td>
            </tr>
            <tr>
                <td><span class="field-name">🔄 转化份额(%)</span></td>
                <td><span class="field-desc">Top1 ASIN 在该搜索词下获得的订单占比</span></td>
                <td><span class="field-meaning">越高 → 头部变现能力越强 → 竞争越激烈</span></td>
            </tr>
            <tr>
                <td><span class="field-name">📦 关联ASIN数</span></td>
                <td><span class="field-desc">该关键词下出现的不同 ASIN 数量</span></td>
                <td><span class="field-meaning">越多 → 市场越分散 → 蓝海机会越大</span></td>
            </tr>
        </table>
        <br>
        <i>💡 平均点击份额 = 所有关键词Top1点击份额的均值，反映市场整体头部垄断程度，建议参考评级：<br>
        < 5% 低垄断 ✅ | 5%~10% 中等 ⚠️ | >10% 高垄断 ❌</i>
    </div>
    """, unsafe_allow_html=True)

# ============ 二级类目列表 ============
CATEGORIES_LEVEL2 = [
    "请选择类目",
    "Electronics > Headphones",
    "Electronics > Speakers",
    "Electronics > Smartwatches",
    "Electronics > Projectors",
    "Electronics > Cameras",
    "Electronics > Drones",
    "Electronics > Smart Home",
    "Electronics > TVs",
    "Computers > Laptops",
    "Computers > Monitors",
    "Computers > Keyboards",
    "Computers > Mice",
    "Computers > Storage",
    "Computers > Printers",
    "Computers > Networking",
    "Cell Phones > Smartphones",
    "Cell Phones > Cases",
    "Cell Phones > Screen Protectors",
    "Cell Phones > Chargers",
    "Cell Phones > Power Banks",
    "Home & Kitchen > Furniture",
    "Home & Kitchen > Bedding",
    "Home & Kitchen > Lighting",
    "Home & Kitchen > Storage",
    "Home & Kitchen > Cookware",
    "Home & Kitchen > Small Appliances",
    "Clothing > Men",
    "Clothing > Women",
    "Clothing > Kids",
    "Shoes > Men",
    "Shoes > Women",
    "Shoes > Kids",
    "Jewelry > Necklaces",
    "Jewelry > Bracelets",
    "Jewelry > Earrings",
    "Jewelry > Rings",
    "Beauty > Skincare",
    "Beauty > Makeup",
    "Beauty > Fragrance",
    "Beauty > Hair Care",
    "Toys & Games > Educational",
    "Toys & Games > Plush",
    "Toys & Games > Models",
    "Toys & Games > Remote Control",
    "Toys & Games > Outdoor",
    "Sports & Outdoors > Fitness",
    "Sports & Outdoors > Yoga",
    "Sports & Outdoors > Camping",
    "Sports & Outdoors > Cycling",
    "Pet Supplies > Dogs",
    "Pet Supplies > Cats",
    "Pet Supplies > Grooming",
    "Tools > Power Tools",
    "Tools > Hand Tools",
    "Tools > Measuring",
    "Automotive > Accessories",
    "Automotive > Electronics",
    "Baby > Feeding",
    "Baby > Diapering",
    "Baby > Gear",
    "Baby > Nursery",
    "Office > Stationery",
    "Office > Equipment",
    "Grocery > Snacks",
    "Grocery > Condiments",
    "Books > Fiction",
    "Books > Non-Fiction",
    "Books > Children"
]

# ============ 合并函数 ============
def merge_aba_files(uploaded_files):
    """
    解析并合并多个ABA文件
    """
    all_keywords = []
    all_asins = []
    total_files = len(uploaded_files)
    
    for file in uploaded_files:
        try:
            file_bytes = file.getvalue()
            file_extension = file.name.split('.')[-1].lower()
            
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
                    df = pd.read_csv(io.BytesIO(file_bytes), skiprows=skip_rows, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(file_bytes), skiprows=skip_rows, encoding='gbk')
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_bytes), skiprows=skip_rows, engine='openpyxl')
            else:
                continue
            
            result = parse_aba_csv(df)
            
            if "error" in result:
                st.warning(f"文件 {file.name} 解析失败: {result['error']}")
                continue
            
            for kw in result.get("non_brand_keywords", []):
                kw['source_file'] = file.name
                all_keywords.append(kw)
            
            for asin, count in result.get("top_asins", []):
                all_asins.append((asin, count))
                
        except Exception as e:
            st.warning(f"处理文件 {file.name} 时出错: {e}")
    
    if not all_keywords:
        return None, None, {}
    
    # 合并关键词
    keyword_map = {}
    for kw in all_keywords:
        term = kw.get("search_term")
        if not term:
            continue
        if term not in keyword_map:
            keyword_map[term] = {
                "search_term": term,
                "search_frequency_rank": kw.get("search_frequency_rank"),
                "click_share": kw.get("click_share"),
                "conversion_share": kw.get("conversion_share"),
                "asin_count": 0,
                "source_files": []
            }
        else:
            if kw.get("search_frequency_rank") is not None:
                if (keyword_map[term]["search_frequency_rank"] is None or 
                    kw["search_frequency_rank"] < keyword_map[term]["search_frequency_rank"]):
                    keyword_map[term]["search_frequency_rank"] = kw["search_frequency_rank"]
            if kw.get("click_share") is not None:
                keyword_map[term]["click_share"] = ((keyword_map[term].get("click_share") or 0) + kw["click_share"]) / 2
            if kw.get("conversion_share") is not None:
                keyword_map[term]["conversion_share"] = ((keyword_map[term].get("conversion_share") or 0) + kw["conversion_share"]) / 2
            if kw.get("source_file"):
                keyword_map[term]["source_files"].append(kw["source_file"])
    
    merged_keywords = list(keyword_map.values())
    merged_keywords.sort(key=lambda x: x["search_frequency_rank"] if x["search_frequency_rank"] is not None else 999999)
    
    # 统计关联ASIN数
    for kw in merged_keywords:
        asin_set = set()
        for item in all_keywords:
            if item.get("search_term") == kw["search_term"] and item.get("clickedAsin"):
                asin_set.add(item["clickedAsin"])
        kw["asin_count"] = len(asin_set)
    
    # 合并ASIN
    asin_counter = {}
    for asin, count in all_asins:
        asin_counter[asin] = asin_counter.get(asin, 0) + count
    sorted_asins = sorted(asin_counter.items(), key=lambda x: x[1], reverse=True)
    
    # 计算平均点击份额
    click_shares = [kw.get("click_share") for kw in merged_keywords if kw.get("click_share") is not None]
    avg_click = sum(click_shares) / len(click_shares) if click_shares else 0
    
    stats = {
        "total_keywords": len(merged_keywords),
        "total_asins": len(sorted_asins),
        "avg_click_share": avg_click,
        "avg_conversion_share": sum([kw.get("conversion_share") for kw in merged_keywords if kw.get("conversion_share") is not None]) / len(merged_keywords) if merged_keywords else 0
    }
    
    return merged_keywords, sorted_asins, stats

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
    st.caption(f"📅 版本: v3.0 | {datetime.now().strftime('%Y-%m-%d')}")

# ============ 主界面 ============
st.markdown('<p class="main-header">🚀 ABA利基分析工具 v3.0</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">多文件合并 · 智能选词 · 6维度报告</p>', unsafe_allow_html=True)

# ============================================================
# STEP 1: 项目设置
# ============================================================
if st.session_state.step == 1:
    st.markdown("### ⚙️ Step 1: 项目设置")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input(
                "📌 项目名称 *",
                value=st.session_state.project_name,
                placeholder="例：2026-06 Standing Desk Market"
            )
            if project_name:
                st.session_state.project_name = project_name
        
        with col2:
            category = st.selectbox(
                "📂 目标类目 *",
                options=CATEGORIES_LEVEL2,
                index=0,
                key="category_select"
            )
            if category != "请选择类目":
                st.session_state.category = category
            else:
                st.session_state.category = ""
        
        date_range = st.date_input(
            "📅 数据时间范围",
            value=st.session_state.date_range if st.session_state.date_range else [],
            help="仅用于报告标注"
        )
        if date_range:
            st.session_state.date_range = date_range
    
    st.info("📌 项目名称和目标类目为必填项")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if not st.session_state.project_name:
                st.error("请填写项目名称")
            elif not st.session_state.category:
                st.error("请选择目标类目")
            else:
                st.session_state.step = 2
                st.rerun()

# ============================================================
# STEP 2: 上传ABA数据（多文件合并）
# ============================================================
elif st.session_state.step == 2:
    st.markdown("### 📂 Step 2: 上传ABA数据（可上传2~5个文件）")
    st.markdown("上传亚马逊品牌分析导出的 Top Search Terms 文件，系统将自动合并分析")

    st.markdown("""
    <div style="background-color: #eaf2f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
    <b>📋 支持格式：</b> .csv, .xlsx, .xls<br>
    • 自动识别中文/英文列名<br>
    • 自动跳过元数据行<br>
    • 多个文件合并去重，保留最小ABA排名<br>
    • 建议上传不同产品线或不同时间段的文件以获取更全面视角
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "选择 ABA 文件（可多选）",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        key="aba_multi_upload"
    )

    if uploaded_files:
        if len(uploaded_files) < 2:
            st.warning("建议上传至少2个文件以获得更全面的分析，当前仅1个文件。")
        elif len(uploaded_files) > 5:
            st.warning("最多支持5个文件，已选择{}个，请减少文件数。".format(len(uploaded_files)))
            uploaded_files = uploaded_files[:5]
            st.info("已自动截取前5个文件。")
        
        st.session_state.uploaded_files = uploaded_files
        st.success(f"✅ 已选择 {len(uploaded_files)} 个文件")
        
        for f in uploaded_files:
            st.write(f"- {f.name} ({f.size//1024} KB)")
        
        with st.spinner("正在解析并合并数据..."):
            merged_keywords, merged_asins, stats = merge_aba_files(uploaded_files)
        
        if merged_keywords is not None and len(merged_keywords) > 0:
            st.session_state.merged_keywords = merged_keywords
            st.session_state.merged_asins = merged_asins
            st.session_state.aba_preview = stats
            
            show_data_legend()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 总关键词数（合并去重）", len(merged_keywords))
            with col2:
                st.metric("🔍 Top 20 关键词", min(20, len(merged_keywords)))
            with col3:
                st.metric("📦 Top 10 ASIN", min(10, len(merged_asins)))
            with col4:
                avg_click = stats.get("avg_click_share", 0)
                st.metric("📈 平均点击份额", f"{avg_click:.2f}%" if avg_click else "N/A")
            
            # Top 20 关键词
            st.markdown("---")
            st.markdown("#### 🔍 Top 20 关键词（按ABA排名排序）")
            st.caption("💡 排名越靠前（数字越小）搜索量越大，建议优先调研高权重关键词")
            
            keyword_data = []
            for i, item in enumerate(merged_keywords[:20], 1):
                rank = item.get("search_frequency_rank")
                if rank and rank <= 10000:
                    weight_tag = "🔴 高权重"
                elif rank and rank <= 50000:
                    weight_tag = "🟡 中权重"
                else:
                    weight_tag = "🟢 低权重"
                
                keyword_data.append({
                    "序号": i,
                    "关键词": item.get("search_term", ""),
                    "ABA排名": rank if rank else "N/A",
                    "权重": weight_tag,
                    "点击份额(%)": item.get("click_share", ""),
                    "转化份额(%)": item.get("conversion_share", ""),
                    "关联ASIN数": item.get("asin_count", 0)
                })
            
            st.dataframe(pd.DataFrame(keyword_data), use_container_width=True, hide_index=True)
            
            keyword_list = "\n".join([item.get("search_term", "") for item in merged_keywords[:20]])
            st.download_button(
                label="📋 复制关键词列表 (Top 20)",
                data=keyword_list,
                file_name="keywords_top20.txt",
                mime="text/plain"
            )
            
            # Top 10 ASIN
            st.markdown("---")
            st.markdown("#### 📦 Top 10 ASIN（按出现频次排序）")
            
            asin_data = []
            for i, (asin, count) in enumerate(merged_asins[:10], 1):
                asin_data.append({
                    "序号": i,
                    "ASIN": asin,
                    "出现频次": count
                })
            st.dataframe(pd.DataFrame(asin_data), use_container_width=True, hide_index=True)
            
            asin_list = "\n".join([asin for asin, _ in merged_asins[:10]])
            st.download_button(
                label="📋 复制ASIN列表 (Top 10)",
                data=asin_list,
                file_name="asins_top10.txt",
                mime="text/plain"
            )
            
            avg_click = stats.get("avg_click_share", 0)
            if avg_click:
                if avg_click < 5:
                    rating = "低垄断 ✅"
                    color = "green"
                elif avg_click < 10:
                    rating = "中等 ⚠️"
                    color = "orange"
                else:
                    rating = "高垄断 ❌"
                    color = "red"
                st.info(f"📊 平均点击份额 **{avg_click:.2f}%** → 评级：<span style='color:{color};font-weight:bold;'>{rating}</span>", unsafe_allow_html=True)
        else:
            st.error("合并结果为空，请检查文件格式是否正确。")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if not st.session_state.uploaded_files:
                st.error("请至少上传一个ABA文件")
            elif st.session_state.merged_keywords is None or len(st.session_state.merged_keywords) == 0:
                st.error("数据解析失败，请检查文件格式")
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
        "keyword": {"label": "📊 关键词数据表 *", "help": "卖家精灵导出的关键词深度数据", "required": True},
        "asin": {"label": "📦 ASIN数据表 *", "help": "卖家精灵导出的ASIN详情数据", "required": True},
        "review": {"label": "💬 评论数据表", "help": "评论数>200的ASIN需提供", "required": False},
        "sif": {"label": "🔗 Sif流量词表", "help": "Sif反查流量词结果", "required": False},
        "trend": {"label": "📈 趋势验证表", "help": "销量/价格变化数据", "required": False}
    }
    
    cols = st.columns(2)
    for idx, (key, config) in enumerate(file_configs.items()):
        with cols[idx % 2]:
            uploaded = st.file_uploader(
                config["label"],
                type=["csv", "xlsx", "xls"],
                key=f"upload_{key}",
                help=config["help"]
            )
            if uploaded is not None:
                st.session_state.uploaded_files[key] = uploaded
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
                    st.success(f"✅ 已上传: {uploaded.name} ({len(df)} 行)")
                except Exception as e:
                    st.error(f"❌ 读取失败: {e}")
    
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
# STEP 4: 预览校验
# ============================================================
elif st.session_state.step == 4:
    st.markdown("### 🔍 Step 4: 数据预览与校验")
    
    for key, file in st.session_state.uploaded_files.items():
        if key in ["aba", "keyword", "asin", "review", "sif", "trend"]:
            try:
                ext = file.name.split('.')[-1].lower()
                if ext == 'csv':
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file, engine='openpyxl')
                st.markdown(f"✅ **{key}**: {file.name} ({len(df)} 行, {len(df.columns)} 列)")
            except:
                st.markdown(f"❌ **{key}**: 读取失败")
    
    st.divider()
    st.markdown("#### 📋 数据完整性检查")
    
    validation_results = []
    for key in ["keyword", "asin"]:
        if key in st.session_state.uploaded_files:
            file = st.session_state.uploaded_files[key]
            try:
                ext = file.name.split('.')[-1].lower()
                if ext == 'csv':
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file, engine='openpyxl')
                validation_results.append(f"✅ {key}: {len(df)}行数据")
            except:
                validation_results.append(f"❌ {key}: 读取失败")
    
    for msg in validation_results:
        st.write(msg)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("🚀 开始分析", type="primary", use_container_width=True):
            with st.spinner("正在分析中..."):
                try:
                    # 读取所有上传的文件
                    data = {}
                    for key, file in st.session_state.uploaded_files.items():
                        if file is not None:
                            ext = file.name.split('.')[-1].lower()
                            if ext == 'csv':
                                try:
                                    data[key] = pd.read_csv(file, encoding='utf-8')
                                except:
                                    file.seek(0)
                                    data[key] = pd.read_csv(file, encoding='gbk')
                            else:
                                file.seek(0)
                                data[key] = pd.read_excel(file, engine='openpyxl')
                    
                    # 解析ABA（如果有多文件，用合并后的数据）
                    if st.session_state.merged_keywords is not None:
                        # 使用合并后的数据（已经包含top_asins等）
                        aba_result = {
                            "non_brand_keywords": st.session_state.merged_keywords,
                            "top_asins": st.session_state.merged_asins,
                            "total_keywords": len(st.session_state.merged_keywords),
                            "avg_click_share": st.session_state.aba_preview.get("avg_click_share", 0)
                        }
                    else:
                        aba_result = parse_aba_csv(data.get("aba"))
                    
                    # 执行完整的10维评分等（这里简化，只做演示）
                    # 实际项目应导入其他模块
                    st.success("分析完成（演示）")
                    
                except Exception as e:
                    st.error(f"❌ 分析失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())
