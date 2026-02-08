#!/usr/bin/env python3
"""
API测试脚本 - 验证后端功能
模拟 Streamlit Cloud 环境的调用
"""

import sys
import os
sys.path.append('src')

# 设置环境变量
os.environ['DEEPSEEK_API_KEY'] = 'sk-cdebe0fafcf9406d962e3e09a0404e4b'

from expert_system_v2 import ExpertSystemV2
from pathlib import Path

def test_full_pipeline():
    """测试完整流程"""
    print("="*70)
    print("🧪 API 后端功能测试")
    print("="*70)
    
    # 1. 初始化系统
    print("\n1️⃣ 初始化专家系统...")
    try:
        system = ExpertSystemV2(data_dir='data')
        print("   ✅ 系统初始化成功")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False
    
    # 2. 测试检索
    print("\n2️⃣ 测试检索功能...")
    test_queries = [
        "徐凤年为什么要杀韩貂寺",
        "王仙芝为什么自称天下第二",
        "姜泥和徐凤年的关系"
    ]
    
    for query in test_queries:
        print(f"\n   查询: {query}")
        try:
            results = system.retrieve(query, top_k=2)
            print(f"   ✅ 找到 {len(results)} 个结果")
            print(f"   最佳匹配: [{results[0]['chapter']}] 相似度 {results[0]['similarity']:.3f}")
        except Exception as e:
            print(f"   ❌ 检索失败: {e}")
    
    # 3. 测试回答生成（只测一个，节省token）
    print("\n3️⃣ 测试回答生成...")
    query = "徐凤年为什么要杀韩貂寺？"
    print(f"   查询: {query}")
    
    try:
        result = system.answer(query)
        if result['success']:
            print(f"   ✅ 回答生成成功")
            print(f"   Token使用: {result['usage']['total_tokens']}")
            print(f"\n   回答预览（前200字）:")
            print(f"   {result['answer'][:200]}...")
        else:
            print(f"   ❌ 生成失败: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n" + "="*70)
    print("✅ 测试完成！")
    print("="*70)
    print("\n如果以上测试通过，部署应该正常工作。")
    print("请访问 https://snowsword-wiki.streamlit.app/ 进行前端测试。")
    
    return True

if __name__ == "__main__":
    test_full_pipeline()
