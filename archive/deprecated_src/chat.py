"""
DeepSeek API 调用模块
"""

import os
from typing import List, Dict
from openai import OpenAI

class DeepSeekChat:
    def __init__(self, api_key: str = None):
        """
        初始化 DeepSeek 客户端
        
        Args:
            api_key: DeepSeek API Key，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            raise ValueError("请提供 DeepSeek API Key 或设置环境变量 DEEPSEEK_API_KEY")
        
        # DeepSeek 使用 OpenAI 兼容的 API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        self.model = "deepseek-chat"  # 使用 DeepSeek-V3 模型
    
    def build_prompt(self, query: str, context: str) -> str:
        """
        构建严格的系统提示词，确保回答基于提供的文本
        """
        system_prompt = """你是一个《雪中悍刀行》小说百科助手。你的任务是严格基于提供的小说原文回答问题。

重要规则：
1. 你只能使用【提供的小说原文段落】来回答问题
2. 如果原文中没有相关信息，请明确说"根据小说原文，我没有找到相关信息"
3. 不要编造、推测或引用原文以外的知识
4. 回答要准确、简洁，并引用相关原文
5. 如果问题涉及多个方面，请分别回答

回答格式：
- 先给出直接答案
- 然后列出依据的原文（标注章节）
- 如果信息不足，说明缺失的部分"""

        user_prompt = f"""问题：{query}

以下是小说中的相关原文段落，请基于这些段落回答问题：

{context}

请根据以上原文回答问题。如果原文中没有答案，请明确说明。"""

        return system_prompt, user_prompt
    
    def chat(self, query: str, context: str, temperature: float = 0.3) -> Dict:
        """
        调用 DeepSeek API 生成回答
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            temperature: 生成温度（越低越确定）
            
        Returns:
            Dict containing answer and metadata
        """
        system_prompt, user_prompt = self.build_prompt(query, context)
        
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
    
    def chat_stream(self, query: str, context: str, temperature: float = 0.3):
        """
        流式调用 API（用于实时显示）
        """
        system_prompt, user_prompt = self.build_prompt(query, context)
        
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
    # 测试
    import sys
    sys.path.append('.')
    from src.retriever import TextRetriever
    
    retriever = TextRetriever()
    chat = DeepSeekChat()
    
    query = "徐凤年是谁？"
    context = retriever.get_context(query, top_k=3)
    
    print(f"查询: {query}")
    print("=" * 60)
    print("上下文:")
    print(context[:500])
    print("\n回答:")
    
    result = chat.chat(query, context)
    if result["success"]:
        print(result["answer"])
        print(f"\nToken 使用: {result['usage']}")
    else:
        print(f"错误: {result['error']}")
