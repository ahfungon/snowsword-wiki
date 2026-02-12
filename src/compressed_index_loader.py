#!/usr/bin/env python3
"""
压缩语义索引加载器
支持从压缩文件自动解压加载
"""

import json
import gzip
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_compressed_index(data_dir: Path):
    """
    加载压缩的语义索引
    
    优先顺序：
    1. 尝试加载已解压的原始文件
    2. 尝试加载压缩文件（自动解压）
    
    Returns:
        (embeddings, paragraphs, metadata) 或 None
    """
    index_dir = data_dir / "zhipu_index"
    
    # 方案1: 检查是否已有解压后的文件
    if (index_dir / "embeddings.npy").exists() and (index_dir / "metadata.json").exists():
        logger.info("📂 发现已解压的索引文件，直接加载")
        try:
            embeddings = np.load(index_dir / "embeddings.npy")
            with open(index_dir / "metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return embeddings, metadata['paragraphs'], metadata['metadata']
        except Exception as e:
            logger.warning(f"⚠️ 加载已解压文件失败: {e}")
    
    # 方案2: 加载压缩文件
    compressed_dir = data_dir
    emb_file = compressed_dir / "zhipu_index_embeddings.npz"
    texts_file = compressed_dir / "zhipu_index_texts.json.gz"
    meta_file = compressed_dir / "zhipu_index_meta.json.gz"
    
    if not emb_file.exists():
        logger.error(f"❌ 找不到压缩索引文件: {emb_file}")
        return None
    
    logger.info("📦 加载压缩索引文件...")
    
    try:
        # 加载 embeddings
        logger.info("  📊 加载 embeddings...")
        with np.load(emb_file) as data:
            embeddings = data['embeddings']
        logger.info(f"  ✅ embeddings: {embeddings.shape}")
        
        # 加载 paragraphs
        logger.info("  📝 加载 paragraphs...")
        if texts_file.exists():
            with gzip.open(texts_file, 'rt', encoding='utf-8') as f:
                paragraphs = json.load(f)
        else:
            paragraphs = []
            logger.warning("⚠️ 找不到 texts 文件，paragraphs 为空")
        
        # 加载 metadata
        logger.info("  📋 加载 metadata...")
        if meta_file.exists():
            with gzip.open(meta_file, 'rt', encoding='utf-8') as f:
                metadata_list = json.load(f)
        else:
            metadata_list = [{'idx': i} for i in range(len(paragraphs))]
        
        # 构建完整 metadata
        full_metadata = {
            'paragraphs': paragraphs,
            'metadata': metadata_list
        }
        
        logger.info(f"✅ 压缩索引加载完成: {len(paragraphs)} 段落")
        
        # 可选：解压保存到本地（下次加载更快）
        try:
            index_dir.mkdir(exist_ok=True, parents=True)
            np.save(index_dir / "embeddings.npy", embeddings)
            with open(index_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(full_metadata, f, ensure_ascii=False)
            logger.info(f"💾 已解压保存到: {index_dir}")
        except Exception as e:
            logger.warning(f"⚠️ 解压保存失败（不影响使用）: {e}")
        
        return embeddings, paragraphs, metadata_list
        
    except Exception as e:
        logger.error(f"❌ 加载压缩索引失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    result = load_compressed_index(Path("data"))
    if result:
        embeddings, paragraphs, metadata = result
        print(f"\n✅ 加载成功!")
        print(f"  Embeddings: {embeddings.shape}")
        print(f"  Paragraphs: {len(paragraphs)}")
        print(f"  Metadata: {len(metadata)}")
        print(f"\n  第一段示例: {paragraphs[0][:100]}...")
    else:
        print("\n❌ 加载失败")
