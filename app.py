#!/usr/bin/env python3
"""
雪中悍刀行 - 专家级智能百科 V2 (支持智谱语义检索)
整合语义检索、知识图谱、深度分析
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path

# ==================== API 模式 (GET/POST) ====================
# 支持 curl GET/POST 调用，返回 JSON 而不是 HTML
# 
# GET 用法:
#   curl "https://snowsword-wiki.streamlit.app/?api_mode=1&action=health"
#   curl "https://snowsword-wiki.streamlit.app/?api_mode=1&action=stats"
#   curl "https://snowsword-wiki.streamlit.app/?api_mode=1&action=query&q=徐凤年"
#
# POST 用法:
#   curl -X POST "https://snowsword-wiki.streamlit.app/?api_mode=1&action=ask" \
#     -H "Content-Type: application/json" \
#     -d '{"query":"徐凤年为什么要杀韩貂寺","temperature":0.7}'

import hashlib
import time
from functools import lru_cache

# 简单的内存缓存（重启后失效）
_answer_cache = {}
_cache_max_size = 100  # 最多缓存 100 个回答
_cache_ttl = 3600  # 缓存 1 小时

def _get_cache_key(query: str, temp: float) -> str:
    """生成缓存键"""
    return hashlib.md5(f"{query}:{temp}".encode()).hexdigest()

def _get_cached_answer(query: str, temp: float):
    """获取缓存的回答"""
    key = _get_cache_key(query, temp)
    if key in _answer_cache:
        data, timestamp = _answer_cache[key]
        if time.time() - timestamp < _cache_ttl:
            return data
        else:
            del _answer_cache[key]
    return None

def _set_cached_answer(query: str, temp: float, answer: dict):
    """设置缓存"""
    key = _get_cache_key(query, temp)
    # 清理过期缓存
    now = time.time()
    expired_keys = [k for k, (_, ts) in _answer_cache.items() if now - ts > _cache_ttl]
    for k in expired_keys:
        del _answer_cache[k]
    # 限制缓存大小
    if len(_answer_cache) >= _cache_max_size:
        oldest_key = min(_answer_cache.keys(), key=lambda k: _answer_cache[k][1])
        del _answer_cache[oldest_key]
    _answer_cache[key] = (answer, now)

query_params = st.query_params

if query_params.get("api_mode") == "1":
    action = query_params.get("action", "health")
    
    if action == "health":
        cache_info = {
            "cached_count": len(_answer_cache),
            "max_size": _cache_max_size,
            "ttl_seconds": _cache_ttl
        }
        st.json({
            "status": "healthy",
            "service": "雪中悍刀行专家级百科",
            "version": "2.1.0",
            "mode": "streamlit_cloud",
            "cache": cache_info
        })
    
    elif action == "stats":
        st.json({
            "paragraphs": 12378,
            "entities": 10820,
            "events": 2236,
            "characters": 14,
            "source": "雪中悍刀行全文",
            "cache_enabled": True,
            "cached_answers": len(_answer_cache)
        })
    
    elif action == "search":
        # 简单返回搜索接口信息
        st.json({
            "endpoint": "search",
            "note": "Streamlit Cloud 不支持完整搜索 API",
            "frontend_url": "https://snowsword-wiki.streamlit.app",
            "available": ["health", "stats", "query", "ask", "cache_clear"]
        })
    
    elif action == "query":
        # GET 方式简单查询（返回缓存或未缓存状态）
        q = query_params.get("q", "")
        temp = float(query_params.get("temp", 0.7))
        if not q:
            st.json({"error": "Missing parameter 'q'", "example": "?api_mode=1&action=query&q=徐凤年"})
        else:
            cached = _get_cached_answer(q, temp)
            if cached:
                st.json({
                    "query": q,
                    "cached": True,
                    "answer_preview": cached.get("answer", "")[:100] + "..." if len(cached.get("answer", "")) > 100 else cached.get("answer", "")
                })
            else:
                st.json({
                    "query": q,
                    "cached": False,
                    "message": "使用 action=ask POST 请求获取完整回答",
                    "cached_count": len(_answer_cache)
                })
    
    elif action == "ask":
        # GET 方式获取回答（简化版，不加载专家系统以避免超时）
        q = query_params.get("q", "")
        temp = float(query_params.get("temp", 0.7))
        
        if not q:
            st.json({
                "error": "Missing parameter 'q'",
                "example": "?api_mode=1&action=ask&q=徐凤年是谁"
            })
        else:
            # 检查缓存
            cached = _get_cached_answer(q, temp)
            if cached:
                st.json({
                    "success": True,
                    "query": q,
                    "cached": True,
                    "answer": cached.get("answer"),
                    "usage": cached.get("usage", {}),
                    "note": "此回答来自缓存"
                })
            else:
                # 简化版：返回提示信息，避免在 Streamlit Cloud 上初始化重型系统
                mock_answer = f"这是一个简化版回答。您的问题是：{q}\n\n在实际应用中，这里会调用 DeepSeek AI 生成详细回答。由于 Streamlit Cloud 资源限制，请使用前端界面进行完整问答。"
                result = {
                    "success": True,
                    "answer": mock_answer,
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                }
                # 缓存这个简化回答
                _set_cached_answer(q, temp, result)
                
                st.json({
                    "success": True,
                    "query": q,
                    "cached": False,
                    "answer": result.get("answer"),
                    "usage": result.get("usage"),
                    "cached_total": len(_answer_cache),
                    "note": "此为简化版回答，请使用前端获取完整 AI 回答"
                })
    
    elif action == "cache_clear":
        # 清除缓存
        _answer_cache.clear()
        st.json({"success": True, "message": "Cache cleared"})
    
    else:
        st.json({
            "error": "Unknown action",
            "available_actions": ["health", "stats", "query", "ask", "cache_clear"],
            "version": "2.1.0"
        })
    
    st.stop()  # 停止渲染页面其余部分

# ==================== 正常页面模式 ====================

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent))

from src.expert_system_v2 import ExpertSystemV2

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
    .section-fact { 
        border-left: 4px solid #3498db; 
        padding-left: 15px; 
        margin: 15px 0;
        background: rgba(52, 152, 219, 0.1);
        padding: 10px 10px 10px 20px;
        border-radius: 0 8px 8px 0;
    }
    .section-analysis { 
        border-left: 4px solid #e74c3c; 
        padding-left: 15px; 
        margin: 15px 0;
        background: rgba(231, 76, 60, 0.1);
        padding: 10px 10px 10px 20px;
        border-radius: 0 8px 8px 0;
    }
    .section-sublime { 
        border-left: 4px solid #9b59b6; 
        padding-left: 15px; 
        margin: 15px 0;
        background: rgba(155, 89, 182, 0.1);
        padding: 10px 10px 10px 20px;
        border-radius: 0 8px 8px 0;
    }
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
    .retrieval-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    .retrieval-semantic { background: #4caf50; color: white; }
    .retrieval-tfidf { background: #ff9800; color: white; }
</style>
""", unsafe_allow_html=True)

# 初始化专家系统（缓存）
@st.cache_resource
def get_expert_system():
    """初始化专家系统（只加载一次）"""
    try:
        # 从环境变量或 secrets 读取 API Key
        api_key = os.getenv("DEEPSEEK_API_KEY")
        zhipu_key = os.getenv("ZHIPU_API_KEY")
        
        # 尝试从 secrets 读取
        try:
            if not api_key:
                api_key = st.secrets.get("DEEPSEEK_API_KEY")
            if not zhipu_key:
                zhipu_key = st.secrets.get("ZHIPU_API_KEY")
        except:
            pass
        
        if not api_key:
            return None, "missing_key"
        
        with st.spinner("📦 正在加载知识库..."):
            system = ExpertSystemV2(
                data_dir="data", 
                api_key=api_key,
                zhipu_api_key=zhipu_key
            )
            
            # 检查是否使用了语义检索
            retrieval_mode = "semantic" if system.use_semantic else "tfidf"
            
            return system, retrieval_mode
    except Exception as e:
        st.error(f"❌ 加载失败: {e}")
        return None, str(e)

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

# 数据展示
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

# 初始化专家系统
system, status = get_expert_system()

# API Key 检查
if not system:
    st.warning("⚠️ 请配置 API Keys")
    with st.expander("如何配置"):
        st.markdown("""
        在 Streamlit Cloud 的 Advanced Settings → Secrets 中添加：
        ```toml
        DEEPSEEK_API_KEY = "sk-..."
        ZHIPU_API_KEY = "7bf1e26ae11344a09b9886056c12da01.5sNpyInlYXwp2ajB"
        ```
        
        - **ZHIPU_API_KEY**: 用于语义检索（提升匹配质量）
        - **DEEPSEEK_API_KEY**: 用于生成回答（必须）
        """)
    st.stop()

# 显示检索模式
if status == "semantic":
    st.success("✅ 已启用智谱语义检索 - 匹配质量更高")
else:
    st.info("ℹ️ 使用 TF-IDF 检索 - 配置 ZHIPU_API_KEY 可启用语义检索")

# 搜索框
query = st.text_input(
    "💭 提出一个关于《雪中悍刀行》的深度问题",
    placeholder="例如：徐凤年为什么要杀韩貂寺？这对他意味着什么？",
    key="query_input"
)

# 示例问题
def set_query(query_text):
    """设置查询文本"""
    st.session_state.query_input = query_text

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
        example_cols[i % 3].button(
            ex, 
            key=f"ex_{i}", 
            use_container_width=True,
            on_click=set_query,
            args=(ex,)
        )

# 提交按钮
if query:
    if st.button("🔍 深度分析", type="primary", use_container_width=True):
        with st.spinner("🤔 专家正在分析..."):
            try:
                # 生成回答
                result = system.answer(query)
                
                if result.get("success"):
                    # 显示检索模式标签
                    retrieval_mode = result.get('retrieval_mode', 'unknown')
                    if retrieval_mode == 'semantic':
                        st.markdown("""
                        <div style="text-align: right; margin-bottom: 10px;">
                            <span class="retrieval-badge retrieval-semantic">🔍 语义检索</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="text-align: right; margin-bottom: 10px;">
                            <span class="retrieval-badge retrieval-tfidf">🔍 TF-IDF检索</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 显示回答
                    st.markdown("<div class='answer-box'>", unsafe_allow_html=True)
                    
                    # 解析三段式回答
                    answer = result['answer']
                    
                    # 处理不同格式的回答
                    if "**【" in answer:
                        # 标准三段式
                        sections = answer.split("**【")
                        for section in sections:
                            if section.strip():
                                if "事实层】**" in section:
                                    st.markdown("""
                                    <div class="section-fact">
                                        <h4 style="color: #3498db; margin-bottom: 10px;">📖 事实层</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(section.replace("事实层】**", "").strip())
                                elif "分析层】**" in section:
                                    st.markdown("""
                                    <div class="section-analysis">
                                        <h4 style="color: #e74c3c; margin-bottom: 10px;">🔍 分析层</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(section.replace("分析层】**", "").strip())
                                elif "升华层】**" in section:
                                    st.markdown("""
                                    <div class="section-sublime">
                                        <h4 style="color: #9b59b6; margin-bottom: 10px;">✨ 升华层</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(section.replace("升华层】**", "").strip())
                    else:
                        # 非标准格式，直接显示
                        st.markdown(answer)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 显示参考来源
                    with st.expander("📚 参考来源"):
                        # 获取检索到的段落
                        context = system.get_context(query, top_k=3)
                        st.markdown("**检索到的相关原文：**")
                        st.markdown(context[:1000] + "...")
                    
                    # Token 使用
                    st.caption(f"💰 Token 使用: {result['usage']['total_tokens']} | 模型: DeepSeek-V3")
                else:
                    st.error(f"生成回答失败: {result.get('error', '未知错误')}")
            
            except Exception as e:
                st.error(f"处理失败: {e}")
                import traceback
                st.error(traceback.format_exc())

# 页脚
st.markdown("---")
st.caption("📌 基于《雪中悍刀行》全文构建 | 语义检索 + DeepSeek AI 驱动 | 专家级文学分析")
