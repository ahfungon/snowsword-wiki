#!/usr/bin/env python3
"""
本地构建语义索引（允许禁用 SSL 验证）
用于 Mac 本地开发环境遇到 SSL 证书问题时
"""

import os
import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from zhipu_retriever import ZhipuEmbeddingRetriever, get_zhipu_embedding


def build_semantic_index_local(
    paragraphs_file: Path,
    output_dir: Path,
    zhipu_api_key: str = None,
    max_paragraphs: int = None,
    verify_ssl: bool = False  # Mac 本地可设为 False 跳过 SSL 验证
):
    """
    构建语义索引（本地版本）
    
    Args:
        verify_ssl: 是否验证 SSL 证书。Mac 本地遇到 SSL 问题可设为 False
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
    
    print(f"🔨 开始构建索引...")
    print(f"   SSL 验证: {'开启' if verify_ssl else '关闭（仅本地测试）'}")
    
    retriever = ZhipuEmbeddingRetriever(api_key=api_key, model="embedding-2")
    
    # 手动构建索引（支持禁用 SSL）
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 保存段落数据
    retriever.paragraphs = [p['content'] for p in all_paragraphs]
    retriever.metadata = [
        {
            'idx': i,
            'chapter': p.get('chapter', ''),
            'chapter_idx': p.get('chapter_idx', 0),
            'paragraph_idx': p.get('paragraph_idx', 0),
        }
        for i, p in enumerate(all_paragraphs)
    ]
    
    # 提取文本
    texts = retriever.paragraphs
    
    # 获取 Embedding（分批处理，支持禁用 SSL）
    print("🔄 调用智谱 Embedding API...")
    import numpy as np
    
    batch_size = 8
    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_num = i // batch_size + 1
        print(f"   批次 {batch_num}/{total_batches} ({len(batch)} 条)...", end=" ")
        
        try:
            embeddings = get_zhipu_embedding(batch, api_key, retriever.model, verify_ssl=verify_ssl)
            all_embeddings.extend(embeddings)
            print("✅")
        except Exception as e:
            print(f"❌ 失败: {e}")
            raise
    
    retriever.embeddings = np.array(all_embeddings)
    retriever.dimension = retriever.embeddings.shape[1]
    
    print(f"✅ 索引构建完成: {retriever.embeddings.shape}")
    
    # 保存
    print(f"💾 保存索引到: {output_dir}")
    
    # 保存向量
    np.save(output_dir / 'embeddings.npy', retriever.embeddings)
    
    # 保存元数据
    with open(output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump({
            'paragraphs': texts,
            'metadata': retriever.metadata,
            'dimension': retriever.dimension,
            'model': retriever.model
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 索引保存完成！")
    print(f"   - 向量文件: {output_dir / 'embeddings.npy'}")
    print(f"   - 元数据: {output_dir / 'metadata.json'}")
    print(f"   - 维度: {retriever.dimension}")
    
    return retriever


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="本地构建智谱 Embedding 语义索引")
    parser.add_argument("--data", type=Path, default=Path("data/processed_v2/paragraphs_v2.json"),
                       help="段落文件路径")
    parser.add_argument("--output", type=Path, default=Path("data/zhipu_index"),
                       help="索引输出目录")
    parser.add_argument("--api-key", type=str, default=None,
                       help="智谱 API Key（默认从环境变量 ZHIPU_API_KEY 读取）")
    parser.add_argument("--max-paragraphs", type=int, default=None,
                       help="最大处理段落数（用于测试）")
    parser.add_argument("--verify-ssl", action="store_true",
                       help="启用 SSL 验证（默认关闭，解决 Mac 证书问题）")
    
    args = parser.parse_args()
    
    # 设置 API Key
    if args.api_key:
        os.environ["ZHIPU_API_KEY"] = args.api_key
    
    # 构建索引
    build_semantic_index_local(
        paragraphs_file=args.data,
        output_dir=args.output,
        zhipu_api_key=args.api_key,
        max_paragraphs=args.max_paragraphs,
        verify_ssl=args.verify_ssl  # 默认 False，解决 Mac SSL 问题
    )
