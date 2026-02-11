#!/usr/bin/env python3
"""
专家检索器 V2 - 完整版
整合文本处理、语义检索、知识图谱
"""

import json
import gzip
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import logging

from text_processor_v2 import TextProcessorV2
from semantic_retriever_v2 import SemanticRetrieverV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpertRetrieverV2:
    """
    专家检索器 V2
    - 文本处理（段落分割、实体抽取、事件检测）
    - 语义检索（BGE Embedding）
    - 知识图谱（人物关系、情节因果）
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.text_processor = TextProcessorV2()
        self.semantic_retriever = None
        
        # 数据存储
        self.paragraphs = []
        self.entities = []
        self.events = []
        self.knowledge_graph = {}
        
        # 加载数据
        self._load_data()
    
    def _load_data(self):
        """加载处理后的数据"""
        processed_dir = self.data_dir / "processed_v2"
        
        # 检查是否需要处理
        if not (processed_dir / "paragraphs_v2.json").exists():
            logger.info("📦 数据未处理，开始处理...")
            self._process_raw_data()
        
        # 加载段落
        logger.info("📂 加载段落数据...")
        with open(processed_dir / "paragraphs_v2.json", 'r', encoding='utf-8') as f:
            self.paragraphs = json.load(f)
        
        # 加载实体
        if (processed_dir / "entities_v2.json").exists():
            with open(processed_dir / "entities_v2.json", 'r', encoding='utf-8') as f:
                self.entities = json.load(f)
        
        # 加载事件
        if (processed_dir / "events_v2.json").exists():
            with open(processed_dir / "events_v2.json", 'r', encoding='utf-8') as f:
                self.events = json.load(f)
        
        # 加载知识图谱
        kg_path = self.data_dir / "expert_knowledge_base.json"
        if kg_path.exists():
            with open(kg_path, 'r', encoding='utf-8') as f:
                self.knowledge_graph = json.load(f)
        
        logger.info(f"✅ 数据加载完成:")
        logger.info(f"   段落: {len(self.paragraphs):,}")
        logger.info(f"   实体记录: {len(self.entities):,}")
        logger.info(f"   事件: {len(self.events):,}")
        if self.knowledge_graph:
            logger.info(f"   人物: {len(self.knowledge_graph.get('character_timeline', {}))}")
    
    def _process_raw_data(self):
        """处理原始数据"""
        text_file = self.data_dir / "雪中悍刀行.txt"
        if not text_file.exists():
            # 解压
            compressed_files = sorted(self.data_dir.glob("chunks_small_*.gz"))
            if compressed_files:
                logger.info("📦 解压数据...")
                self._decompress_files(compressed_files)
        
        # 处理
        if text_file.exists():
            self.text_processor.process_novel(
                text_file,
                self.data_dir / "processed_v2"
            )
    
    def _decompress_files(self, compressed_files: List[Path]):
        """解压文件"""
        temp_dir = self.data_dir / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"🗜️  解压 {len(compressed_files)} 个文件...")
        for gz_file in compressed_files:
            output_file = temp_dir / gz_file.stem
            with gzip.open(gz_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    f_out.write(f_in.read())
        
        # 合并
        output_file = self.data_dir / "雪中悍刀行.txt"
        split_files = sorted(temp_dir.glob("chunks_small_*"))
        files_str = ' '.join([str(f) for f in split_files])
        cmd = f"cat {files_str} > {output_file}"
        subprocess.run(cmd, shell=True, check=True)
        
        # 清理
        for f in split_files:
            f.unlink()
        temp_dir.rmdir()
        
        logger.info(f"✅ 解压完成: {output_file}")
    
    def build_semantic_index(self):
        """构建语义索引"""
        logger.info("🔨 构建语义索引...")
        
        self.semantic_retriever = SemanticRetrieverV2()
        self.semantic_retriever.build_index(
            self.paragraphs,
            self.data_dir / "semantic_index_v2"
        )
        
        logger.info("✅ 语义索引构建完成")
    
    def load_semantic_index(self):
        """加载语义索引"""
        index_dir = self.data_dir / "semantic_index_v2"
        if not (index_dir / "embeddings.npy").exists():
            logger.info("📦 语义索引不存在，开始构建...")
            self.build_semantic_index()
        else:
            self.semantic_retriever = SemanticRetrieverV2()
            self.semantic_retriever.load_index(index_dir)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索相关段落
        """
        if self.semantic_retriever is None:
            self.load_semantic_index()
        
        # 语义检索
        results = self.semantic_retriever.search(query, top_k=top_k)
        
        return results
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        获取增强上下文（用于回答生成）
        """
        # 检索段落
        results = self.retrieve(query, top_k=top_k)
        
        # 提取查询中的人物
        mentioned_chars = []
        for char in self.knowledge_graph.get('character_timeline', {}).keys():
            if char in query:
                mentioned_chars.append(char)
        
        # 构建上下文
        context_parts = []
        
        # 1. 人物时间线信息
        if mentioned_chars:
            context_parts.append("【人物轨迹】")
            for char in mentioned_chars[:2]:
                timeline = self.knowledge_graph.get('character_timeline', {}).get(char, [])
                if timeline:
                    # 找到相关事件
                    relevant = [
                        e for e in timeline 
                        if any(kw in query for kw in e.get('event', '')[:20])
                    ][:3]
                    if not relevant:
                        relevant = timeline[:3]
                    
                    context_parts.append(f"\n{char}:")
                    for e in relevant:
                        context_parts.append(f"  - {e['chapter']}: {e['event'][:60]}...")
        
        # 2. 相关原文段落
        context_parts.append("\n【相关原文】")
        for i, r in enumerate(results, 1):
            context_parts.append(f"\n段落{i} (相关度: {r['similarity']:.3f}):")
            context_parts.append(r['content'][:300])
        
        return "\n".join(context_parts)


if __name__ == "__main__":
    print("🧪 测试 Expert Retriever V2")
    print("="*60)
    
    # 初始化
    retriever = ExpertRetrieverV2()
    
    # 构建语义索引（如果未构建）
    # retriever.build_semantic_index()
    
    # 测试查询
    query = "徐凤年为什么要杀韩貂寺？"
    print(f"\n🔍 查询: {query}")
    
    # 检索
    results = retriever.retrieve(query, top_k=3)
    
    print(f"\n检索结果:")
    for r in results:
        print(f"  [{r['idx']}] {r['content'][:80]}...")
        print(f"      相似度: {r['similarity']:.3f}, 章节: {r['chapter']}")
