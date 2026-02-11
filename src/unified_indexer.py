"""
统一索引模块 - 整合关键词索引和向量索引
"""

import re
import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np
from openai import OpenAI


class UnifiedIndexer:
    """统一索引器：支持关键词索引和向量索引"""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100, api_key: str = None):
        """
        初始化索引器
        
        Args:
            chunk_size: 每个文本块的大小（字符数）
            overlap: 相邻块之间的重叠字符数
            api_key: DeepSeek/OpenAI API Key（用于向量索引）
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks: List[Dict] = []
        self.keyword_index: Dict = {}
        
        # 向量索引相关
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        else:
            self.client = None
    
    def extract_chapters(self, text: str) -> List[Tuple[str, str]]:
        """提取章节标题和内容"""
        chapter_pattern = r'(第[一二三四五六七八九十百千零\d]+章\s+[^\n]+)'
        parts = re.split(f'({chapter_pattern})', text)
        
        chapters = []
        current_title = "序言"
        current_content = []
        
        for part in parts:
            if not part.strip():
                continue
            
            if re.match(chapter_pattern, part.strip()):
                if current_content:
                    chapters.append((current_title, '\n'.join(current_content)))
                current_title = part.strip()
                current_content = []
            else:
                current_content.append(part)
        
        if current_content:
            chapters.append((current_title, '\n'.join(current_content)))
        
        return chapters
    
    def create_chunks(self, text: str) -> List[Dict]:
        """将文本分割成带元数据的块"""
        print("正在提取章节...")
        chapters = self.extract_chapters(text)
        print(f"找到 {len(chapters)} 个章节")
        
        chunks = []
        
        for chapter_idx, (chapter_title, chapter_content) in enumerate(chapters):
            content = chapter_content.strip()
            if not content:
                continue
            
            sentences = re.split(r'([。！？；\n]+)', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            current_chunk = []
            current_size = 0
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i] if i < len(sentences) else ""
                
                if not sentence:
                    continue
                
                if current_size + len(sentence) > self.chunk_size and current_chunk:
                    chunk_text = ''.join(current_chunk)
                    chunks.append({
                        'id': f"chunk_{len(chunks)}",
                        'chapter': chapter_title,
                        'content': chunk_text,
                        'char_count': len(chunk_text),
                        'chapter_idx': chapter_idx
                    })
                    
                    overlap_text = ''.join(current_chunk[-2:]) if len(current_chunk) >= 2 else chunk_text[-self.overlap:]
                    current_chunk = [overlap_text, sentence]
                    current_size = len(overlap_text) + len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_size += len(sentence)
            
            if current_chunk:
                chunk_text = ''.join(current_chunk)
                chunks.append({
                    'id': f"chunk_{len(chunks)}",
                    'chapter': chapter_title,
                    'content': chunk_text,
                    'char_count': len(chunk_text),
                    'chapter_idx': chapter_idx
                })
        
        print(f"共创建 {len(chunks)} 个文本块")
        return chunks
    
    def _build_keyword_index(self) -> Dict:
        """构建简单关键词索引"""
        try:
            import jieba
        except ImportError:
            print("警告：未安装 jieba，关键词索引功能受限")
            return {}
        
        index = defaultdict(list)
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        for chunk in self.chunks:
            words = jieba.lcut(chunk['content'])
            
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in stop_words:
                    index[word].append(chunk['id'])
        
        for word in index:
            index[word] = list(set(index[word]))
        
        return dict(index)
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量嵌入（简化版）"""
        words = set(text[:200])
        vector = []
        for char in words:
            vector.append(ord(char) % 100 / 100.0)
        
        while len(vector) < 128:
            vector.append(0.0)
        return vector[:128]
    
    def _create_vector_index(self) -> List[Dict]:
        """为所有文本块生成向量索引"""
        print(f"🧮 正在为 {len(self.chunks)} 个文本块生成向量嵌入...")
        
        indexed_chunks = []
        for i, chunk in enumerate(self.chunks):
            if (i + 1) % 1000 == 0:
                print(f"  进度: {i+1}/{len(self.chunks)}")
            
            vector = self._get_embedding(chunk['content'])
            indexed_chunks.append({**chunk, 'embedding': vector})
        
        print(f"✅ 向量索引生成完成")
        return indexed_chunks
    
    def build_index(self, text_path: str, output_dir: str = "data", 
                    build_keyword: bool = True, build_vector: bool = True):
        """
        构建完整索引
        
        Args:
            text_path: 文本文件路径
            output_dir: 输出目录
            build_keyword: 是否构建关键词索引
            build_vector: 是否构建向量索引
        """
        print(f"📖 读取文本文件: {text_path}")
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"📝 文本总长度: {len(text)} 字符")
        
        # 创建文本块
        self.chunks = self.create_chunks(text)
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存基础 chunks
        json_path = output_path / "chunks.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"💾 文本块已保存: {json_path}")
        
        # 构建关键词索引
        if build_keyword:
            print("🔍 构建关键词索引...")
            self.keyword_index = self._build_keyword_index()
            keyword_path = output_path / "keyword_index.json"
            with open(keyword_path, 'w', encoding='utf-8') as f:
                json.dump(self.keyword_index, f, ensure_ascii=False)
            print(f"💾 关键词索引已保存: {keyword_path}")
        
        # 构建向量索引
        if build_vector:
            indexed_chunks = self._create_vector_index()
            vector_path = output_path / "chunks_vector.json"
            with open(vector_path, 'w', encoding='utf-8') as f:
                json.dump(indexed_chunks, f, ensure_ascii=False)
            print(f"💾 向量索引已保存: {vector_path}")
        
        return self.chunks
    
    def load_index(self, index_dir: str = "data"):
        """加载已有索引"""
        index_path = Path(index_dir)
        
        # 加载 chunks
        chunks_path = index_path / "chunks.json"
        if chunks_path.exists():
            with open(chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            print(f"✅ 已加载 {len(self.chunks)} 个文本块")
        
        # 加载关键词索引
        keyword_path = index_path / "keyword_index.json"
        if keyword_path.exists():
            with open(keyword_path, 'r', encoding='utf-8') as f:
                self.keyword_index = json.load(f)
            print(f"✅ 已加载关键词索引")


# 保持向后兼容的别名
TextIndexer = UnifiedIndexer
VectorIndexer = UnifiedIndexer

if __name__ == "__main__":
    indexer = UnifiedIndexer(chunk_size=800, overlap=100)
    indexer.build_index("data/雪中悍刀行.txt")