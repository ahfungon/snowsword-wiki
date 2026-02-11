#!/usr/bin/env python3
"""
初始化脚本：构建多源知识库
整合小说原文和解说全集
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent))

def main():
    # 检查是否有解说全集
    commentary_file = Path("data/雪中悍刀行_解说全集.txt")
    novel_file = Path("data/雪中悍刀行.txt")
    
    if commentary_file.exists():
        # 使用多源构建器
        print("🚀 检测到解说全集，使用多源知识库构建...")
        from build_multi_source import build_multi_source_knowledge
        return build_multi_source_knowledge()
    elif novel_file.exists():
        # 仅构建小说索引
        print("🚀 开始构建小说索引...")
        from src.multi_source_indexer import MultiSourceIndexer
        
        print(f"📖 文本文件: {novel_file}")
        print(f"📊 文件大小: {novel_file.stat().st_size / 1024 / 1024:.2f} MB")
        print()
        
        indexer = MultiSourceIndexer(chunk_size=800, overlap=100)
        
        try:
            indexer.add_source(novel_file, "小说原文", "novel")
            indexer.build_all_indexes("data")
            print()
            print("✅ 索引构建完成！")
            print("现在可以运行: streamlit run app.py")
            return 0
        except Exception as e:
            print(f"❌ 索引构建失败: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print(f"❌ 错误：找不到文本文件")
        print("请确保以下文件之一存在:")
        print("  - data/雪中悍刀行.txt")
        print("  - data/雪中悍刀行_解说全集.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
