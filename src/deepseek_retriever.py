#!/usr/bin/env python3
"""
DeepSeek Embedding 语义检索器
使用 DeepSeek Embedding API 进行向量语义检索
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekEmbeddingRetriever:
    """
    DeepSeek Embedding 语义检索器
    - 使用 DeepSeek Embedding API 编码文本
    - 向量相似度检索
    - 语义理解优于 TF-IDF
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供 DeepSeek API Key")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-embedding"  # DeepSeek Embedding 模型
        
        self.embeddings = None
        self.paragraphs = []
        self.metadata = []
        self.dimension = None
    
    def _get_embedding(self, texts: List[str]) -> List[List[float]]:
        """调用 DeepSeek Embedding API"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"❌ Embedding API 错误: {e}")
            raise
    
    def _get_embedding_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """批量获取 Embedding（带分批处理）"""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.info(f"🔄 编码批次 {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} ({len(batch)} 条)")
            embeddings = self._get_embedding(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings
    
    def build_index(self, paragraphs: List[Dict], output_dir: Path):
        """构建向量索引"""
        logger.info(f"🔨 构建 DeepSeek Embedding 索引，共 {len(paragraphs)} 个段落")
        
        # 保存段落数据
        self.paragraphs = paragraphs
        self.metadata = [
            {
                'idx': i,
                'chapter': p.get('chapter', ''),
                'chapter_idx': p.get('chapter_idx', 0),
                'paragraph_idx': p.get('paragraph_idx', 0),
            }
            for i, p in enumerate(paragraphs)
        ]
        
        # 提取文本
        texts = [p['content'] for p in paragraphs]
        
        # 获取 Embedding（分批处理）
        logger.info("🔄 调用 DeepSeek Embedding API...")
        embeddings_list = self._get_embedding_batch(texts)
        self.embeddings = np.array(embeddings_list)
        self.dimension = self.embeddings.shape[1]
        
        logger.info(f"✅ 索引构建完成: {self.embeddings.shape}")
        
        # 保存
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # 保存向量
        np.save(output_dir / 'embeddings.npy', self.embeddings)
        
        # 保存元数据
        with open(output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump({
                'paragraphs': texts,
                'metadata': self.metadata,
                'dimension': self.dimension,
                'model': self.model
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 索引已保存: {output_dir}")
    
    def load_index(self, index_dir: Path):
        """加载索引"""
        logger.info(f"📂 加载 DeepSeek Embedding 索引: {index_dir}")
        
        # 加载向量
        self.embeddings = np.load(index_dir / 'embeddings.npy')
        self.dimension = self.embeddings.shape[1]
        
        # 加载元数据
        with open(index_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.paragraphs = data['paragraphs']
            self.metadata = data['metadata']
            saved_model = data.get('model', 'unknown')
        
        logger.info(f"✅ 索引加载完成: {self.embeddings.shape}, 模型: {saved_model}")
    
    def _cosine_similarity(self, query_vec: np.ndarray) -> np.ndarray:
        """计算余弦相似度"""
        # 归一化
        query_vec = query_vec / np.linalg.norm(query_vec)
        embeddings_norm = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        
        # 计算相似度
        similarities = np.dot(embeddings_norm, query_vec)
        return similarities
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义检索"""
        if self.embeddings is None:
            logger.error("❌ 索引未加载")
            return []
        
        # 编码查询
        logger.info(f"🔍 编码查询: {query[:50]}...")
        query_embedding = self._get_embedding([query])[0]
        query_vec = np.array(query_embedding)
        
        # 计算相似度
        similarities = self._cosine_similarity(query_vec)
        
        # 取 top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 组装结果
        results = []
        for idx in top_indices:
            results.append({
                'idx': int(idx),
                'similarity': float(similarities[idx]),
                'content': self.paragraphs[idx],
                **self.metadata[idx]
            })
        
        return results
    
    def hybrid_search(self, query: str, top_k: int = 5, alpha: float = 0.7) -> List[Dict]:
        """混合检索：语义 + 关键词"""
        import jieba
        
        # 语义分数
        query_embedding = self._get_embedding([query])[0]
        query_vec = np.array(query_embedding)
        semantic_scores = self._cosine_similarity(query_vec)
        
        # 关键词分数
        keywords = set(jieba.cut(query))
        keyword_scores = np.zeros(len(self.paragraphs))
        
        for i, content in enumerate(self.paragraphs):
            score = sum(1 for kw in keywords if kw in content)
            keyword_scores[i] = score / max(len(keywords), 1)
        
        # 归一化关键词分数
        if keyword_scores.max() > 0:
            keyword_scores = keyword_scores / keyword_scores.max()
        
        # 融合（语义权重 alpha，关键词权重 1-alpha）
        combined_scores = alpha * semantic_scores + (1 - alpha) * keyword_scores
        
        # 取 top-k
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'idx': int(idx),
                'similarity': float(combined_scores[idx]),
                'semantic_score': float(semantic_scores[idx]),
                'keyword_score': float(keyword_scores[idx]),
                'content': self.paragraphs[idx],
                **self.metadata[idx]
            })
        
        return results


if __name__ == "__main__":
    print("🧪 测试 DeepSeek Embedding 检索器")
    print("="*60)
    
    # 测试数据
    test_paragraphs = [
        {'content': '徐凤年为母报仇，在太安城外斩杀韩貂寺', 'chapter': '第100章'},
        {'content': '姜泥和徐凤年青梅竹马，最终成为北凉王妃', 'chapter': '第200章'},
        {'content': '李淳罡传授徐凤年两袖青蛇，剑道大成', 'chapter': '第50章'},
        {'content': '王仙芝自称天下第二，镇守武帝城一甲子', 'chapter': '第150章'},
        {'content': '徐骁人屠之名威震天下，守护北凉三十年', 'chapter': '第10章'},
    ]
    
    # 创建检索器
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️ 请设置 DEEPSEEK_API_KEY 环境变量")
        exit(1)
    
    retriever = DeepSeekEmbeddingRetriever(api_key=api_key)
    
    # 构建索引
    retriever.build_index(test_paragraphs, Path("test_index_deepseek"))
    
    # 测试查询
    queries = [
        "徐凤年为什么要杀韩貂寺？",
        "姜泥和徐凤年的关系？",
        "谁教徐凤年剑法？",
    ]
    
    for query in queries:
        print(f"\n🔍 查询: {query}")
        results = retriever.search(query, top_k=2)
        for r in results:
            print(f"   [{r['idx']}] {r['content'][:40]}... (相似度: {r['similarity']:.3f})")
