# Lerer-aba-niche-analysis-tool
ABA关键词利基分析工具+sif和卖家精灵 - 全手动版 
markdown
# 🚀 ABA利基分析工具

全手动、零API依赖的亚马逊ABA关键词利基分析工具

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🚫 零API依赖 | 无需任何第三方接口，完全本地运行 |
| 🖥️ 向导式界面 | 5步操作，上传文件即得报告 |
| 🧠 10维评分 | 市场规模、转化、竞争、成长、利润、品牌垄断、新品存活、卖点接受、价格弹性、季节性 |
| 📊 九象限验证 | 销量/价格变化判断卖点市场象限 |
| 💬 评论挖掘 | 情感分析 + 产品优化建议 |
| 📈 入场规划 | 季节性分析 + 备货时间线 |
| 📋 6 Sheet报告 | 细分市场总览、关键词明细、ASIN排行、评论洞察、入场时机、卖点趋势 |

---

## 📦 安装与使用

### 1. 克隆仓库

```bash
git clone https://github.com/ABRAHAM-3178/Lerer-aba-niche-analysis-tool.git
cd Lerer-aba-niche-analysis-tool
2. 安装依赖
bash
pip install -r requirements.txt
3. 运行工具
bash
streamlit run app.py
浏览器会自动打开 http://localhost:8501

📂 文件上传说明
文件	必填	说明	来源
ABA原始CSV	✅	Top Search Terms报告	亚马逊品牌分析
关键词数据表	✅	关键词深度数据	卖家精灵
ASIN数据表	✅	ASIN详情数据	卖家精灵
评论数据表	条件必填	评论>200的ASIN需提供	卖家精灵插件
Sif流量词表	可选	反查流量词结果	Sif
趋势验证表	可选	销量/价格变化数据	卖家精灵
📊 输出报告（6个Sheet）
Sheet	内容
1. 细分市场总览	10维评分、综合分、等级、推荐说明
2. 关键词明细	每个关键词的权重等级、得分、排名
3. ASIN排行	竞品ASIN分析、进入建议
4. 评论洞察	用户痛点、好评、产品优化建议
5. 入场时机	季节性分析、备货时间线
6. 卖点趋势	九象限验证、市场象限判断
🛠️ 技术栈
Python 3.8+

Streamlit

Pandas

OpenPyXL
