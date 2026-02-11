#!/usr/bin/env python3
"""
专家级 AI - 真正的精读者和文学评论家
"""

import os
import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI


class ExpertAI:
    """
    专家级 AI - 以文学评论家、小说精读者的身份回答
    """
    
    def __init__(self, api_key: str = None, knowledge_base_path: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"
        
        # 加载专家知识库
        self.kb = {}
        if knowledge_base_path:
            self._load_knowledge_base(knowledge_base_path)
    
    def _load_knowledge_base(self, path: str):
        """加载专家知识库"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.kb = json.load(f)
            print(f"✅ 专家知识库加载完成: {len(self.kb.get('character_timeline', {}))} 个人物")
        except Exception as e:
            print(f"⚠️ 知识库加载失败: {e}")
    
    def build_system_prompt(self) -> str:
        """
        专家级系统提示词 - 文学评论家+精读者身份
        """
        return """你是《雪中悍刀行》的顶尖文学评论家兼资深精读者。你不仅熟悉每一个情节、每一个人物，更能洞察小说的深层结构、主题意涵和文学价值。

你的身份特征：
1. **文学评论家** - 能从叙事结构、人物塑造、主题表达等专业角度分析作品
2. **精读者** - 对文本细节了如指掌，能精准引用原文，追踪人物命运轨迹
3. **故事讲述者** - 善于将复杂情节娓娓道来，让听众身临其境

回答原则：
1. **深度优先于广度** - 不要泛泛而谈，深入分析2-3个关键点即可
2. **因果重于罗列** - 解释"为什么"比罗列"发生了什么"更重要
3. **原文作为证据** - 关键论点必须有原文支撑，引用要精确到章节感
4. **人物动机分析** - 深入挖掘人物行为的内心驱动力
5. **主题升华** - 从具体情节上升到人生哲理或社会隐喻

回答结构（三段式）：
**【事实层】** 精准回答发生了什么（什么人、什么事、什么结果）
**【分析层】** 深入剖析原因、动机、影响（为什么会这样、意味着什么）
**【升华层】** 联系主题、象征意义、人物成长弧线（更大的图景）

语言风格：
- 专业但不晦涩，像给知己讲一个你深爱的故事
- 适当使用文学评论术语（如"人物弧光"、"叙事张力"、"象征隐喻"）
- 可以表达对人物、情节的个人理解和情感共鸣
- 不回避复杂性——好的文学作品从来都不是非黑即白的

禁止：
- 机械罗列章节内容
- 只描述不分析
- 给出确定的道德判断（而是呈现复杂性）"""
    
    def build_context(self, query: str, text_context: str = "") -> str:
        """
        构建增强上下文 - 融合专家知识库
        """
        context_parts = []
        
        # 1. 提取查询中的关键人物
        mentioned_chars = []
        if self.kb:
            for char in self.kb.get('character_timeline', {}).keys():
                if char in query:
                    mentioned_chars.append(char)
        
        # 2. 添加人物时间线信息
        if mentioned_chars:
            context_parts.append("【人物轨迹】")
            for char in mentioned_chars[:2]:  # 最多2个人物
                timeline = self.kb.get('character_timeline', {}).get(char, [])
                if timeline:
                    # 找到与问题相关的关键节点
                    relevant_events = [
                        e for e in timeline 
                        if any(kw in e.get('event', '') for kw in query.split())
                    ][:3]
                    
                    if not relevant_events:
                        relevant_events = timeline[:3]
                    
                    context_parts.append(f"\n{char}的关键节点:")
                    for e in relevant_events:
                        context_parts.append(f"  - {e['chapter']}: {e['event'][:80]}...")
        
        # 3. 添加情节因果（如果匹配）
        if self.kb and 'plot_causes' in self.kb:
            for event_name, event_data in self.kb['plot_causes'].items():
                if any(kw in query for kw in event_name.split()):
                    context_parts.append(f"\n【事件分析: {event_name}】")
                    context_parts.append(f"深层原因: {event_data.get('cause', '')}")
                    context_parts.append(f"直接影响: {event_data.get('result', '')}")
                    context_parts.append(f"长远意义: {event_data.get('impact', '')}")
                    break
        
        # 4. 添加主题关联（如果匹配）
        if self.kb and 'themes' in self.kb:
            for theme_name, theme_data in self.kb['themes'].items():
                if any(kw in query for kw in theme_name.split()):
                    context_parts.append(f"\n【主题关联: {theme_name}】")
                    context_parts.append(theme_data.get('description', ''))
                    break
        
        # 5. 添加原文片段
        if text_context:
            context_parts.append("\n【原文参考】")
            context_parts.append(text_context)
        
        return "\n".join(context_parts)
    
    def answer(self, query: str, text_context: str = "", temperature: float = 0.7) -> Dict:
        """生成专家级回答"""
        
        system_prompt = self.build_system_prompt()
        context = self.build_context(query, text_context)
        
        user_prompt = f"""关于《雪中悍刀行》的深度问题：

{query}

以下是我为你整理的背景信息（包括人物轨迹、情节因果、主题关联和原文参考）：

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
                "usage": {
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


if __name__ == "__main__":
    # 测试
    print("🧪 测试专家级 AI")
    print("="*80)
    
    ai = ExpertAI(
        api_key="sk-cdebe0fafcf9406d962e3e09a0404e4b",
        knowledge_base_path="data/expert_knowledge_base.json"
    )
    
    test_queries = [
        "徐凤年为什么要杀韩貂寺？这个事件对他的成长意味着什么？",
        "王仙芝自称天下第二，这背后有什么深层含义？",
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"❓ 问题: {query}")
        print(f"{'='*80}")
        
        result = ai.answer(query)
        
        if result['success']:
            print(f"\n💬 专家回答:")
            print(result['answer'])
            print(f"\n💰 Token: {result['usage']['total_tokens']}")
        else:
            print(f"❌ 错误: {result['error']}")
