"""
Streamlit 主应用
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent))

from src.retriever import TextRetriever
from src.chat import DeepSeekChat

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
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .source-box {
        background-color: #fafafa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        font-size: 14px;
        color: #666;
    }
    .header-text {
        text-align: center;
        color: #1f1f1f;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_retriever():
    """缓存检索器，支持自动构建索引"""
    try:
        return TextRetriever()
    except FileNotFoundError as e:
        # 索引不存在，尝试自动构建
        st.info("📦 首次启动，正在构建索引（约需 1-2 分钟）...")
        try:
            from src.indexer import TextIndexer
            import json
            
            data_dir = Path("data")
            text_file = data_dir / "雪中悍刀行.txt"
            
            if not text_file.exists():
                st.error(f"找不到小说文本文件: {text_file}")
                return None
            
            # 构建索引
            indexer = TextIndexer(chunk_size=800, overlap=100)
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            chunks = indexer.create_chunks(text)
            
            # 保存索引
            chunks_path = data_dir / "chunks.json"
            with open(chunks_path, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False)
            
            st.success(f"✅ 索引构建完成！共 {len(chunks)} 个文本块")
            
            # 重新加载
            return TextRetriever()
        except Exception as build_error:
            st.error(f"构建索引失败: {build_error}")
            return None
    except Exception as e:
        st.error(f"加载索引失败: {e}")
        return None

@st.cache_resource
def load_chat():
    """缓存 Chat 客户端"""
    try:
        api_key = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return None
        return DeepSeekChat(api_key)
    except Exception as e:
        st.error(f"初始化 DeepSeek 失败: {e}")
        return None

def main():
    # 标题
    st.markdown("<h1 class='header-text'>📚 雪中悍刀行 · 智能百科</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>基于小说原文的精准问答系统 | 零幻觉 · 可追溯</p>", unsafe_allow_html=True)
    
    # 初始化
    retriever = load_retriever()
    
    # 检查 API Key（优先从环境变量读取，避免 secrets.toml 解析错误）
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    # 如果环境变量没有，再尝试从 secrets 读取（用于 Streamlit Cloud）
    if not api_key:
        try:
            api_key = st.secrets.get("DEEPSEEK_API_KEY")
        except Exception:
            api_key = None
    
    if not api_key:
        st.warning("⚠️ 请配置 DeepSeek API Key")
        with st.expander("如何配置 API Key"):
            st.markdown("""
            **本地运行：**
            ```bash
            export DEEPSEEK_API_KEY="your-api-key"
            streamlit run app.py
            ```
            
            **Streamlit Cloud：**
            1. 点击右上角 "⋮" → Settings
            2. 选择 Secrets
            3. 添加：`DEEPSEEK_API_KEY = "your-api-key"`
            """)
        return
    
    chat = load_chat()
    
    if not retriever:
        st.error("❌ 数据索引加载失败，请确认已运行 indexer.py 构建索引")
        return
    
    # 侧边栏 - 搜索设置
    with st.sidebar:
        st.header("⚙️ 设置")
        
        top_k = st.slider("检索段落数", min_value=1, max_value=10, value=5, 
                         help="检索多少个相关段落作为回答依据")
        
        temperature = st.slider("回答创造性", min_value=0.0, max_value=1.0, value=0.3,
                               help="越低越严格基于原文，越高越灵活")
        
        st.divider()
        
        st.header("📊 系统状态")
        st.write(f"索引块数: {len(retriever.chunks)}")
        st.write(f"关键词数: {len(retriever.keyword_index)}")
        
        st.divider()
        
        st.header("💡 示例问题")
        examples = [
            "徐凤年是谁？",
            "黄蛮儿有什么特殊能力？",
            "北凉王府在哪里？",
            "徐骁有几个孩子？",
            "龙虎山是什么地方？"
        ]
        
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                st.session_state.query = ex
                st.rerun()
    
    # 主界面 - 搜索框
    query = st.text_input(
        "输入你的问题",
        value=st.session_state.get("query", ""),
        placeholder="例如：徐凤年是谁？北凉王府在哪里？",
        key="query_input"
    )
    
    if query:
        # 显示进度
        with st.spinner("🔍 正在检索相关内容..."):
            results = retriever.retrieve(query, top_k=top_k)
            context = retriever.get_context(query, top_k=top_k)
        
        if not results:
            st.warning("😕 未找到相关内容，请尝试其他关键词")
            return
        
        # 生成回答
        st.markdown("### 🤖 AI 回答")
        
        answer_container = st.container()
        
        with st.spinner("🤖 正在生成回答..."):
            # 使用流式输出
            answer_text = ""
            answer_placeholder = answer_container.empty()
            
            for chunk in chat.chat_stream(query, context, temperature=temperature):
                answer_text += chunk
                answer_placeholder.markdown(f"<div class='answer-box'>{answer_text}</div>", 
                                          unsafe_allow_html=True)
        
        # 显示来源
        with st.expander("📖 查看原文出处", expanded=False):
            for i, result in enumerate(results, 1):
                st.markdown(f"""
                <div class='source-box'>
                <strong>参考 {i} - {result['chapter']}</strong> (相关度: {result['relevance_score']})<br>
                {result['content'][:400]}{'...' if len(result['content']) > 400 else ''}
                </div>
                """, unsafe_allow_html=True)
                st.write("")
        
        # Token 使用信息（调试用）
        # result = chat.chat(query, context, temperature=temperature)
        # if result["success"]:
        #     st.caption(f"Token 使用: {result['usage']['total_tokens']} (提示: {result['usage']['prompt_tokens']}, 生成: {result['usage']['completion_tokens']})")

if __name__ == "__main__":
    main()
