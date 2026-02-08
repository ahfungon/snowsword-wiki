#!/usr/bin/env python3
"""
增强版 DeepSeek Chat - 更自然、更智能的回答
"""

import os
from typing import List, Dict
from openai import OpenAI


class EnhancedChat:
    """增强版聊天模块"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            raise ValueError("请提供 DeepSeek API Key")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        self.model = "deepseek-chat"
    
    def build_system_prompt(self) -> str:
        """
        构建系统提示词 - 更像一个懂小说的朋友
        """
        return """你是《雪中悍刀行》的资深读者，一个对这部小说烂熟于心的朋友。你热爱这部小说，乐于分享你的理解。

回答风格：
1. **像朋友聊天一样自然** - 不用学术腔，不说"根据第X章"，而是用"我记得"、"小说里写过"
2. **善于串联信息** - 能结合多处原文，给出完整的故事脉络
3. **有温度有情感** - 可以表达对人物、情节的理解和感受
4. **合理推测补充** - 如果原文有留白，可以基于人物性格合理推断，但要说明是推测
5. **适当引用原文** - 关键情节可以引用一两句原文增强说服力，但不要大段罗列

回答结构：
- 先给出核心答案（直接、简洁）
- 然后展开讲述（背景、原因、影响）
- 最后可以分享一点见解或感受

不要：
- 机械罗列"原文第X章说..."
- 只给答案不给解释
- 说"根据提供的文本..."这种AI腔
- 编造原文中没有的重大情节"""
    
    def build_user_prompt(self, query: str, context: str) -> str:
        """构建用户提示"""
        return f"""关于《雪中悍刀行》的问题：{query}

我找到的参考信息（你不需要全部使用，选有用的）：
{context}

请像朋友一样回答这个问题。如果参考信息不够，可以基于你对小说的理解补充，但要诚实地说哪些是你的推断。

直接回答我的问题，不要客套话。"""
    
    def chat(self, query: str, context: str, temperature: float = 0.7) -> Dict:
        """
        生成回答
        
        temperature 调高到 0.7 让回答更自然有创意
        """
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(query, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2000,
                stream=False
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "answer": answer,
                "query": query,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def chat_stream(self, query: str, context: str, temperature: float = 0.7):
        """流式生成"""
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(query, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2000,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"\n[错误: {str(e)}]"


if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from src.enhanced_retriever import EnhancedRetriever
    
    print("🧪 测试增强版聊天...")
    
    retriever = EnhancedRetriever()
    chat = EnhancedChat()
    
    query = "徐凤年为什么要杀韩貂寺？"
    print(f"\n🔍 查询: {query}")
    
    context = retriever.get_context(query, top_k=3)
    print(f"\n上下文长度: {len(context)} 字符")
    
    result = chat.chat(query, context)
    
    if result["success"]:
        print(f"\n💬 AI 回答:")
        print("=" * 60)
        print(result["answer"])
        print(f"\n💰 Token: {result['usage']['total_tokens']}")
    else:
        print(f"❌ 错误: {result['error']}")
