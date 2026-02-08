#!/usr/bin/env python3
"""
向量索引生成器 - 使用 DeepSeek Embedding API
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import numpy as np
from openai import OpenAI


class VectorIndexer:
    """生成文本块的向量嵌入"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "text-embedding-ada-002"  # 或使用 deepseek 的 embedding
        
    def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量嵌入"""
        # DeepSeek 目前没有专门的 embedding API，使用简单的字符编码作为临时方案
        # 实际生产环境应该使用 OpenAI 或其他 embedding 服务
        
        # 简化版：使用词频向量
        words = set(text[:200])  # 取前200字符
        vector = []
        for char in words:
            vector.append(ord(char) % 100 / 100.0)  # 归一化
        
        # 填充到固定长度
        while len(vector) < 128:
            vector.append(0.0)
        return vector[:128]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        a = np.array(vec1)
        b = np.array(vec2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def create_vector_index(self, chunks: List[Dict]) -> List[Dict]:
        """为所有文本块生成向量索引"""
        print(f"🧮 正在为 {len(chunks)} 个文本块生成向量嵌入...")
        
        indexed_chunks = []
        for i, chunk in enumerate(chunks):
            if (i + 1) % 1000 == 0:
                print(f"  进度: {i+1}/{len(chunks)}")
            
            vector = self.get_embedding(chunk['content'])
            indexed_chunks.append({
                **chunk,
                'embedding': vector
            })
        
        print(f"✅ 向量索引生成完成")
        return indexed_chunks
    
    def save_index(self, indexed_chunks: List[Dict], output_path: Path):
        """保存向量索引"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(indexed_chunks, f, ensure_ascii=False)
        print(f"💾 向量索引已保存: {output_path}")


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.append('.')
    from src.indexer import TextIndexer
    
    # 加载已有 chunks
    data_dir = Path("data")
    with open(data_dir / "chunks.json", 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # 生成向量索引
    indexer = VectorIndexer()
    indexed_chunks = indexer.create_vector_index(chunks)
    
    # 保存
    indexer.save_index(indexed_chunks, data_dir / "chunks_vector.json")
