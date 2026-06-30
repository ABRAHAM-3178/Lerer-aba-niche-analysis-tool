"""
ABA利基分析工具 v3.0 - AI增强版
全手动·可选AI·6维度选品报告
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
if "ai_enabled" not in st.session_state:
    st.session_state.ai_enabled = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "deepseek-chat"
if "base_url" not in st.session_state:
    st.session_state.base_url = "https://api.deepseek.com/v1"

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
    
    # ===== AI 配置模块（默认 DeepSeek，支持 st.secrets） =====
    st.markdown("### 🤖 AI 智能分析")
    st.caption("启用AI可获得更精准的语义聚类和评论洞察")
    
    # 从 st.secrets 读取默认配置
    default_api_key = ""
    default_base_url = "https://api.deepseek.com/v1"
    default_model = "deepseek-chat"
    
    try:
        default_api_key = st.secrets.get("OPENAI_API_KEY", "")
        default_base_url = st.secrets.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        default_model = st.secrets.get("MODEL_NAME", "deepseek-chat")
    except Exception:
        pass
    
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=default_api_key,
        placeholder="输入 DeepSeek API Key（sk-...）",
        help="获取：platform.deepseek.com",
        key="api_key_input"
    )
    
    model_choice = st.selectbox(
        "选择模型",
        ["deepseek-chat", "deepseek-reasoner", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "qwen-plus"],
        index=0,
        key="model_choice"
    )
    
    base_url = st.text_input(
        "API Base URL",
        value=default_base_url,
        placeholder="https://api.deepseek.com/v1",
        help="DeepSeek 使用 https://api.deepseek.com/v1",
        key="base_url_input"
    )
    
    if api_key:
        st.session_state.ai_enabled = True
        st.session_state.api_key = api_key
        st.session_state.model = model_choice
        st.session_state.base_url = base_url
        st.success("✅ DeepSeek AI 已启用")
    else:
        st.session_state.ai_enabled = False
        st.info("💡 未启用AI，使用本地词库")
    
    st.divider()
    st.caption(f"📅 版本: v3.0 | {datetime.now().strftime('%Y-%m-%d')}")
    st.caption("💡 所有数据仅在本地处理，API调用仅用于分析")

# ============ 主界面 ============
st.markdown('<p class="main-header">🚀 ABA利基分析工具 v3.0</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">全手动 · 可选AI · 6维度选品报告</p>', unsafe_allow_html=True)

# ============================================================
# STEP 1: 项目设置
# ============================================================
if st.session_state.step == 1:
    st.markdown("### ⚙️ Step 1: 项目设置")
    
    # 全英文四级类目列表
    CATEGORIES_EN = [
        "请选择类目",
        "Electronics > Headphones > Over-Ear > Noise Cancelling",
        "Electronics > Headphones > Over-Ear > Wireless",
        "Electronics > Headphones > In-Ear > True Wireless",
        "Electronics > Headphones > In-Ear > Noise Cancelling",
        "Electronics > Headphones > Sports > Wireless Sports",
        "Electronics > Speakers > Bluetooth > Portable Bluetooth",
        "Electronics > Speakers > Bluetooth > Waterproof Bluetooth",
        "Electronics > Smartwatches > Sports > GPS Sports Watch",
        "Electronics > Smartwatches > Sports > Heart Rate Monitor",
        "Electronics > Projectors > Home > 4K Home Projector",
        "Electronics > Projectors > Portable > Mini Portable Projector",
        "Electronics > Cameras > Digital > DSLR Cameras",
        "Electronics > Cameras > Digital > Mirrorless Cameras",
        "Electronics > Drones > Consumer > Professional Drones",
        "Electronics > Smart Home > Security > Smart Cameras",
        "Electronics > TVs > 4K > OLED TVs",
        "Electronics > TVs > 4K > QLED TVs",
        "Computers > Laptops > Gaming > Gaming Laptops",
        "Computers > Laptops > Business > Business Laptops",
        "Computers > Laptops > Chromebooks > Google Chromebooks",
        "Computers > Monitors > Gaming > High Refresh Rate Monitors",
        "Computers > Monitors > Office > 4K Office Monitors",
        "Computers > Keyboards > Mechanical > Wired Mechanical",
        "Computers > Keyboards > Mechanical > Wireless Mechanical",
        "Computers > Mice > Gaming > Wired Gaming Mice",
        "Computers > Mice > Gaming > Wireless Gaming Mice",
        "Computers > Storage > SSD > External SSD",
        "Computers > Storage > SSD > Internal SSD",
        "Computers > Printers > Laser > Black & White Laser",
        "Computers > Printers > Inkjet > Color Inkjet",
        "Computers > Networking > Routers > WiFi 6 Routers",
        "Cell Phones > Smartphones > Android > Samsung Galaxy",
        "Cell Phones > Smartphones > Android > Google Pixel",
        "Cell Phones > Smartphones > iPhone > iPhone Series",
        "Cell Phones > Cases > iPhone > Shockproof Cases",
        "Cell Phones > Cases > iPhone > Magnetic Cases",
        "Cell Phones > Screen Protectors > Tempered Glass > iPhone Tempered Glass",
        "Cell Phones > Chargers > Wall > Fast Chargers",
        "Cell Phones > Chargers > Wall > Wireless Chargers",
        "Cell Phones > Power Banks > High Capacity > Large Capacity Power Banks",
        "Cell Phones > Power Banks > Portable > Compact Power Banks",
        "Home & Kitchen > Furniture > Living Room > Sofas",
        "Home & Kitchen > Furniture > Living Room > Coffee Tables",
        "Home & Kitchen > Furniture > Bedroom > Bed Frames",
        "Home & Kitchen > Furniture > Study > Desks",
        "Home & Kitchen > Furniture > Dining > Dining Tables",
        "Home & Kitchen > Furniture > Outdoor > Outdoor Tables & Chairs",
        "Home & Kitchen > Bedding > Sheet Sets > Cotton Sheet Sets",
        "Home & Kitchen > Bedding > Pillows > Memory Foam Pillows",
        "Home & Kitchen > Lighting > Floor Lamps > Modern Floor Lamps",
        "Home & Kitchen > Lighting > Table Lamps > Eye-Care Desk Lamps",
        "Home & Kitchen > Storage > Shelves > Shelving Units",
        "Home & Kitchen > Cookware > Pans > Non-Stick Pans",
        "Home & Kitchen > Cookware > Knives > Chef Knife Sets",
        "Home & Kitchen > Small Appliances > Coffee > Drip Coffee Makers",
        "Home & Kitchen > Small Appliances > Coffee > Espresso Machines",
        "Home & Kitchen > Small Appliances > Air Fryers > Air Fryers",
        "Home & Kitchen > Small Appliances > Ovens > Countertop Ovens",
        "Clothing > Men > Tops > T-Shirts",
        "Clothing > Men > Tops > Polo Shirts",
        "Clothing > Men > Outerwear > Jackets",
        "Clothing > Men > Pants > Jeans",
        "Clothing > Men > Pants > Shorts",
        "Clothing > Women > Dresses > Casual Dresses",
        "Clothing > Women > Tops > Blouses",
        "Clothing > Women > Outerwear > Trench Coats",
        "Clothing > Women > Pants > Jeans",
        "Clothing > Women > Skirts > Midi Skirts",
        "Clothing > Kids > Toddler > Toddler T-Shirts",
        "Shoes > Men > Athletic > Running Shoes",
        "Shoes > Men > Athletic > Basketball Shoes",
        "Shoes > Men > Formal > Leather Shoes",
        "Shoes > Men > Casual > Sneakers",
        "Shoes > Women > Athletic > Running Shoes",
        "Shoes > Women > Heels > Stiletto Heels",
        "Shoes > Women > Flats > Ballet Flats",
        "Shoes > Women > Boots > Ankle Boots",
        "Shoes > Women > Sandals > Flat Sandals",
        "Jewelry > Necklaces > Gold > Gold Necklaces",
        "Jewelry > Necklaces > Silver > Silver Necklaces",
        "Jewelry > Bracelets > Gold > Gold Bracelets",
        "Jewelry > Earrings > Gold > Gold Earrings",
        "Jewelry > Rings > Gold > Gold Rings",
        "Beauty > Skincare > Face > Facial Cleansers",
        "Beauty > Skincare > Face > Serums",
        "Beauty > Skincare > Face > Moisturizers",
        "Beauty > Skincare > Face > Sunscreens",
        "Beauty > Makeup > Base > Foundations",
        "Beauty > Makeup > Eyes > Eyeshadow Palettes",
        "Beauty > Makeup > Lips > Lipsticks",
        "Beauty > Fragrance > Women > Eau de Parfum",
        "Beauty > Fragrance > Men > Eau de Cologne",
        "Beauty > Hair Care > Shampoo > Shampoos",
        "Beauty > Hair Care > Styling > Hair Straighteners",
        "Toys & Games > Educational > Puzzles > Adult Puzzles",
        "Toys & Games > Educational > Board Games > Family Board Games",
        "Toys & Games > Plush > Stuffed Animals > Plush Toys",
        "Toys & Games > Models > Figures > Action Figures",
        "Toys & Games > Remote Control > Cars > RC Cars",
        "Toys & Games > Outdoor > Bikes > Kids Bicycles",
        "Sports & Outdoors > Fitness > Strength > Dumbbells",
        "Sports & Outdoors > Fitness > Cardio > Treadmills",
        "Sports & Outdoors > Fitness > Accessories > Yoga Mats",
        "Sports & Outdoors > Fitness > Accessories > Resistance Bands",
        "Sports & Outdoors > Yoga > Mats > Travel Yoga Mats",
        "Sports & Outdoors > Camping > Tents > Backpacking Tents",
        "Sports & Outdoors > Cycling > Bikes > Mountain Bikes",
        "Sports & Outdoors > Cycling > Bikes > Road Bikes",
        "Pet Supplies > Dogs > Food > Dry Dog Food",
        "Pet Supplies > Dogs > Toys > Chew Toys",
        "Pet Supplies > Cats > Food > Dry Cat Food",
        "Pet Supplies > Cats > Litter > Clay Cat Litter",
        "Pet Supplies > Cats > Furniture > Cat Trees",
        "Tools > Power Tools > Drills > Impact Drills",
        "Tools > Power Tools > Saws > Circular Saws",
        "Tools > Hand Tools > Wrenches > Wrench Sets",
        "Tools > Hand Tools > Screwdrivers > Screwdriver Sets",
        "Tools > Measuring > Tape > Tape Measures",
        "Automotive > Accessories > Mounts > Vent Mounts",
        "Automotive > Accessories > Chargers > USB Car Chargers",
        "Automotive > Electronics > Dash Cams > Dash Cameras",
        "Baby > Feeding > Formula > Baby Formula",
        "Baby > Diapering > Diapers > Disposable Diapers",
        "Baby > Feeding > Bottles > Glass Baby Bottles",
        "Baby > Gear > Strollers > Lightweight Strollers",
        "Baby > Nursery > Cribs > Wooden Cribs",
        "Office > Stationery > Pens > Gel Pens",
        "Office > Stationery > Notebooks > Grid Notebooks",
        "Office > Equipment > Projectors > Business Projectors",
        "Office > Equipment > Shredders > Paper Shredders",
        "Grocery > Snacks > Nuts > Mixed Nuts",
        "Grocery > Snacks > Chocolate > Dark Chocolate",
        "Books > Books > Fiction > Bestseller Fiction",
        "Books > Books > Non-Fiction > Business Books",
        "Books > Books > Children > Picture Books"
    ]

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input(
                "📌 项目名称 *",
                value=st.session_state.project_name,
                placeholder="例：2026-06 Wireless Headphones Market Research"
            )
            if project_name:
                st.session_state.project_name = project_name
        
        with col2:
            search_term = st.text_input(
                "🔍 搜索类目",
                placeholder="输入关键词过滤类目（如：headphones, yoga）",
                key="category_search"
            )
            if search_term:
                filtered_categories = [cat for cat in CATEGORIES_EN if search_term.lower() in cat.lower()]
                filtered_categories = filtered_categories or ["未找到匹配类目"]
            else:
                filtered_categories = CATEGORIES_EN
            
            category = st.selectbox(
                "📂 目标类目 *",
                options=filtered_categories,
                index=0
            )
            if category != "请选择类目" and category != "未找到匹配类目":
                st.session_state.category = category
        
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
            elif not st.session_state.category or st.session_state.category in ["请选择类目", "未找到匹配类目"]:
                st.error("请选择目标类目")
            else:
                st.session_state.step = 2
                st.rerun()

# ============================================================
# STEP 2: 上传ABA数据（含智能文件读取）
# ============================================================
elif st.session_state.step == 2:
    st.markdown("### 📂 Step 2: 上传ABA原始数据")
    st.markdown("上传亚马逊品牌分析导出的 Top Search Terms 文件")

    st.markdown("""
    <div style="background-color: #eaf2f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
    <b>📋 支持格式：</b> .csv, .xlsx, .xls<br>
    • 自动识别中文/英文列名<br>
    • 自动跳过元数据行<br>
    • 建议导出最近一周的数据
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "选择 ABA 文件",
        type=["csv", "xlsx", "xls"],
        key="aba_upload"
    )

    if uploaded is not None:
        st.session_state.uploaded_files["aba"] = uploaded
        try:
            # ===== 智能读取文件 =====
            file_bytes = uploaded.getvalue()
            file_extension = uploaded.name.split('.')[-1].lower()
            
            # 检测第一行是否为元数据行（包含"报告范围"）
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
            elif file_extension in ['xlsx', 'xls']:
                uploaded.seek(0)
                df = pd.read_excel(uploaded, skiprows=skip_rows, engine='openpyxl')
            else:
                st.error(f"不支持的文件格式: {file_extension}")
                st.stop()
            
            st.success(f"✅ 已上传: {uploaded.name} ({len(df)} 行)")
            
            # ===== 立即执行初步分析 =====
            from core.parser import parse_aba_csv
            from core.clustering import semantic_clustering
            
            with st.spinner("正在分析ABA数据..."):
                use_ai = st.session_state.ai_enabled
                api_key = st.session_state.api_key if use_ai else None
                model = st.session_state.model if use_ai else None
                base_url = st.session_state.base_url if use_ai else None
                
                aba_result = parse_aba_csv(df)
                clusters = semantic_clustering(
                    aba_result, 
                    st.session_state.category,
                    use_ai=use_ai,
                    api_key=api_key,
                    model=model,
                    base_url=base_url
                )
            
            # 显示数据面板
            st.markdown("---")
            st.markdown("### 📊 Step 2 数据面板：调研候选清单")
            
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
            
            # 需要调研的关键词
            st.markdown("---")
            st.markdown("#### 🔍 需要调研的关键词（Top 30）")
            top_non_brand = aba_result.get("non_brand_keywords", [])[:30]
            if top_non_brand:
                keyword_data = []
                for i, item in enumerate(top_non_brand, 1):
                    keyword_data.append({
                        "序号": i,
                        "关键词": item.get("search_term", ""),
                        "ABA排名": item.get("search_frequency_rank", "N/A"),
                        "点击份额(%)": item.get("click_share", ""),
                        "转化份额(%)": item.get("conversion_share", ""),
                        "建议导出": "✅ 是"
                    })
                st.dataframe(pd.DataFrame(keyword_data), use_container_width=True, hide_index=True)
                
                keyword_list = "\n".join([item.get("search_term", "") for item in top_non_brand[:20]])
                st.download_button(
                    label="📋 复制关键词列表 (Top 20)",
                    data=keyword_list,
                    file_name="keywords_to_research.txt",
                    mime="text/plain"
                )
            
            # 需要调研的ASIN
            st.markdown("---")
            st.markdown("#### 📦 需要调研的 ASIN（Top 20）")
            top_asins = aba_result.get("top_asins", [])[:20]
            if top_asins:
                asin_data = []
                for i, (asin, count) in enumerate(top_asins, 1):
                    asin_data.append({
                        "序号": i,
                        "ASIN": asin,
                        "出现次数": count,
                        "建议导出": "✅ 是"
                    })
                st.dataframe(pd.DataFrame(asin_data), use_container_width=True, hide_index=True)
                
                asin_list = "\n".join([asin for asin, _ in top_asins[:15]])
                st.download_button(
                    label="📋 复制ASIN列表 (Top 15)",
                    data=asin_list,
                    file_name="asins_to_research.txt",
                    mime="text/plain"
                )
            
            # 高频修饰词/卖点
            st.markdown("---")
            st.markdown("#### 🏷️ 高频修饰词 / 卖点")
            top_mods = aba_result.get("top_modifiers", [])[:20]
            if top_mods:
                mod_text = "、".join([f"**{word}** ({count}次)" for word, count in top_mods])
                st.markdown(mod_text)
            
            # 细分市场聚类
            st.markdown("---")
            st.markdown("#### 📂 识别出的细分市场")
            if clusters:
                for cluster in clusters[:8]:
                    ai_tag = " 🤖" if cluster.get("ai_generated") else ""
                    with st.expander(f"📁 {cluster['name']}{ai_tag} ({cluster['keyword_count']}个关键词)"):
                        st.write(f"**平均ABA排名**: {cluster['avg_rank']:.0f}")
                        st.write(f"**平均点击份额**: {cluster['avg_click_share']:.2f}%")
                        st.write(f"**示例关键词**: {', '.join(cluster['keywords'][:5])}")
            else:
                st.info("未识别出明显聚类")
            
            # 存储结果
            st.session_state.aba_preview = {
                "total_keywords": aba_result.get("total_keywords", 0),
                "top_non_brand": top_non_brand,
                "top_asins": top_asins,
                "top_modifiers": top_mods,
                "clusters": clusters
            }

        except Exception as e:
            st.error(f"❌ 读取文件失败: {e}")
            import traceback
            st.code(traceback.format_exc())

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 上一步"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if "aba" not in st.session_state.uploaded_files:
                st.error("请上传ABA文件")
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
    for key in ["aba", "keyword", "asin"]:
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
                    
                    # 获取AI配置
                    use_ai = st.session_state.ai_enabled
                    api_key = st.session_state.api_key if use_ai else None
                    model = st.session_state.model if use_ai else None
                    base_url = st.session_state.base_url if use_ai else None
                    
                    # 解析ABA
                    aba_result = parse_aba_csv(data.get("aba"))
                    
                    # 聚类
                    clusters = semantic_clustering(
                        aba_result, 
                        st.session_state.category,
                        use_ai=use_ai,
                        api_key=api_key,
                        model=model,
                        base_url=base_url
                    )
                    
                    # 权重分级
                    total_keywords = aba_result.get("total_keywords", 1)
                    for cluster in clusters:
                        cluster["weight_level"] = assign_weight_level(
                            cluster.get("avg_rank", 999999), 
                            total_keywords
                        )
                    
                    # 10维评分
                    scored_markets = []
                    for cluster in clusters:
                        scores = calculate_10d_scores(
                            cluster, 
                            data.get("keyword"), 
                            data.get("asin"),
                            data.get("trend")
                        )
                        scored_markets.append(scores)
                    
                    # 趋势验证
                    if "trend" in data:
                        for market in scored_markets:
                            market["trend_result"] = trend_verification(market, data.get("trend"))
                    
                    # 评论分析（含AI）
                    comment_insights = []
                    if "review" in data:
                        comment_insights = analyze_comments(
                            data.get("review"), 
                            data.get("asin"),
                            use_ai=use_ai,
                            api_key=api_key,
                            model=model,
                            base_url=base_url
                        )
                    
                    # 生成报告
                    excel_data = generate_excel_report(
                        scored_markets,
                        data,
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
                        "keyword_count": len(aba_result.get("non_brand_keywords", [])),
                        "asin_count": len(data.get("asin", [])),
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
                
                ai_summary = market.get("ai_summary", "")
                st.markdown(f"""
                <div style="background-color:#f8f9fa; padding:0.8rem 1.2rem; border-radius:8px; margin-bottom:0.5rem;">
                    <span>#{i+1} <b>{market.get('name', 'N/A')}</b></span>
                    <span style="float:right;">综合分: {market.get('final_score', 0):.2f}  <span class="{grade_badge}">{market.get('grade', 'N/A')}</span></span>
                </div>
                """, unsafe_allow_html=True)
                if ai_summary:
                    st.info(f"💡 {ai_summary}")
        
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
        
        if st.button("🔄 重新分析"):
            st.session_state.step = 1
            st.session_state.analysis_complete = False
            st.session_state.analysis_result = None
            st.rerun()
    else:
        st.error("分析结果丢失，请重新执行分析")
        if st.button("重新开始"):
            st.session_state.step = 1
            st.rerun()
