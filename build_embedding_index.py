#!/usr/bin/env python3
"""
构建 DeepSeek Embedding 索引
将小说文本转换为向量索引
"""

import os
import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.deepseek_retriever import DeepSeekEmbeddingRetriever


def build_embedding_index(
    paragraphs_file: Path,
    output_dir: Path,
    api_key: str = None,
    max_paragraphs: int = None
):
    """
    构建 DeepSeek Embedding 索引
    
    Args:
        paragraphs_file: 段落 JSON 文件路径
        output_dir: 索引输出目录
        api_key: DeepSeek API Key（默认从环境变量读取）
        max_paragraphs: 最大处理段落数（测试用）
    """
    print("🚀 构建 DeepSeek Embedding 索引")
    print("="*60)
    
    # 加载段落
    print(f"📂 加载段落文件: {paragraphs_file}")
    with open(paragraphs_file, 'r', encoding='utf-8') as f:
        all_paragraphs = json.load(f)
    
    print(f"   共 {len(all_paragraphs)} 个段落")
    
    # 限制数量（测试用）
    if max_paragraphs:
        all_paragraphs = all_paragraphs[:max_paragraphs]
        print(f"   ⚠️ 测试模式：只处理前 {max_paragraphs} 个段落")
    
    # 创建检索器
    retriever = DeepSeekEmbeddingRetriever(api_key=api_key)
    
    # 构建索引
    retriever.build_index(all_paragraphs, output_dir)
    
    print("\n✅ 索引构建完成！")
    print(f"   输出目录: {output_dir}")
    print(f"   向量维度: {retriever.dimension}")
    print(f"   段落数量: {len(retriever.paragraphs)}")
    
    # 测试检索
    print("\n🧪 测试检索...")
    test_query = "徐凤年为什么要杀韩貂寺"
    results = retriever.search(test_query, top_k=3)
    
    print(f"\n查询: {test_query}")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['chapter']}] {r['content'][:50]}... (相似度: {r['similarity']:.3f})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='构建 DeepSeek Embedding 索引')
    parser.add_argument('--input', '-i', type=Path, default=Path('data/processed_v2/paragraphs_v2.json'),
                        help='段落 JSON 文件路径')
    parser.add_argument('--output', '-o', type=Path, default=Path('data/embedding_index'),
                        help='索引输出目录')
    parser.add_argument('--api-key', type=str, default=None,
                        help='DeepSeek API Key（默认从环境变量 DEEPSEEK_API_KEY 读取）')
    parser.add_argument('--max', '-m', type=int, default=None,
                        help='最大处理段落数（测试用）')
    
    args = parser.parse_args()
    
    # 检查 API Key
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 需要提供 DeepSeek API Key")
        print("   方式1: 设置环境变量 DEEPSEEK_API_KEY")
        print("   方式2: 使用 --api-key 参数")
        sys.exit(1)
    
    # 检查输入文件
    if not args.input.exists():
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 构建索引
    build_embedding_index(
        paragraphs_file=args.input,
        output_dir=args.output,
        api_key=api_key,
        max_paragraphs=args.max
    )
