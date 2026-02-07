#!/usr/bin/env python3
"""
初始化脚本：构建索引
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent))

from src.indexer import TextIndexer

def main():
    # 检查文本文件是否存在
    text_file = Path("data/雪中悍刀行.txt")
    
    if not text_file.exists():
        print(f"❌ 错误：找不到文本文件 {text_file}")
        print("请确保小说文本文件位于 data/雪中悍刀行.txt")
        return 1
    
    print("🚀 开始构建索引...")
    print(f"📖 文本文件: {text_file}")
    print(f"📊 文件大小: {text_file.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # 创建索引器
    indexer = TextIndexer(chunk_size=800, overlap=100)
    
    # 构建索引
    try:
        indexer.build_index(str(text_file))
        print()
        print("✅ 索引构建完成！")
        print("现在可以运行: streamlit run app.py")
        return 0
    except Exception as e:
        print(f"❌ 索引构建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
