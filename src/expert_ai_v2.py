#!/usr/bin/env python3
"""
专家级 AI V2 - 深度分析回答生成器
基于现有知识库（不依赖语义索引）
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpertAIV2:
    """
    专家级 AI V2
    - 整合知识图谱、事件、原文进行深度分析
    - 三段式回答：事实→分析→升华
    - 支持 DeepSeek Embedding 语义检索
    """
    
    def __init__(self, api_key: str = None, knowledge_base_path: Path = None, use_semantic: bool = True):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"
        self.use_semantic = use_semantic  # 是否使用语义检索
        
        # 加载知识库
        self.knowledge_base = {}
        self.events = []
        self.paragraphs = []
        self.retriever = None  # 语义检索器
        
        if knowledge_base_path:
            self._load_knowledge(knowledge_base_path)
    
    def load_semantic_index(self, index_path: Path, zhipu_api_key: str = None):
        """加载语义检索索引（智谱 AI Embedding）"""
        try:
            from .zhipu_retriever import ZhipuEmbeddingRetriever
            
            api_key = zhipu_api_key or os.getenv("ZHIPU_API_KEY")
            if not api_key:
                logger.warning("⚠️ 未提供智谱 API Key，回退到关键词检索")
                self.use_semantic = False
                return
            
            self.retriever = ZhipuEmbeddingRetriever(api_key=api_key)
            self.retriever.load_index(index_path)
            self.use_semantic = True
            logger.info("✅ 智谱语义检索索引加载成功")
        except Exception as e:
            logger.warning(f"⚠️ 语义检索索引加载失败: {e}，回退到关键词检索")
            self.use_semantic = False
    
    def _load_knowledge(self, base_path: Path):
        """加载知识库数据"""
        logger.info("📂 加载知识库...")
        
        # 加载专家知识库
        kb_file = base_path / "expert_knowledge_base.json"
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            logger.info(f"   ✓ 知识图谱: {len(self.knowledge_base.get('character_timeline', {}))} 人物")
        
        # 加载事件
        events_file = base_path / "processed_v2" / "events_v2.json"
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                self.events = json.load(f)
            logger.info(f"   ✓ 事件: {len(self.events)} 条")
        
        # 加载段落（前1000个用于快速检索）
        para_file = base_path / "processed_v2" / "paragraphs_v2.json"
        if para_file.exists():
            with open(para_file, 'r', encoding='utf-8') as f:
                all_paras = json.load(f)
                self.paragraphs = all_paras[:2000]  # 先加载前2000个
            logger.info(f"   ✓ 段落: {len(self.paragraphs)}/{len(all_paras)} (前2000)")
    
    def build_system_prompt(self) -> str:
        """专家级系统提示词"""
        return """你是《雪中悍刀行》的顶尖文学评论家兼资深精读者。

回答原则：
1. **深度优先于广度** - 深入分析2-3个关键点，不要泛泛而谈
2. **因果重于罗列** - 解释"为什么"比罗列"发生了什么"更重要
3. **原文作为证据** - 关键论点必须有原文支撑，引用要精确
4. **人物动机分析** - 深入挖掘人物行为的内心驱动力
5. **主题升华** - 从具体情节上升到人生哲理或社会隐喻

回答结构（三段式）：
**【事实层】** 精准回答发生了什么（人物、事件、结果）
**【分析层】** 深入剖析原因、动机、影响（为什么会这样）
**【升华层】** 联系主题、象征意义、人物成长（更大的图景）

语言风格：
- 专业但不晦涩，像给知己讲一个深爱的故事
- 使用文学评论术语（人物弧光、叙事张力、象征隐喻）
- 可以表达对人物的理解和情感共鸣
- 呈现复杂性，不回避灰色地带

禁止：
- 机械罗列章节内容
- 只描述不分析
- 给出简单的道德判断"""
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """关键词检索（备用方案）"""
        keywords = set(query.split())
        
        # 在段落中搜索
        scored_paras = []
        for para in self.paragraphs:
            content = para['content']
            
            # 计算关键词匹配分数
            score = sum(2 for kw in keywords if kw in content)
            
            # 如果有实体匹配，加分
            for char in self.knowledge_base.get('character_timeline', {}).keys():
                if char in query and char in content:
                    score += 3
            
            if score > 0:
                scored_paras.append((para, score))
        
        # 排序取前K
        scored_paras.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in scored_paras[:top_k]]
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义检索（使用 DeepSeek Embedding）"""
        if self.retriever is None:
            logger.warning("⚠️ 语义检索器未加载，回退到关键词检索")
            return self.keyword_search(query, top_k)
        
        try:
            results = self.retriever.search(query, top_k=top_k)
            # 转换为统一格式
            return [
                {
                    'content': r['content'],
                    'chapter': r.get('chapter', '未知'),
                    'similarity': r.get('similarity', 0)
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"❌ 语义检索失败: {e}")
            return self.keyword_search(query, top_k)
    
    def build_context(self, query: str) -> str:
        """构建增强上下文"""
        context_parts = []
        
        # 1. 提取查询中的人物
        mentioned_chars = []
        for char in self.knowledge_base.get('character_timeline', {}).keys():
            if char in query:
                mentioned_chars.append(char)
        
        # 2. 添加人物时间线
        if mentioned_chars:
            context_parts.append("【人物轨迹】")
            for char in mentioned_chars[:2]:
                timeline = self.knowledge_base.get('character_timeline', {}).get(char, [])
                if timeline:
                    # 找相关事件
                    relevant = [
                        e for e in timeline 
                        if any(kw in e.get('event', '') for kw in query.split()[:3])
                    ][:3]
                    if not relevant:
                        relevant = timeline[:3]
                    
                    context_parts.append(f"\n{char}:")
                    for e in relevant:
                        context_parts.append(f"  - {e['chapter']}: {e['event'][:80]}...")
        
        # 3. 添加情节因果（如果匹配）
        if self.knowledge_base.get('plot_causes'):
            for event_name, event_data in self.knowledge_base['plot_causes'].items():
                if any(kw in query for kw in event_name.split()):
                    context_parts.append(f"\n【事件分析: {event_name}】")
                    context_parts.append(f"原因: {event_data.get('cause', '')}")
                    context_parts.append(f"结果: {event_data.get('result', '')}")
                    context_parts.append(f"影响: {event_data.get('impact', '')}")
                    break
        
        # 4. 添加原文段落（优先使用语义检索）
        if self.use_semantic and self.retriever is not None:
            logger.info("🔍 使用语义检索查找相关原文...")
            relevant_paras = self.semantic_search(query, top_k=3)
            context_parts.append("\n【相关原文 (语义匹配)】")
        else:
            logger.info("🔍 使用关键词检索查找相关原文...")
            relevant_paras = self.keyword_search(query, top_k=3)
            context_parts.append("\n【相关原文 (关键词匹配)】")
        
        if relevant_paras:
            for i, para in enumerate(relevant_paras, 1):
                context_parts.append(f"\n段落{i} [{para.get('chapter', '未知')}]:")
                context_parts.append(para['content'][:300])
        
        return "\n".join(context_parts)
    
    def answer(self, query: str, temperature: float = 0.7) -> Dict:
        """生成专家级回答"""
        logger.info(f"🤖 处理问题: {query[:50]}...")
        
        # 构建上下文
        context = self.build_context(query)
        
        # 构建提示
        system_prompt = self.build_system_prompt()
        user_prompt = f"""关于《雪中悍刀行》的深度问题：

{query}

以下是我为你整理的背景信息：

{context}

请以文学评论家+精读者的身份，用三段式结构（事实层→分析层→升华层）回答这个问题。深入分析，不要泛泛而谈。"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
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
                }
            }
        except Exception as e:
            logger.error(f"❌ API 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }


if __name__ == "__main__":
    print("🧪 测试 Expert AI V2")
    print("="*60)
    
    ai = ExpertAIV2(
        api_key="sk-cdebe0fafcf9406d962e3e09a0404e4b",
        knowledge_base_path=Path("data")
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
        
        result = ai.answer(query)
        
        if result['success']:
            print(f"\n💬 回答:")
            print(result['answer'])
            print(f"\n💰 Token: {result['usage']['total_tokens']}")
        else:
            print(f"❌ 错误: {result['error']}")
