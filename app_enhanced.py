"""
雪中悍刀行 - 增强版智能百科
使用向量检索 + 知识图谱 + 章节摘要
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent))

from src.enhanced_retriever import EnhancedRetriever
from src.enhanced_chat import EnhancedChat

# 页面配置
st.set_page_config(
    page_title="雪中悍刀行 - 智能百科",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .answer-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        color: #1f1f1f !important;
        font-size: 16px;
        line-height: 1.8;
        margin-top: 15px;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        font-size: 13px;
        color: #555 !important;
        margin-top: 15px;
    }
    .header-text {
        text-align: center;
        color: #1f1f1f !important;
    }
    .subtitle {
        text-align: center;
        color: #666 !important;
        margin-bottom: 2rem;
    }
    .feature-badge {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 8px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_retriever():
    """加载增强检索器"""
    try:
        with st.spinner("📦 正在加载知识库，请稍候..."):
            return EnhancedRetriever()
    except Exception as e:
        st.error(f"❌ 加载知识库失败: {e}")
        return None


@st.cache_resource
def load_chat():
    """加载聊天模块"""
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            # 尝试从 secrets 读取
            try:
                api_key = st.secrets.get("DEEPSEEK_API_KEY")
            except:
                pass
        
        if not api_key:
            return None
        return EnhancedChat(api_key)
    except Exception as e:
        st.error(f"初始化失败: {e}")
        return None


def main():
    # 标题
    st.markdown("<h1 class='header-text'>📚 雪中悍刀行 · 智能百科</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>读懂这部江湖 | 向量检索 + 知识图谱 + 智能推理</p>", unsafe_allow_html=True)
    
    # 功能标签
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <span class="feature-badge">🔍 语义检索</span>
            <span class="feature-badge">🕸️ 知识图谱</span>
            <span class="feature-badge">📖 章节摘要</span>
            <span class="feature-badge">🧠 智能推理</span>
        </div>
        """, unsafe_allow_html=True)
    
    # 初始化
    retriever = load_retriever()
    chat = load_chat()
    
    # API Key 检查
    if not chat:
        st.warning("⚠️ 请配置 DeepSeek API Key")
        with st.expander("如何配置"):
            st.markdown("""
            在 Streamlit Cloud 的 Advanced Settings 中添加：
            - **Key**: `DEEPSEEK_API_KEY`
            - **Value**: `sk-...`
            """)
        return
    
    # 检查知识库
    if not retriever:
        st.error("❌ 知识库加载失败，请检查数据文件")
        return
    
    # 显示知识库状态
    with st.expander("📊 知识库状态"):
        st.markdown(f"- **文本块**: {len(retriever.chunks):,} 个")
        if retriever.knowledge_graph:
            chars = len(retriever.knowledge_graph.get('characters', {}))
            st.markdown(f"- **人物**: {chars} 个")
        if retriever.chapter_summaries:
            st.markdown(f"- **章节**: {len(retriever.chapter_summaries)} 章")
    
    # 搜索框
    st.markdown("---")
    
    query = st.text_input(
        "💭 问一个关于《雪中悍刀行》的问题",
        placeholder="例如：徐凤年为什么杀韩貂寺？姜泥和徐凤年最后在一起了吗？",
        key="query_input"
    )
    
    # 示例问题
    if not query:
        st.caption("💡 试试这些问题：")
        cols = st.columns(3)
        examples = [
            "徐凤年为什么杀韩貂寺？",
            "李淳罡为什么被困听潮阁？",
            "姜泥和徐凤年的结局是什么？",
            "王仙芝为什么自称天下第二？",
            "北凉和北莽的关系如何？"
        ]
        for i, ex in enumerate(examples):
            if cols[i % 3].button(ex, key=f"ex_{i}"):
                st.session_state.query_input = ex
                st.rerun()
    
    # 提交按钮
    if query:
        if st.button("🔍 搜索", type="primary", use_container_width=True):
            with st.spinner("🤔 正在思考..."):
                try:
                    # 获取上下文
                    context = retriever.get_context(query, top_k=5)
                    
                    # 生成回答
                    result = chat.chat(query, context, temperature=0.7)
                    
                    if result['success']:
                        # 显示回答
                        st.markdown("<div class='answer-box'>", unsafe_allow_html=True)
                        st.markdown(result['answer'])
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # 显示参考来源
                        with st.expander("📖 参考原文"):
                            st.markdown(f"<div class='source-box'>{context.replace(chr(10), '<br>')}</div>", 
                                      unsafe_allow_html=True)
                        
                        # Token 使用
                        st.caption(f"💰 Token: {result['usage']['total_tokens']} | 模型: {result['model']}")
                    else:
                        st.error(f"生成回答失败: {result['error']}")
                
                except Exception as e:
                    st.error(f"处理失败: {e}")
    
    # 页脚
    st.markdown("---")
    st.caption("基于《雪中悍刀行》全文构建 | 使用 DeepSeek AI 驱动")


if __name__ == "__main__":
    main()
