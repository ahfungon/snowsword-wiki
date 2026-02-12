#!/usr/bin/env python3
"""
专家系统 V2 完整版 - 支持智谱语义检索
整合：文本处理 + 语义检索 + 专家AI
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent))

from lightweight_retriever import LightweightRetriever
from expert_ai_v2 import ExpertAIV2

# 尝试导入智谱检索器
try:
    from zhipu_retriever import ZhipuEmbeddingRetriever
    ZHIPU_RETRIEVER_AVAILABLE = True
    logger.info("✅ ZhipuEmbeddingRetriever 导入成功")
except ImportError as e:
    logger.warning(f"⚠️ 无法导入 ZhipuEmbeddingRetriever: {e}")
    ZhipuEmbeddingRetriever = None
    ZHIPU_RETRIEVER_AVAILABLE = False


class ExpertSystemV2:
    """
    专家系统 V2（支持智谱语义检索）
    """
    
    def __init__(self, data_dir: str = "data", api_key: str = None, zhipu_api_key: str = None):
        self.data_dir = Path(data_dir)
        self.zhipu_api_key = zhipu_api_key or os.getenv("ZHIPU_API_KEY")
        
        # 初始化组件
        self.retriever = None
        self.ai = None
        self.use_semantic = False  # 是否使用语义检索
        
        # 加载
        self._init_retriever()
        self._init_ai(api_key)
    
    def _init_retriever(self):
        """初始化检索器（优先使用智谱语义索引）"""
        logger.info("📂 初始化检索器...")
        
        # 1. 优先尝试加载智谱语义索引
        zhipu_index_dir = self.data_dir / "zhipu_index"
        if zhipu_index_dir.exists() and (zhipu_index_dir / "embeddings.npy").exists():
            if self.zhipu_api_key:
                try:
                    if not ZHIPU_RETRIEVER_AVAILABLE or ZhipuEmbeddingRetriever is None:
                        raise ImportError("ZhipuEmbeddingRetriever 模块不可用")
                    self.retriever = ZhipuEmbeddingRetriever(api_key=self.zhipu_api_key)
                    self.retriever.load_index(zhipu_index_dir)
                    self.use_semantic = True
                    logger.info("✅ 智谱语义检索器加载成功")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ 智谱语义索引加载失败: {e}")
            else:
                logger.info("ℹ️ 未配置 ZHIPU_API_KEY，跳过语义索引")
        
        # 2. 回退到 TF-IDF 索引
        logger.info("📂 使用 TF-IDF 索引...")
        index_dir = self.data_dir / "semantic_index_light"
        
        # 检查索引是否存在
        if not (index_dir / "tfidf_matrix.npz").exists():
            logger.info("📦 索引不存在，开始构建...")
            self._build_index()
        
        # 加载索引
        self.retriever = LightweightRetriever()
        self.retriever.load_index(index_dir)
        self.use_semantic = False
        
        logger.info("✅ TF-IDF 检索器初始化完成")
    
    def _build_index(self):
        """构建 TF-IDF 索引（备用）"""
        from text_processor_v2 import TextProcessorV2
        
        # 检查处理后的数据是否存在
        para_file = self.data_dir / "processed_v2" / "paragraphs_v2.json"
        
        if not para_file.exists():
            logger.info("📦 处理原始数据...")
            processor = TextProcessorV2()
            processor.process_novel(
                self.data_dir / "雪中悍刀行.txt",
                self.data_dir / "processed_v2"
            )
        
        # 加载段落并构建索引
        logger.info("🔨 构建 TF-IDF 索引...")
        with open(para_file, 'r', encoding='utf-8') as f:
            paragraphs = json.load(f)
        
        retriever = LightweightRetriever()
        retriever.build_index(paragraphs, self.data_dir / "semantic_index_light")
    
    def _init_ai(self, api_key: str = None):
        """初始化AI"""
        logger.info("🤖 初始化专家AI...")
        
        self.ai = ExpertAIV2(
            api_key=api_key,
            knowledge_base_path=self.data_dir
        )
        
        # 如果用了智谱检索器，也加载到 AI 中
        if self.use_semantic and isinstance(self.retriever, ZhipuEmbeddingRetriever):
            self.ai.retriever = self.retriever
            self.ai.use_semantic = True
            logger.info("✅ AI 已关联语义检索器")
        
        logger.info("✅ AI初始化完成")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关段落"""
        return self.retriever.search(query, top_k=top_k)
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """获取增强上下文"""
        # 检索段落
        results = self.retrieve(query, top_k=top_k)
        
        # 构建上下文
        context_parts = []
        
        # 1. 相关原文段落
        index_type = "语义匹配" if self.use_semantic else "关键词匹配"
        context_parts.append(f"【相关原文 ({index_type})】")
        for i, r in enumerate(results, 1):
            context_parts.append(f"\n段落{i} [{r.get('chapter', '未知')}] (相关度: {r.get('similarity', 0):.3f}):")
            context_parts.append(r['content'][:400])
        
        # 2. 知识图谱信息（如果AI已加载）
        if self.ai and self.ai.knowledge_base:
            # 提取查询中的人物
            mentioned_chars = []
            for char in self.ai.knowledge_base.get('character_timeline', {}).keys():
                if char in query:
                    mentioned_chars.append(char)
            
            if mentioned_chars:
                context_parts.append("\n\n【人物背景】")
                for char in mentioned_chars[:2]:
                    timeline = self.ai.knowledge_base.get('character_timeline', {}).get(char, [])
                    if timeline:
                        relevant = [
                            e for e in timeline 
                            if any(kw in e.get('event', '') for kw in query.split()[:3])
                        ][:2]
                        if relevant:
                            context_parts.append(f"\n{char}:")
                            for e in relevant:
                                context_parts.append(f"  - {e['chapter']}: {e['event'][:60]}...")
        
        return "\n".join(context_parts)
    
    def answer(self, query: str, temperature: float = 0.7) -> Dict:
        """生成专家级回答"""
        logger.info(f"🤖 处理问题: {query[:50]}...")
        
        # 获取上下文
        context = self.get_context(query)
        
        # 构建提示
        system_prompt = self.ai.build_system_prompt()
        user_prompt = f"""关于《雪中悍刀行》的深度问题：

{query}

以下是我为你整理的背景信息（包括相关原文和人物背景）：

{context}

请以文学评论家+精读者的身份，用三段式结构（事实层→分析层→升华层）回答这个问题。深入分析，不要泛泛而谈。"""
        
        # 调用API
        try:
            response = self.ai.client.chat.completions.create(
                model=self.ai.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2500,
                stream=False
            )
            
            return {
                "success": True,
                "answer": response.choices[0].message.content,
                "query": query,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "retrieval_mode": "semantic" if self.use_semantic else "tfidf"
            }
        except Exception as e:
            logger.error(f"❌ API 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }


if __name__ == "__main__":
    print("🧪 测试 Expert System V2")
    print("="*60)
    
    # 初始化系统
    system = ExpertSystemV2(
        data_dir="data",
        api_key="sk-cdebe0fafcf9406d962e3e09a0404e4b"
    )
    
    # 测试查询
    test_queries = [
        "徐凤年为什么要杀韩貂寺？",
        "王仙芝为什么自称天下第二？",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"❓ {query}")
        print(f"{'='*60}")
        
        result = system.answer(query)
        
        if result['success']:
            print(f"\n💬 回答:")
            print(result['answer'])
            print(f"\n💰 Token: {result['usage']['total_tokens']}")
            print(f"🔍 检索模式: {result.get('retrieval_mode', 'unknown')}")
        else:
            print(f"❌ 错误: {result['error']}")
