"""
雪中悍刀行 - 专家级智能百科 V2
整合语义检索、知识图谱、深度分析
"""

import streamlit as st
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

# 页面配置
st.set_page_config(
    page_title="雪中悍刀行 - 专家级百科",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .main { padding: 2rem; }
    .header-text { text-align: center; color: #1f1f1f; }
    .subtitle { text-align: center; color: #666; margin-bottom: 1rem; }
    .answer-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        padding: 25px;
        border-radius: 12px;
        border-left: 5px solid #ff4b4b;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .section-fact { border-left: 4px solid #3498db; padding-left: 15px; margin: 15px 0; }
    .section-analysis { border-left: 4px solid #e74c3c; padding-left: 15px; margin: 15px 0; }
    .section-sublime { border-left: 4px solid #9b59b6; padding-left: 15px; margin: 15px 0; }
    .feature-badge {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        margin: 0 5px 5px 0;
    }
    .stats-card {
        background: #fff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .stats-number { font-size: 24px; font-weight: bold; color: #ff4b4b; }
    .stats-label { font-size: 12px; color: #666; }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown("<h1 class='header-text'>📚 雪中悍刀行 · 专家级百科</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>深度解读这部江湖 | 专家视角 · 文学评论 · 可溯源</p>", unsafe_allow_html=True)

# 功能标签
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="feature-badge">🔍 语义检索</span>
        <span class="feature-badge">🕸️ 知识图谱</span>
        <span class="feature-badge">📖 原文溯源</span>
        <span class="feature-badge">🎭 深度解读</span>
    </div>
    """, unsafe_allow_html=True)

# 数据展示（静态展示，实际应从文件读取）
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="stats-card">
        <div class="stats-number">12,378</div>
        <div class="stats-label">原文段落</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="stats-card">
        <div class="stats-number">10,820</div>
        <div class="stats-label">实体记录</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="stats-card">
        <div class="stats-number">2,236</div>
        <div class="stats-label">关键事件</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="stats-card">
        <div class="stats-number">14</div>
        <div class="stats-label">核心人物</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 搜索框
query = st.text_input(
    "💭 提出一个关于《雪中悍刀行》的深度问题",
    placeholder="例如：徐凤年为什么要杀韩貂寺？这对他意味着什么？",
    key="query"
)

# 示例问题
if not query:
    st.caption("💡 试试这些深度问题：")
    example_cols = st.columns(3)
    examples = [
        "徐凤年为什么要杀韩貂寺？",
        "王仙芝为什么自称天下第二？",
        "李淳罡为什么被困听潮阁？",
        "姜泥和徐凤年的结局是什么？",
        "徐凤年的武道成长经历了哪些阶段？",
        "北凉和北莽的冲突根源是什么？"
    ]
    for i, ex in enumerate(examples):
        if example_cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.query = ex
            st.rerun()

# 提交按钮
if query:
    if st.button("🔍 深度分析", type="primary", use_container_width=True):
        with st.spinner("🤔 专家正在分析..."):
            try:
                # 这里应该调用 ExpertAIV2，但为演示先用模拟数据
                # 实际部署时取消注释下面代码：
                # from expert_ai_v2 import ExpertAIV2
                # ai = ExpertAIV2()
                # result = ai.answer(query)
                
                # 模拟结果（实际应删除）
                result = {
                    "success": True,
                    "answer": """**【事实层】**
徐凤年在太安城外设局斩杀韩貂寺。这场战斗不是简单的武力对决，而是精心策划的复仇。

**【分析层】**
这一行为包含三重必然：
1. **情感逻辑**：完成母亲遗愿，为白衣案报仇
2. **政治觉醒**：向离阳皇室宣示北凉意志
3. **武道突破**：从被保护者成长为布局者

**【升华层】**
这是徐凤年从"世子"到"北凉王"的精神成人礼。通过完成复仇，他理解了父亲的选择，并找到了自己的道路。""",
                    "usage": {"total_tokens": 850}
                }
                
                if result.get("success"):
                    # 显示回答
                    st.markdown("<div class='answer-box'>", unsafe_allow_html=True)
                    
                    # 解析三段式回答并渲染
                    answer = result['answer']
                    
                    if "**【事实层】**" in answer:
                        # 格式化三段式回答
                        sections = answer.split("**【")
                        for section in sections:
                            if section.strip():
                                if "事实层】**" in section:
                                    st.markdown("""
                                    <div class="section-fact">
                                        <h4>📖 事实层</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(section.replace("事实层】**", "").strip())
                                elif "分析层】**" in section:
                                    st.markdown("""
                                    <div class="section-analysis">
                                        <h4>🔍 分析层</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(section.replace("分析层】**", "").strip())
                                elif "升华层】**" in section:
                                    st.markdown("""
                                    <div class="section-sublime">
                                        <h4>✨ 升华层</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(section.replace("升华层】**", "").strip())
                    else:
                        st.markdown(answer)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 参考来源
                    with st.expander("📚 参考来源"):
                        st.markdown("""
                        **相关人物**：徐凤年、韩貂寺、吴素
                        
                        **关键章节**：第XXX章 太安城之战
                        
                        **引用原文**：
                        > "你娘吴素，是咱家亲手杀的。" —— 韩貂寺临终
                        
                        **知识图谱**：
                        - 徐凤年 → 韩貂寺：杀母之仇
                        - 韩貂寺 → 离阳皇室：执行者关系
                        """)
                    
                    # Token 使用
                    st.caption(f"💰 Token 使用: {result['usage']['total_tokens']} | 模型: DeepSeek-V3")
                else:
                    st.error(f"生成回答失败: {result.get('error', '未知错误')}")
            
            except Exception as e:
                st.error(f"处理失败: {e}")

# 页脚
st.markdown("---")
st.caption("📌 基于《雪中悍刀行》全文构建 | 使用 DeepSeek AI 驱动 | 专家级文学分析")
