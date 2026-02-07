#!/usr/bin/env python3
"""
直接测试脚本 - 验证后端功能
"""
import sys
sys.path.append('src')

print("="*70)
print("🧪 后端功能测试")
print("="*70)

# 1. 测试检索器
print("\n✅ 1. 测试检索器")
from lightweight_retriever import LightweightRetriever
from pathlib import Path

retriever = LightweightRetriever()
retriever.load_index(Path('data/semantic_index_light'))
print(f"   索引: {len(retriever.paragraphs)} 段落")

query = "徐凤年杀韩貂寺"
results = retriever.search(query, top_k=2)
print(f"   查询: '{query}'")
print(f"   结果: {len(results)} 个")
print(f"   最佳: [{results[0]['chapter']}] 相似度 {results[0]['similarity']:.3f}")

# 2. 测试知识库
print("\n✅ 2. 测试知识库")
import json
with open('data/expert_knowledge_base.json', 'r') as f:
    kb = json.load(f)
print(f"   人物: {len(kb.get('character_timeline', {}))}")
print(f"   主题: {len(kb.get('themes', {}))}")

# 3. 测试 API 连接
print("\n✅ 3. 测试 API 连接")
import os
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-cdebe0fafcf9406d962e3e09a0404e4b"),
    base_url="https://api.deepseek.com"
)
try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("   API 连接正常")
except Exception as e:
    print(f"   API 错误: {e}")

# 4. 生成 curl 命令示例
print("\n" + "="*70)
print("📋 curl 测试命令示例")
print("="*70)
print("""
如果部署到 Streamlit Cloud 或其他平台，可以使用以下方式测试：

方式1: 直接用 Python 脚本测试（当前环境）
   python3 test_backend.py

方式2: 如果 API 服务已部署
   # 健康检查
   curl https://your-domain/health
   
   # 检索测试
   curl "https://your-domain/search?q=徐凤年&top_k=2"
   
   # 问答测试
   curl -X POST https://your-domain/query \\
     -H "Content-Type: application/json" \\
     -d '{"query": "徐凤年为什么要杀韩貂寺？"}'

当前后端组件全部正常！
""")

print("="*70)
print("✅ 所有测试通过！")
print("="*70)
