#!/usr/bin/env python3
"""
语义检索器 V2 - 轻量版
使用 FlagEmbedding/BGE 进行语义检索
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticRetrieverV2:
    """
    语义检索器 V2
    - 使用 BGE 中文 Embedding
    - 支持本地向量存储
    """
    
    def __init__(self, model_name: str = "BAAI/bge-base-zh", use_fp16: bool = False):
        self.model_name = model_name
        self.model = None
        self.embeddings = None
        self.metadata = None
        self._load_model(use_fp16)
    
    def _load_model(self, use_fp16: bool = False):
        """加载 Embedding 模型"""
        try:
            # 尝试使用 FlagEmbedding（推荐）
            from FlagEmbedding import FlagModel
            logger.info(f"📥 加载 FlagEmbedding 模型: {self.model_name}")
            self.model = FlagModel(self.model_name, use_fp16=use_fp16)
            self.model_type = 'flag'
            logger.info("✅ FlagEmbedding 模型加载成功")
        except Exception as e1:
            logger.warning(f"⚠️ FlagEmbedding 加载失败: {e1}")
            try:
                # 备用：使用 sentence-transformers
                from sentence_transformers import SentenceTransformer
                logger.info(f"📥 加载 SentenceTransformer: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                self.model_type = 'st'
                logger.info("✅ SentenceTransformer 加载成功")
            except Exception as e2:
                logger.error(f"❌ 模型加载失败: {e2}")
                raise
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """编码文本"""
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model_type == 'flag':
            # FlagEmbedding 编码
            embeddings = self.model.encode(texts)
        else:
            # SentenceTransformer 编码
            embeddings = self.model.encode(texts, show_progress_bar=False)
        
        return embeddings
    
    def build_index(self, paragraphs: List[Dict], output_dir: Path):
        """
        构建向量索引
        paragraphs: [{'content': ..., 'chapter': ..., ...}, ...]
        """
        logger.info(f"🔨 构建向量索引，共 {len(paragraphs)} 个段落")
        
        # 提取文本
        texts = [p['content'] for p in paragraphs]
        
        # 分批编码（避免内存问题）
        batch_size = 500
        all_embeddings = []
        
        logger.info("🔄 编码文本...")
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = self.encode(batch)
            all_embeddings.append(embeddings)
            if (i + batch_size) % 2000 == 0:
                logger.info(f"   已编码: {min(i+batch_size, len(texts))}/{len(texts)}")
        
        # 合并
        all_embeddings = np.vstack(all_embeddings)
        
        # 保存
        output_dir.mkdir(exist_ok=True, parents=True)
        np.save(output_dir / "embeddings.npy", all_embeddings)
        
        # 保存元数据
        metadata = [
            {
                'idx': i,
                'chapter': p.get('chapter', ''),
                'chapter_idx': p.get('chapter_idx', 0),
                'paragraph_idx': p.get('paragraph_idx', 0),
                'content': p['content'],
                'length': p.get('length', 0)
            }
            for i, p in enumerate(paragraphs)
        ]
        
        with open(output_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.embeddings = all_embeddings
        self.metadata = metadata
        
        logger.info(f"✅ 索引构建完成: {output_dir}")
        logger.info(f"   向量维度: {all_embeddings.shape}")
    
    def load_index(self, index_dir: Path):
        """加载索引"""
        logger.info(f"📂 加载索引: {index_dir}")
        
        self.embeddings = np.load(index_dir / "embeddings.npy")
        with open(index_dir / "metadata.json", 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        logger.info(f"✅ 索引加载完成: {self.embeddings.shape}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        语义检索
        """
        if self.embeddings is None:
            logger.error("❌ 索引未加载")
            return []
        
        # 编码查询
        query_emb = self.encode([query])
        
        # 计算相似度（余弦相似度）
        similarities = np.dot(self.embeddings, query_emb.T).squeeze()
        
        # 取 top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 组装结果
        results = []
        for idx in top_indices:
            results.append({
                'idx': int(idx),
                'similarity': float(similarities[idx]),
                **self.metadata[idx]
            })
        
        return results
    
    def hybrid_search(self, query: str, top_k: int = 5, keyword_weight: float = 0.3) -> List[Dict]:
        """
        混合检索：语义 + 关键词
        """
        # 语义分数
        query_emb = self.encode([query])
        semantic_scores = np.dot(self.embeddings, query_emb.T).squeeze()
        
        # 关键词分数
        keywords = set(query.split())
        keyword_scores = np.zeros(len(self.metadata))
        
        for i, meta in enumerate(self.metadata):
            content = meta['content']
            score = sum(1 for kw in keywords if kw in content)
            keyword_scores[i] = score / max(len(keywords), 1)
        
        # 融合
        combined_scores = (1 - keyword_weight) * semantic_scores + keyword_weight * keyword_scores
        
        # 取 top-k
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'idx': int(idx),
                'similarity': float(combined_scores[idx]),
                'semantic_score': float(semantic_scores[idx]),
                'keyword_score': float(keyword_scores[idx]),
                **self.metadata[idx]
            })
        
        return results


if __name__ == "__main__":
    print("🧪 测试语义检索器 V2")
    
    # 测试数据
    test_paragraphs = [
        {'content': '徐凤年为母报仇，在太安城外斩杀韩貂寺', 'chapter': '第100章'},
        {'content': '姜泥和徐凤年从小一起长大，最终成为北凉王妃', 'chapter': '第200章'},
        {'content': '李淳罡传授徐凤年两袖青蛇，剑道大成', 'chapter': '第50章'},
        {'content': '王仙芝自称天下第二，镇守武帝城一甲子', 'chapter': '第150章'},
        {'content': '徐骁人屠之名威震天下，守护北凉三十年', 'chapter': '第10章'},
    ]
    
    # 创建检索器
    retriever = SemanticRetrieverV2()
    
    # 构建索引
    retriever.build_index(test_paragraphs, Path("test_index"))
    
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
