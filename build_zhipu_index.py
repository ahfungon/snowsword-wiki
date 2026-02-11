#!/usr/bin/env python3
"""
构建智谱 Embedding 语义索引
用于替换原有的 TF-IDF 索引
"""

import os
import sys
import json
from pathlib import Path
from tqdm import tqdm

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from zhipu_retriever import ZhipuEmbeddingRetriever


def build_semantic_index(
    paragraphs_file: Path,
    output_dir: Path,
    zhipu_api_key: str = None,
    batch_size: int = 8,
    max_paragraphs: int = None
):
    """
    构建语义索引
    
    Args:
        paragraphs_file: 段落文件路径 (paragraphs_v2.json)
        output_dir: 索引输出目录
        zhipu_api_key: 智谱 API Key
        batch_size: 每批处理的段落数（智谱限制每批最多8条）
        max_paragraphs: 最大处理段落数（用于测试，None表示处理全部）
    """
    # 加载段落
    print(f"📂 加载段落文件: {paragraphs_file}")
    with open(paragraphs_file, 'r', encoding='utf-8') as f:
        all_paragraphs = json.load(f)
    
    if max_paragraphs:
        all_paragraphs = all_paragraphs[:max_paragraphs]
    
    print(f"📊 共 {len(all_paragraphs)} 个段落")
    
    # 创建检索器
    api_key = zhipu_api_key or os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise ValueError("请提供智谱 API Key (ZHIPU_API_KEY)")
    
    retriever = ZhipuEmbeddingRetriever(api_key=api_key, model="embedding-2")
    
    # 构建索引
    print(f"🔨 开始构建索引...")
    retriever.build_index(all_paragraphs, output_dir)
    
    print(f"✅ 索引构建完成！保存至: {output_dir}")
    print(f"   - 向量文件: embeddings.npy")
    print(f"   - 元数据: metadata.json")
    print(f"   - 维度: {retriever.dimension}")
    
    return retriever


def test_index(index_dir: Path, zhipu_api_key: str = None):
    """测试索引"""
    print("\n🧪 测试索引...")
    
    api_key = zhipu_api_key or os.getenv("ZHIPU_API_KEY")
    retriever = ZhipuEmbeddingRetriever(api_key=api_key)
    retriever.load_index(index_dir)
    
    test_queries = [
        "徐凤年为什么要杀韩貂寺？",
        "姜泥和徐凤年是什么关系？",
        "李淳罡教了徐凤年什么？",
        "王仙芝为什么自称天下第二？",
        "徐骁为什么叫人屠？",
    ]
    
    for query in test_queries:
        print(f"\n🔍 {query}")
        results = retriever.search(query, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['chapter']}] {r['content'][:60]}... (相似度: {r['similarity']:.3f})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="构建智谱 Embedding 语义索引")
    parser.add_argument("--data", type=Path, default=Path("data/processed_v2/paragraphs_v2.json"),
                       help="段落文件路径")
    parser.add_argument("--output", type=Path, default=Path("data/zhipu_index"),
                       help="索引输出目录")
    parser.add_argument("--api-key", type=str, default=None,
                       help="智谱 API Key（默认从环境变量 ZHIPU_API_KEY 读取）")
    parser.add_argument("--max-paragraphs", type=int, default=None,
                       help="最大处理段落数（用于测试）")
    parser.add_argument("--test", action="store_true",
                       help="仅测试已有索引")
    
    args = parser.parse_args()
    
    # 设置 API Key
    if args.api_key:
        os.environ["ZHIPU_API_KEY"] = args.api_key
    
    if args.test:
        # 仅测试
        test_index(args.output)
    else:
        # 构建索引
        build_semantic_index(
            paragraphs_file=args.data,
            output_dir=args.output,
            zhipu_api_key=args.api_key,
            max_paragraphs=args.max_paragraphs
        )
        
        # 测试
        test_index(args.output)
