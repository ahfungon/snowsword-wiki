#!/usr/bin/env python3
"""
构建多源知识库 - 整合小说原文和解说全集
"""

import sys
from pathlib import Path

sys.path.append('.')

from src.multi_source_indexer import MultiSourceIndexer
from src.knowledge_builder import KnowledgeBuilder
import json


def build_multi_source_knowledge():
    """构建多源知识库"""
    data_dir = Path("data")
    
    print("🚀 开始构建多源知识库...")
    print(f"📁 数据目录: {data_dir.absolute()}")
    
    # ========== 1. 检查源文件 ==========
    sources = []
    
    # 小说原文
    novel_path = data_dir / "雪中悍刀行.txt"
    if novel_path.exists():
        sources.append((novel_path, "小说原文", "novel"))
        print(f"✅ 找到小说原文: {novel_path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"⚠️  找不到小说原文: {novel_path}")
    
    # 解说全集
    commentary_path = data_dir / "雪中悍刀行_解说全集.txt"
    if commentary_path.exists():
        sources.append((commentary_path, "解说全集", "commentary"))
        print(f"✅ 找到解说全集: {commentary_path.stat().st_size / 1024:.2f} KB")
    else:
        print(f"⚠️  找不到解说全集: {commentary_path}")
    
    if not sources:
        print("❌ 错误：没有找到任何源文件")
        return 1
    
    # ========== 2. 构建多源索引 ==========
    print(f"\n{'='*60}")
    print("📚 步骤 1: 构建多源文本索引")
    print(f"{'='*60}")
    
    indexer = MultiSourceIndexer(chunk_size=800, overlap=100)
    
    for path, name, source_id in sources:
        try:
            indexer.add_source(path, name, source_id)
        except Exception as e:
            print(f"❌ 处理 {name} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 保存索引
    indexer.build_all_indexes(str(data_dir))
    
    # ========== 3. 构建解说全集的知识库 ==========
    if commentary_path.exists():
        print(f"\n{'='*60}")
        print("📖 步骤 2: 构建解说全集知识库")
        print(f"{'='*60}")
        
        try:
            with open(commentary_path, 'r', encoding='utf-8') as f:
                commentary_text = f.read()
            
            # 使用 KnowledgeBuilder 处理解说全集
            kb = KnowledgeBuilder()
            
            # 解析章节
            print("\n🔍 解析解说全集章节...")
            # 解说全集的章节提取逻辑
            import re
            
            sections = []
            section_pattern = r'第\s*[0-9]+\s*章：[^\n]+'
            parts = re.split(f'({section_pattern})', commentary_text)
            
            current_title = "前言"
            current_content = []
            
            for part in parts:
                if not part.strip():
                    continue
                
                if re.match(section_pattern, part.strip()):
                    if current_content:
                        sections.append({
                            'title': current_title,
                            'content': '\n'.join(current_content),
                            'word_count': len(''.join(current_content))
                        })
                    current_title = part.strip()
                    current_content = []
                else:
                    current_content.append(part)
            
            if current_content:
                sections.append({
                    'title': current_title,
                    'content': '\n'.join(current_content),
                    'word_count': len(''.join(current_content))
                })
            
            print(f"   找到 {len(sections)} 个解说章节")
            
            # 生成章节摘要
            kb.chapters = sections
            summaries = kb.generate_all_summaries()
            kb.save_summaries(data_dir / "commentary_summaries.json")
            
            # 构建专家知识库
            kb.build_expert_knowledge()
            kb.save_knowledge_base(data_dir / "commentary_knowledge.json")
            
            print(f"\n✅ 解说全集知识库构建完成")
            
        except Exception as e:
            print(f"❌ 处理解说全集时出错: {e}")
            import traceback
            traceback.print_exc()
    
    # ========== 4. 生成统计报告 ==========
    print(f"\n{'='*60}")
    print("📊 知识库统计报告")
    print(f"{'='*60}")
    
    # 加载索引统计
    chunks_path = data_dir / "chunks.json"
    if chunks_path.exists():
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"\n总文本块: {len(chunks)}")
        
        # 按来源统计
        from collections import Counter
        source_counts = Counter(c['source_name'] for c in chunks)
        for source, count in source_counts.items():
            print(f"  - {source}: {count} 个文本块 ({count/len(chunks)*100:.1f}%)")
    
    # 知识库文件
    print(f"\n生成的文件:")
    for file in ["chunks.json", "sources.json", "keyword_index.json", 
                 "commentary_summaries.json", "commentary_knowledge.json"]:
        file_path = data_dir / file
        if file_path.exists():
            size = file_path.stat().st_size / 1024
            print(f"  ✅ {file} ({size:.1f} KB)")
    
    print(f"\n{'='*60}")
    print("✅ 多源知识库构建完成！")
    print(f"{'='*60}")
    print("\n现在可以运行: streamlit run app.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(build_multi_source_knowledge())