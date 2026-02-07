#!/usr/bin/env python3
"""
轻量语义检索器 - 使用 TF-IDF + 词频
无需下载大模型，快速可用
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LightweightRetriever:
    """
    轻量级检索器
    - TF-IDF 向量化
    - 余弦相似度检索
    - 无需深度学习模型
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._tokenize,
            max_features=10000,  # 限制特征数
            ngram_range=(1, 2),  # 1-2 gram
            min_df=2,  # 至少出现2次
            max_df=0.8  # 最多80%的文档
        )
        self.tfidf_matrix = None
        self.paragraphs = []
        self.metadata = []
    
    def _tokenize(self, text: str) -> List[str]:
        """中文分词"""
        return list(jieba.cut(text))
    
    def build_index(self, paragraphs: List[Dict], output_dir: Path):
        """构建 TF-IDF 索引"""
        logger.info(f"🔨 构建轻量索引，共 {len(paragraphs)} 个段落")
        
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
        
        # 构建 TF-IDF 矩阵
        logger.info("🔄 计算 TF-IDF...")
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        logger.info(f"✅ 索引构建完成: {self.tfidf_matrix.shape}")
        
        # 保存
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # 保存向量化器
        import pickle
        with open(output_dir / 'vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        # 保存 TF-IDF 矩阵
        from scipy.sparse import save_npz
        save_npz(output_dir / 'tfidf_matrix.npz', self.tfidf_matrix)
        
        # 保存元数据
        with open(output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump({
                'paragraphs': texts,
                'metadata': self.metadata
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 索引已保存: {output_dir}")
    
    def load_index(self, index_dir: Path):
        """加载索引"""
        logger.info(f"📂 加载索引: {index_dir}")
        
        import pickle
        from scipy.sparse import load_npz
        
        # 加载向量化器
        with open(index_dir / 'vectorizer.pkl', 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        # 加载 TF-IDF 矩阵
        self.tfidf_matrix = load_npz(index_dir / 'tfidf_matrix.npz')
        
        # 加载元数据
        with open(index_dir / 'metadata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.paragraphs = data['paragraphs']
            self.metadata = data['metadata']
        
        logger.info(f"✅ 索引加载完成: {self.tfidf_matrix.shape}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索"""
        if self.tfidf_matrix is None:
            logger.error("❌ 索引未加载")
            return []
        
        # 编码查询
        query_vec = self.vectorizer.transform([query])
        
        # 计算相似度
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
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
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """混合检索：TF-IDF + 关键词加权"""
        # TF-IDF 分数
        query_vec = self.vectorizer.transform([query])
        tfidf_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # 关键词分数
        keywords = set(jieba.cut(query))
        keyword_scores = np.zeros(len(self.paragraphs))
        
        for i, content in enumerate(self.paragraphs):
            score = sum(1 for kw in keywords if kw in content)
            keyword_scores[i] = score / max(len(keywords), 1)
        
        # 融合（TF-IDF 权重 0.7，关键词 0.3）
        combined_scores = 0.7 * tfidf_scores + 0.3 * keyword_scores
        
        # 取 top-k
        top_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'idx': int(idx),
                'similarity': float(combined_scores[idx]),
                'tfidf_score': float(tfidf_scores[idx]),
                'keyword_score': float(keyword_scores[idx]),
                'content': self.paragraphs[idx],
                **self.metadata[idx]
            })
        
        return results


if __name__ == "__main__":
    print("🧪 测试轻量级检索器")
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
    retriever = LightweightRetriever()
    
    # 构建索引
    retriever.build_index(test_paragraphs, Path("test_index_light"))
    
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
