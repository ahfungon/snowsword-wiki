"""
文本处理模块：将小说文本分块并建立索引
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
import pickle

class TextIndexer:
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        """
        初始化索引器
        
        Args:
            chunk_size: 每个文本块的大小（字符数）
            overlap: 相邻块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks: List[Dict] = []
        
    def extract_chapters(self, text: str) -> List[Tuple[str, str]]:
        """
        提取章节标题和内容
        
        Returns:
            List of (chapter_title, chapter_content)
        """
        # 匹配章节标题模式（如：第一章 小二上酒）
        chapter_pattern = r'(第[一二三四五六七八九十百千零\d]+章\s+[^\n]+)'
        
        # 分割文本
        parts = re.split(f'({chapter_pattern})', text)
        
        chapters = []
        current_title = "序言"
        current_content = []
        
        for part in parts:
            if not part.strip():
                continue
                
            # 检查是否是章节标题
            if re.match(chapter_pattern, part.strip()):
                # 保存前一章节
                if current_content:
                    chapters.append((
                        current_title,
                        '\n'.join(current_content)
                    ))
                current_title = part.strip()
                current_content = []
            else:
                current_content.append(part)
        
        # 保存最后一章
        if current_content:
            chapters.append((
                current_title,
                '\n'.join(current_content)
            ))
            
        return chapters
    
    def create_chunks(self, text: str) -> List[Dict]:
        """
        将文本分割成带元数据的块
        """
        print("正在提取章节...")
        chapters = self.extract_chapters(text)
        print(f"找到 {len(chapters)} 个章节")
        
        chunks = []
        
        for chapter_idx, (chapter_title, chapter_content) in enumerate(chapters):
            # 清理内容
            content = chapter_content.strip()
            if not content:
                continue
                
            # 按句子分割（保持上下文）
            sentences = re.split(r'([。！？；\n]+)', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # 构建段落
            current_chunk = []
            current_size = 0
            
            for i in range(0, len(sentences), 2):  # 跳过标点符号
                sentence = sentences[i] if i < len(sentences) else ""
                
                if not sentence:
                    continue
                    
                # 如果当前块加上新句子超过限制，保存当前块
                if current_size + len(sentence) > self.chunk_size and current_chunk:
                    chunk_text = ''.join(current_chunk)
                    chunks.append({
                        'id': f"chunk_{len(chunks)}",
                        'chapter': chapter_title,
                        'content': chunk_text,
                        'char_count': len(chunk_text),
                        'chapter_idx': chapter_idx
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
                    'id': f"chunk_{len(chunks)}",
                    'chapter': chapter_title,
                    'content': chunk_text,
                    'char_count': len(chunk_text),
                    'chapter_idx': chapter_idx
                })
        
        print(f"共创建 {len(chunks)} 个文本块")
        return chunks
    
    def build_index(self, text_path: str, output_dir: str = "data"):
        """
        构建索引并保存
        """
        print(f"读取文本文件: {text_path}")
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"文本总长度: {len(text)} 字符")
        
        # 创建块
        self.chunks = self.create_chunks(text)
        
        # 保存为 JSON（方便查看）
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        json_path = output_path / "chunks.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        
        print(f"索引已保存到: {json_path}")
        
        # 创建简单关键词索引
        keyword_index = self._build_keyword_index()
        index_path = output_path / "keyword_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(keyword_index, f, ensure_ascii=False)
        
        print(f"关键词索引已保存到: {index_path}")
        
        return self.chunks
    
    def _build_keyword_index(self) -> Dict:
        """
        构建简单关键词索引（用于快速检索）
        """
        from collections import defaultdict
        import jieba
        
        index = defaultdict(list)
        
        for chunk in self.chunks:
            # 提取关键词（使用 jieba 分词）
            words = jieba.lcut(chunk['content'])
            
            # 过滤短词和停用词
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in stop_words:
                    index[word].append(chunk['id'])
        
        # 去重
        for word in index:
            index[word] = list(set(index[word]))
        
        return dict(index)

if __name__ == "__main__":
    indexer = TextIndexer(chunk_size=800, overlap=100)
    indexer.build_index("data/雪中悍刀行.txt")
