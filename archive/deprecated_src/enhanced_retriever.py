#!/usr/bin/env python3
"""
增强检索器 - 集成向量检索、知识图谱、章节摘要
"""

import json
import gzip
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import jieba


class EnhancedRetriever:
    """增强版检索器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.chunks = []
        self.chunk_map = {}
        self.vector_index = []
        self.knowledge_graph = None
        self.chapter_summaries = []
        
        # 加载数据
        self._load_data()
    
    def _load_data(self):
        """加载所有数据"""
        print("🔄 正在加载增强索引...")
        
        # 1. 加载文本块（支持压缩文件解压）
        self._load_chunks()
        
        # 2. 加载知识图谱
        self._load_knowledge_graph()
        
        # 3. 加载章节摘要
        self._load_chapter_summaries()
        
        print(f"✅ 索引加载完成")
    
    def _load_chunks(self):
        """加载文本块，支持压缩文件"""
        chunks_path = self.data_dir / "chunks.json"
        
        # 检查压缩文件
        compressed_files = sorted(self.data_dir.glob("chunks_small_*.gz"))
        
        if not chunks_path.exists() and compressed_files:
            print(f"📦 发现 {len(compressed_files)} 个压缩文件，开始解压...")
            self._decompress_and_merge(compressed_files, chunks_path)
        
        if chunks_path.exists():
            print(f"📖 加载文本块...")
            with open(chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            self.chunk_map = {chunk['id']: chunk for chunk in self.chunks}
            print(f"   ✓ 加载了 {len(self.chunks)} 个文本块")
    
    def _decompress_and_merge(self, compressed_files: List[Path], output_path: Path):
        """解压并合并文件"""
        temp_dir = self.data_dir / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        total = len(compressed_files)
        for i, gz_file in enumerate(compressed_files, 1):
            print(f"   [{i}/{total}] 解压 {gz_file.name}...")
            output_file = temp_dir / gz_file.stem
            with gzip.open(gz_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    f_out.write(f_in.read())
        
        # 合并
        print(f"📑 合并 {total} 个文件...")
        split_files = sorted(temp_dir.glob("chunks_small_*"))
        files_str = ' '.join([str(f) for f in split_files])
        cmd = f"cat {files_str} > {output_path}"
        subprocess.run(cmd, shell=True, check=True)
        
        # 清理
        for f in split_files:
            f.unlink()
        temp_dir.rmdir()
        
        print(f"   ✓ 解压合并完成")
    
    def _load_knowledge_graph(self):
        """加载知识图谱"""
        kg_path = self.data_dir / "knowledge_graph.json"
        if kg_path.exists():
            with open(kg_path, 'r', encoding='utf-8') as f:
                self.knowledge_graph = json.load(f)
            print(f"   ✓ 知识图谱: {len(self.knowledge_graph.get('characters', {}))} 个人物")
    
    def _load_chapter_summaries(self):
        """加载章节摘要"""
        summary_path = self.data_dir / "chapter_summaries.json"
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                self.chapter_summaries = json.load(f)
            print(f"   ✓ 章节摘要: {len(self.chapter_summaries)} 章")
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本向量（简化版）"""
        words = set(text[:200])
        vector = [ord(char) % 100 / 100.0 for char in words]
        while len(vector) < 128:
            vector.append(0.0)
        return vector[:128]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        a = np.array(vec1)
        b = np.array(vec2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = jieba.lcut(text)
        # 过滤停用词和短词
        stopwords = {'的', '是', '在', '和', '了', '有', '我', '都', '个', '与', '也', '对', '为', '能', '很', '可以', '就', '不', '会', '要', '没有', '到', '更', '让', '但', '给', '上', '这', '他', '她', '它', '们', '你', '您', '我们', '你们', '他们', '她们', '它们'}
        keywords = [w.strip() for w in words if len(w.strip()) > 1 and w.strip() not in stopwords]
        return keywords
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        多策略检索：
        1. 向量相似度
        2. 关键词匹配
        3. 知识图谱增强
        """
        results = []
        
        # 1. 向量相似度检索
        query_vector = self._get_embedding(query)
        vector_scores = []
        
        for chunk in self.chunks:
            chunk_vector = self._get_embedding(chunk['content'])
            similarity = self._cosine_similarity(query_vector, chunk_vector)
            vector_scores.append((chunk, similarity))
        
        vector_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 2. 关键词匹配
        query_keywords = set(self._extract_keywords(query))
        keyword_scores = []
        
        for chunk in self.chunks:
            chunk_text = chunk['content']
            chunk_keywords = set(self._extract_keywords(chunk_text))
            
            # 计算匹配度
            if query_keywords:
                match_ratio = len(query_keywords & chunk_keywords) / len(query_keywords)
            else:
                match_ratio = 0
            
            keyword_scores.append((chunk, match_ratio))
        
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 3. 知识图谱增强
        # 提取查询中的人物
        mentioned_chars = []
        if self.knowledge_graph:
            for char in self.knowledge_graph.get('characters', {}):
                if char in query:
                    mentioned_chars.append(char)
        
        # 4. 融合排序
        chunk_scores = {}
        
        # 向量分数权重
        for i, (chunk, score) in enumerate(vector_scores[:top_k * 2]):
            chunk_id = chunk['id']
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + score * 0.4
        
        # 关键词分数权重
        for i, (chunk, score) in enumerate(keyword_scores[:top_k * 2]):
            chunk_id = chunk['id']
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + score * 0.4
        
        # 人物匹配加分
        for chunk in self.chunks:
            chunk_id = chunk['id']
            for char in mentioned_chars:
                if char in chunk['content']:
                    chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + 0.2
        
        # 排序并返回 top_k
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
        
        for chunk_id, score in sorted_chunks[:top_k]:
            if chunk_id in self.chunk_map:
                results.append((self.chunk_map[chunk_id], score))
        
        return results
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """获取增强上下文"""
        # 获取检索结果
        results = self.retrieve(query, top_k=top_k)
        
        # 提取查询中的人物
        mentioned_chars = []
        if self.knowledge_graph:
            for char in self.knowledge_graph.get('characters', {}):
                if char in query:
                    mentioned_chars.append(char)
        
        # 构建上下文
        context_parts = []
        
        # 1. 知识图谱信息
        if mentioned_chars and self.knowledge_graph:
            context_parts.append("【人物背景】")
            for char in mentioned_chars:
                info = self.knowledge_graph['characters'].get(char, {})
                if info:
                    identity = info.get('identity', '')
                    faction = info.get('faction', '')
                    context_parts.append(f"{char}：{identity}，所属：{faction}")
            context_parts.append("")
        
        # 2. 原文片段
        context_parts.append("【相关原文】")
        for i, (chunk, score) in enumerate(results, 1):
            context_parts.append(f"片段{i}（相关度：{score:.2f}）：")
            context_parts.append(chunk['content'])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_chapter_summary(self, chapter_title: str) -> Dict:
        """获取章节摘要"""
        for summary in self.chapter_summaries:
            if chapter_title in summary['title']:
                return summary
        return {}


if __name__ == "__main__":
    # 测试
    print("🧪 测试增强检索器...")
    retriever = EnhancedRetriever()
    
    query = "徐凤年和拓跋菩萨的关系"
    print(f"\n🔍 查询: {query}")
    
    results = retriever.retrieve(query, top_k=3)
    print(f"\n检索结果:")
    for chunk, score in results:
        print(f"  [{chunk['chapter']}] 相关度: {score:.2f}")
        print(f"    {chunk['content'][:80]}...")
    
    print(f"\n上下文预览:")
    context = retriever.get_context(query, top_k=2)
    print(context[:500])
