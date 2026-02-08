#!/usr/bin/env python3
"""
构建所有增强索引
"""

import sys
from pathlib import Path

sys.path.append('.')

from src.indexer import TextIndexer
from src.knowledge_graph import KnowledgeGraph
from src.chapter_summarizer import ChapterSummarizer
import json
import gzip


def build_all():
    """构建所有索引"""
    data_dir = Path("data")
    
    # 1. 检查小说文本
    text_file = data_dir / "雪中悍刀行.txt"
    if not text_file.exists():
        print("❌ 找不到小说文本文件")
        return
    
    print("📖 加载小说文本...")
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"   文本长度: {len(text):,} 字符")
    
    # 2. 构建文本块索引
    chunks_path = data_dir / "chunks.json"
    if not chunks_path.exists():
        print("\n📝 构建文本块索引...")
        indexer = TextIndexer(chunk_size=800, overlap=100)
        chunks = indexer.create_chunks(text)
        
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False)
        print(f"   ✓ 生成了 {len(chunks)} 个文本块")
    else:
        print(f"\n📦 文本块索引已存在")
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
    
    # 3. 压缩分块（30MB每份）
    print("\n🗜️  压缩分块文件...")
    import subprocess
    
    # 清理旧文件
    for f in data_dir.glob("chunks_small_*.gz"):
        f.unlink()
    
    # 分割
    subprocess.run(f"cd {data_dir} && split -b 30m chunks.json chunks_small_", shell=True)
    
    # 压缩
    for part in data_dir.glob("chunks_small_*"):
        if not str(part).endswith('.gz'):
            subprocess.run(f"gzip -9 {part}", shell=True)
            print(f"   ✓ {part.name}.gz")
    
    # 4. 构建知识图谱
    kg_path = data_dir / "knowledge_graph.json"
    if not kg_path.exists():
        print("\n🕸️  构建知识图谱...")
        graph = KnowledgeGraph()
        graph.build_from_text(text[:100000])  # 先用前10万字
        graph.save(kg_path)
    else:
        print(f"\n📦 知识图谱已存在")
    
    # 5. 构建章节摘要
    summary_path = data_dir / "chapter_summaries.json"
    if not summary_path.exists():
        print("\n📚 构建章节摘要...")
        summarizer = ChapterSummarizer()
        chapters = summarizer.parse_chapters(text)
        summaries = summarizer.generate_all_summaries()
        summarizer.save(summaries, summary_path)
    else:
        print(f"\n📦 章节摘要已存在")
    
    print("\n" + "="*60)
    print("✅ 所有索引构建完成！")
    print("="*60)


if __name__ == "__main__":
    build_all()
