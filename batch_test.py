#!/usr/bin/env python3
"""
批量测试 - 自动运行预设问题
"""

import sys
import time
sys.path.append('src')

from enhanced_retriever import EnhancedRetriever
from enhanced_chat import EnhancedChat

# 测试问题
test_queries = [
    "徐凤年为什么要杀韩貂寺？",
    "王仙芝为什么自称天下第二？",
    "姜泥和徐凤年的结局是什么？",
]

def main():
    print("="*80)
    print("🧪 增强版批量测试")
    print("="*80)
    
    api_key = "sk-cdebe0fafcf9406d962e3e09a0404e4b"
    
    # 加载
    print("\n📦 加载知识库...")
    retriever = EnhancedRetriever('data')
    chat = EnhancedChat(api_key)
    print("✅ 加载完成\n")
    
    # 测试每个问题
    for i, query in enumerate(test_queries, 1):
        print("\n" + "="*80)
        print(f"【测试 {i}/{len(test_queries)}】")
        print(f"❓ 问题: {query}")
        print("="*80)
        
        start = time.time()
        
        # 检索
        print("\n📖 检索中...")
        context = retriever.get_context(query, top_k=3)
        
        # 显示检索信息
        if "【人物背景】" in context:
            print("   ✓ 包含人物背景")
        if "【相关原文】" in context:
            print("   ✓ 包含原文片段")
        
        # 生成回答
        print("\n🤖 生成回答...")
        result = chat.chat(query, context, temperature=0.7)
        
        elapsed = time.time() - start
        
        if result['success']:
            print(f"\n💬 回答 (耗时 {elapsed:.1f}s, {result['usage']['total_tokens']} tokens):")
            print("-" * 80)
            print(result['answer'])
            print("-" * 80)
        else:
            print(f"❌ 错误: {result['error']}")
        
        print()
    
    print("\n" + "="*80)
    print("✅ 所有测试完成!")
    print("="*80)

if __name__ == "__main__":
    main()
