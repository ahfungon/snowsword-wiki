#!/usr/bin/env python3
"""
语义检索器 V2 - 基于 BGE 中文 Embedding
实现真正的语义理解检索
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticRetriever:
    """
    语义检索器
    - 使用 BGE 中文 Embedding
    - 支持 ChromaDB 向量存储
    - 混合检索（语义 + 关键词）
    """
    
    def __init__(self, model_name: str = "BAAI/bge-base-zh", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.collection = None
        self._load_model()
    
    def _load_model(self):
        """加载 Embedding 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"📥 加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("✅ 模型加载成功")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """编码文本为向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        # BGE 模型需要在文本前加指令
        instruction = "为这个句子生成表示以用于检索相关文章："
        texts_with_instruction = [f"{instruction}{t}" for t in texts]
        
        embeddings = self.model.encode(
            texts_with_instruction,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings
    
    def cosine_similarity(self, query_emb: np.ndarray, doc_emb: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(query_emb, doc_emb)
    
    def build_index(self, chunks: List[Dict], index_path: Path = None):
        """
        构建向量索引
        chunks: [{'id': ..., 'content': ..., 'chapter': ...}, ...]
        """
        logger.info(f"🔨 构建向量索引，共 {len(chunks)} 个文本块")
        
        # 提取文本内容
        texts = [chunk['content'] for chunk in chunks]
        ids = [str(chunk['id']) for chunk in chunks]
        metadatas = [
            {
                'chapter': chunk.get('chapter', ''),
                'chapter_idx': chunk.get('chapter_idx', 0)
            }
            for chunk in chunks
        ]
        
        # 编码
        logger.info("🔄 编码文本...")
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # 使用 ChromaDB 存储
        try:
            import chromadb
            client = chromadb.Client()
            
            # 创建或获取集合
            self.collection = client.create_collection(
                name="snowsword",
                metadata={"hnsw:space": "cosine"}
            )
            
            # 分批添加（避免内存问题）
            batch_size = 1000
            for i in range(0, len(chunks), batch_size):
                batch_end = min(i + batch_size, len(chunks))
                self.collection.add(
                    embeddings=embeddings[i:batch_end].tolist(),
                    documents=texts[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
                logger.info(f"   已添加: {batch_end}/{len(chunks)}")
            
            logger.info("✅ 向量索引构建完成")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB 错误: {e}")
            # 备用方案：使用 numpy 存储
            self._save_numpy_index(embeddings, ids, metadatas, index_path)
    
    def _save_numpy_index(self, embeddings: np.ndarray, ids: List[str], 
                         metadatas: List[Dict], index_path: Path):
        """备用：使用 numpy 存储索引"""
        if index_path is None:
            index_path = Path("data/semantic_index")
        
        index_path.mkdir(exist_ok=True, parents=True)
        
        np.save(index_path / "embeddings.npy", embeddings)
        with open(index_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump({
                'ids': ids,
                'metadatas': metadatas
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Numpy 索引已保存: {index_path}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        语义检索
        """
        if self.collection is None:
            logger.error("❌ 索引未加载")
            return []
        
        # 编码查询
        query_embedding = self.encode([query])
        
        # 检索
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return formatted_results
    
    def hybrid_search(self, query: str, keyword_index: Dict, top_k: int = 5) -> List[Dict]:
        """
        混合检索：语义 + 关键词
        """
        # 语义检索
        semantic_results = self.search(query, top_k=top_k * 2)
        
        # 关键词检索（简单实现）
        keywords = set(query.split())
        keyword_scores = {}
        
        for chunk_id, chunk_data in keyword_index.items():
            content = chunk_data.get('content', '')
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                keyword_scores[chunk_id] = score
        
        # 融合排序
        fused_scores = {}
        
        # 语义分数（归一化到0-1）
        for i, result in enumerate(semantic_results):
            fused_scores[result['id']] = fused_scores.get(result['id'], 0) + (1 - i / len(semantic_results)) * 0.6
        
        # 关键词分数
        max_kw_score = max(keyword_scores.values()) if keyword_scores else 1
        for chunk_id, score in keyword_scores.items():
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + (score / max_kw_score) * 0.4
        
        # 排序
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        # 组装结果
        final_results = []
        for chunk_id in sorted_ids[:top_k]:
            # 从语义结果中找
            found = False
            for result in semantic_results:
                if result['id'] == chunk_id:
                    final_results.append(result)
                    found = True
                    break
            
            # 如果不在语义结果中，从关键词索引找
            if not found and chunk_id in keyword_index:
                final_results.append({
                    'id': chunk_id,
                    'content': keyword_index[chunk_id]['content'],
                    'metadata': keyword_index[chunk_id].get('metadata', {}),
                    'distance': 0.5  # 默认中等相关度
                })
        
        return final_results


if __name__ == "__main__":
    # 测试
    print("🧪 测试语义检索器")
    
    # 创建检索器
    retriever = SemanticRetriever()
    
    # 测试数据
    test_chunks = [
        {'id': '1', 'content': '徐凤年为母报仇，斩杀韩貂寺于太安城外', 'chapter': '第100章'},
        {'id': '2', 'content': '姜泥和徐凤年青梅竹马，最终成为北凉王妃', 'chapter': '第200章'},
        {'id': '3', 'content': '李淳罡传授两袖青蛇，徐凤年剑道大成', 'chapter': '第50章'},
    ]
    
    # 构建索引
    retriever.build_index(test_chunks)
    
    # 测试查询
    queries = [
        "徐凤年为什么要杀韩貂寺？",
        "姜泥和徐凤年什么关系？",
    ]
    
    for query in queries:
        print(f"\n🔍 查询: {query}")
        results = retriever.search(query, top_k=2)
        for r in results:
            print(f"   [{r['id']}] {r['content'][:50]}... (相似度: {1-r['distance']:.3f})")
