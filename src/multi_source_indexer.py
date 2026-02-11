#!/usr/bin/env python3
"""
多源统一索引模块 - 支持小说原文和解说全集等多源索引
"""

import re
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np


class MultiSourceIndexer:
    """
    多源统一索引器
    - 支持多个文本源（小说原文、解说全集等）
    - 为每个文本块标记来源
    - 统一检索时考虑所有源
    """
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100, api_key: str = None):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks: List[Dict] = []
        self.keyword_index: Dict = {}
        self.sources: Dict[str, str] = {}  # source_id -> source_name
        
        # 向量索引相关
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    
    def extract_sections(self, text: str, source_name: str) -> List[Tuple[str, str]]:
        """
        提取章节或段落
        
        针对不同来源使用不同的提取策略：
        - 小说原文：按章节提取
        - 解说全集：按章节标题提取
        """
        sections = []
        
        if "解说" in source_name or "commentary" in source_name.lower():
            # 解说全集格式：第 X 章：标题 + 内容
            section_pattern = r'(第\s*[0-9]+\s*章：[^\n]+)'
            parts = re.split(f'({section_pattern})', text)
            
            current_title = "前言"
            current_content = []
            
            for part in parts:
                if not part.strip():
                    continue
                
                if re.match(section_pattern, part.strip()):
                    if current_content:
                        sections.append((current_title, '\n'.join(current_content)))
                    current_title = part.strip()
                    current_content = []
                else:
                    current_content.append(part)
            
            if current_content:
                sections.append((current_title, '\n'.join(current_content)))
        else:
            # 小说原文格式：第X章 标题
            chapter_pattern = r'(第[一二三四五六七八九十百千零\d]+章\s+[^\n]+)'
            parts = re.split(f'({chapter_pattern})', text)
            
            current_title = "序言"
            current_content = []
            
            for part in parts:
                if not part.strip():
                    continue
                
                if re.match(chapter_pattern, part.strip()):
                    if current_content:
                        sections.append((current_title, '\n'.join(current_content)))
                    current_title = part.strip()
                    current_content = []
                else:
                    current_content.append(part)
            
            if current_content:
                sections.append((current_title, '\n'.join(current_content)))
        
        return sections
    
    def create_chunks(self, text: str, source_name: str, source_id: str) -> List[Dict]:
        """
        将文本分割成带元数据的块
        
        Args:
            text: 文本内容
            source_name: 来源名称（如"小说原文"、"解说全集"）
            source_id: 来源ID（如"novel"、"commentary"）
        """
        print(f"📖 处理 {source_name}...")
        sections = self.extract_sections(text, source_name)
        print(f"   找到 {len(sections)} 个章节/段落")
        
        chunks = []
        base_chunk_id = len(self.chunks)  # 基于已有chunks数量
        
        for section_idx, (section_title, section_content) in enumerate(sections):
            content = section_content.strip()
            if not content:
                continue
            
            # 按句子分割
            sentences = re.split(r'([。！？；\n]+)', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            current_chunk = []
            current_size = 0
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i] if i < len(sentences) else ""
                
                if not sentence:
                    continue
                
                # 如果超过块大小，保存当前块
                if current_size + len(sentence) > self.chunk_size and current_chunk:
                    chunk_text = ''.join(current_chunk)
                    chunks.append({
                        'id': f"chunk_{base_chunk_id + len(chunks)}",
                        'section': section_title,
                        'content': chunk_text,
                        'char_count': len(chunk_text),
                        'section_idx': section_idx,
                        'source_id': source_id,
                        'source_name': source_name
                    })
                    
                    # 保留重叠部分
                    overlap_text = ''.join(current_chunk[-2:]) if len(current_chunk) >= 2 else chunk_text[-self.overlap:]
                    current_chunk = [overlap_text, sentence]
                    current_size = len(overlap_text) + len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_size += len(sentence)
            
            # 保存最后一个块
            if current_chunk:
                chunk_text = ''.join(current_chunk)
                chunks.append({
                    'id': f"chunk_{base_chunk_id + len(chunks)}",
                    'section': section_title,
                    'content': chunk_text,
                    'char_count': len(chunk_text),
                    'section_idx': section_idx,
                    'source_id': source_id,
                    'source_name': source_name
                })
        
        print(f"   共创建 {len(chunks)} 个文本块")
        return chunks
    
    def add_source(self, text_path: Path, source_name: str, source_id: str):
        """
        添加一个文本源
        
        Args:
            text_path: 文本文件路径
            source_name: 来源名称
            source_id: 来源ID
        """
        print(f"\n📖 加载 {source_name}: {text_path}")
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"   文本长度: {len(text):,} 字符")
        
        # 创建文本块
        chunks = self.create_chunks(text, source_name, source_id)
        self.chunks.extend(chunks)
        self.sources[source_id] = source_name
        
        print(f"   ✅ {source_name} 处理完成，共 {len(chunks)} 个文本块")
    
    def _build_keyword_index(self) -> Dict:
        """构建关键词索引"""
        try:
            import jieba
        except ImportError:
            print("警告：未安装 jieba，关键词索引功能受限")
            return {}
        
        index = defaultdict(list)
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '中', '为', '以', '及', '与', '或', '但', '而', '之', '其', '所', '等', '个', '从', '将', '把', '被', '给', '让', '向', '往', '于', '当', '与', '和', '跟', '同', '给', '为', '为了', '因为', '所以', '因此', '如果', '即使', '虽然', '尽管', '但是', '然而', '可是', '不过', '然后', '接着', '于是', '就', '便', '才', '却', '竟', '难道'}
        
        for chunk in self.chunks:
            words = jieba.lcut(chunk['content'])
            
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in stop_words:
                    index[word].append(chunk['id'])
        
        for word in index:
            index[word] = list(set(index[word]))
        
        return dict(index)
    
    def build_all_indexes(self, output_dir: str = "data", build_keyword: bool = True):
        """
        构建所有索引
        
        Args:
            output_dir: 输出目录
            build_keyword: 是否构建关键词索引
        """
        print(f"\n{'='*60}")
        print("🔧 构建多源索引")
        print(f"{'='*60}")
        
        print(f"\n📊 统计:")
        print(f"   总文本块: {len(self.chunks)}")
        for source_id, source_name in self.sources.items():
            count = sum(1 for c in self.chunks if c['source_id'] == source_id)
            print(f"   - {source_name}: {count} 个文本块")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存所有 chunks
        chunks_path = output_path / "chunks.json"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"\n💾 文本块已保存: {chunks_path}")
        
        # 保存来源信息
        sources_path = output_path / "sources.json"
        with open(sources_path, 'w', encoding='utf-8') as f:
            json.dump(self.sources, f, ensure_ascii=False, indent=2)
        print(f"💾 来源信息已保存: {sources_path}")
        
        # 构建关键词索引
        if build_keyword:
            print("\n🔍 构建关键词索引...")
            self.keyword_index = self._build_keyword_index()
            keyword_path = output_path / "keyword_index.json"
            with open(keyword_path, 'w', encoding='utf-8') as f:
                json.dump(self.keyword_index, f, ensure_ascii=False)
            print(f"💾 关键词索引已保存: {keyword_path}")
        
        print(f"\n{'='*60}")
        print("✅ 多源索引构建完成！")
        print(f"{'='*60}")
    
    def search_by_keyword(self, keyword: str, source_filter: str = None) -> List[Dict]:
        """
        按关键词搜索
        
        Args:
            keyword: 关键词
            source_filter: 来源过滤器（如"novel"、"commentary"）
        """
        if not self.keyword_index:
            return []
        
        chunk_ids = self.keyword_index.get(keyword, [])
        results = []
        
        for chunk_id in chunk_ids:
            chunk = next((c for c in self.chunks if c['id'] == chunk_id), None)
            if chunk:
                if source_filter and chunk['source_id'] != source_filter:
                    continue
                results.append(chunk)
        
        return results
    
    def get_chunks_by_source(self, source_id: str) -> List[Dict]:
        """获取特定来源的所有文本块"""
        return [c for c in self.chunks if c['source_id'] == source_id]


# 保持向后兼容的别名
UnifiedIndexer = MultiSourceIndexer
TextIndexer = MultiSourceIndexer

if __name__ == "__main__":
    # 测试多源索引
    indexer = MultiSourceIndexer(chunk_size=800, overlap=100)
    
    # 添加小说原文
    novel_path = Path("data/雪中悍刀行.txt")
    if novel_path.exists():
        indexer.add_source(novel_path, "小说原文", "novel")
    
    # 添加解说全集
    commentary_path = Path("data/雪中悍刀行_解说全集.txt")
    if commentary_path.exists():
        indexer.add_source(commentary_path, "解说全集", "commentary")
    
    # 构建索引
    indexer.build_all_indexes()