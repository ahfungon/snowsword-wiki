#!/usr/bin/env python3
"""
Expert AI V2 - 简化测试版（不加载大JSON）
"""

import os
from openai import OpenAI

client = OpenAI(
    api_key="sk-cdebe0fafcf9406d962e3e09a0404e4b",
    base_url="https://api.deepseek.com"
)

# 专家级系统提示词
system_prompt = """你是《雪中悍刀行》的顶尖文学评论家兼资深精读者。

回答原则：
1. 深度优先于广度 - 深入分析2-3个关键点
2. 因果重于罗列 - 解释"为什么"比罗列"发生了什么"更重要
3. 原文作为证据 - 关键论点必须有原文支撑
4. 人物动机分析 - 深入挖掘人物行为的内心驱动力
5. 主题升华 - 从具体情节上升到人生哲理

回答结构（三段式）：
**【事实层】** 精准回答发生了什么
**【分析层】** 深入剖析原因、动机、影响
**【升华层】** 联系主题、象征意义、人物成长弧线

语言风格：专业但不晦涩，像给知己讲一个深爱的故事。"""

# 模拟上下文（不依赖大文件）
context = """【人物背景】
徐凤年：北凉王世子，母亲吴素被韩貂寺参与杀害
韩貂寺：离阳太监首领，人称"人猫"，参与京城白衣案

【关键情节】
1. 韩貂寺参与京城白衣案，导致吴素重伤死亡
2. 徐凤年在太安城外设局，带徐婴、呵呵姑娘围攻韩貂寺
3. 韩貂寺死前承认杀害徐凤年母亲

【人物关系】
徐凤年与韩貂寺：杀母之仇，敌对阵营"""

query = "徐凤年为什么要杀韩貂寺？这个事件对他的成长意味着什么？"

user_prompt = f"""问题：{query}

背景信息：{context}

请以文学评论家+精读者的身份，用三段式结构回答。"""

print("🧪 测试 Expert AI V2")
print("="*80)
print(f"\n问题: {query}")
print("\n🤖 生成回答...")
print("="*80)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(f"\n💬 回答 ({response.usage.total_tokens} tokens):")
print("="*80)
print(response.choices[0].message.content)
print("="*80)
print("\n✅ 测试完成！")
