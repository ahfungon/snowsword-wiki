#!/usr/bin/env python3
"""
本地测试工具 - 对比新旧版本效果
"""

import sys
import time
sys.path.append('src')

from enhanced_retriever import EnhancedRetriever
from enhanced_chat import EnhancedChat
from retriever import TextRetriever
from chat import DeepSeekChat


class LocalTester:
    """本地测试工具"""
    
    def __init__(self):
        self.api_key = "sk-cdebe0fafcf9406d962e3e09a0404e4b"
        self.enhanced_retriever = None
        self.enhanced_chat = None
        self.old_retriever = None
        self.old_chat = None
        
    def load_enhanced(self):
        """加载增强版"""
        print("📦 正在加载增强版...")
        print("   (包含知识图谱、章节摘要、向量检索)")
        self.enhanced_retriever = EnhancedRetriever('data')
        self.enhanced_chat = EnhancedChat(self.api_key)
        print("   ✅ 增强版加载完成")
        
    def load_old(self):
        """加载旧版"""
        print("📦 正在加载旧版...")
        print("   (仅关键词检索)")
        self.old_retriever = TextRetriever('data')
        self.old_chat = DeepSeekChat(self.api_key)
        print("   ✅ 旧版加载完成")
    
    def test_query(self, query, mode='both'):
        """
        测试单个查询
        mode: 'enhanced' | 'old' | 'both'
        """
        print(f"\n{'='*80}")
        print(f"🔍 查询: {query}")
        print(f"{'='*80}")
        
        if mode in ('enhanced', 'both'):
            print("\n" + "🚀"*40)
            print("【增强版回答】")
            print("🚀"*40)
            self._test_enhanced(query)
        
        if mode in ('old', 'both'):
            print("\n" + "📋"*40)
            print("【旧版回答】")
            print("📋"*40)
            self._test_old(query)
        
        if mode == 'both':
            print("\n" + "="*80)
            print("💡 对比总结:")
            print("   增强版: 自然、有情感、会串联分析")
            print("   旧版:   机械、仅罗列原文")
            print("="*80)
    
    def _test_enhanced(self, query):
        """测试增强版"""
        start = time.time()
        
        # 检索
        print("\n📖 检索阶段...")
        context = self.enhanced_retriever.get_context(query, top_k=3)
        
        # 显示检索到的信息
        print("   ✓ 找到相关片段")
        if "【人物背景】" in context:
            print("   ✓ 包含人物背景信息")
        if "【相关原文】" in context:
            print("   ✓ 包含原文片段")
        
        # 生成回答
        print("\n🤖 生成回答...")
        result = self.enhanced_chat.chat(query, context, temperature=0.7)
        
        elapsed = time.time() - start
        
        if result['success']:
            print(f"\n💬 回答 (耗时 {elapsed:.1f}s):")
            print("-" * 80)
            print(result['answer'])
            print("-" * 80)
            print(f"💰 Token: {result['usage']['total_tokens']}")
        else:
            print(f"❌ 错误: {result['error']}")
    
    def _test_old(self, query):
        """测试旧版"""
        start = time.time()
        
        # 检索
        print("\n📖 检索阶段...")
        context = self.old_retriever.get_context(query, top_k=3)
        
        # 生成回答
        print("\n🤖 生成回答...")
        result = self.old_chat.chat(query, context, temperature=0.3)
        
        elapsed = time.time() - start
        
        if result['success']:
            print(f"\n💬 回答 (耗时 {elapsed:.1f}s):")
            print("-" * 80)
            print(result['answer'])
            print("-" * 80)
            print(f"💰 Token: {result['usage']['total_tokens']}")
        else:
            print(f"❌ 错误: {result['error']}")
    
    def interactive_mode(self):
        """交互式测试模式"""
        print("\n" + "="*80)
        print("🎮 交互式测试模式")
        print("="*80)
        print("输入问题测试增强版，输入 'old:问题' 测试旧版，输入 'quit' 退出")
        print("示例问题:")
        print("  - 徐凤年为什么要杀韩貂寺？")
        print("  - 王仙芝为什么自称天下第二？")
        print("  - 姜泥和徐凤年的结局是什么？")
        print("="*80)
        
        while True:
            print("\n" + "-"*80)
            user_input = input("\n❓ 你的问题: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("👋 再见！")
                break
            
            if user_input.startswith('old:'):
                query = user_input[4:].strip()
                self.test_query(query, mode='old')
            else:
                self.test_query(user_input, mode='enhanced')
    
    def batch_test(self, queries):
        """批量测试"""
        print("\n" + "="*80)
        print(f"🧪 批量测试 {len(queries)} 个问题")
        print("="*80)
        
        for i, query in enumerate(queries, 1):
            print(f"\n【测试 {i}/{len(queries)}】")
            self.test_query(query, mode='both')
            if i < len(queries):
                input("\n按 Enter 继续下一个...")


def main():
    """主函数"""
    print("="*80)
    print("🧪 雪中悍刀行 Wiki - 本地测试工具")
    print("="*80)
    
    tester = LocalTester()
    
    # 加载模型
    print("\n📦 正在加载模型（首次需要1-2分钟）...")
    tester.load_enhanced()
    # tester.load_old()  # 如果需要对比，取消注释
    
    # 预设测试问题
    test_queries = [
        "徐凤年为什么要杀韩貂寺？",
        "王仙芝为什么自称天下第二？",
        "姜泥和徐凤年的结局是什么？",
        "李淳罡为什么被困听潮阁？",
        "徐凤年和拓跋菩萨打过几回？",
    ]
    
    print("\n" + "="*80)
    print("请选择测试模式:")
    print("  1. 交互式测试（推荐）")
    print("  2. 批量测试预设问题")
    print("  3. 对比测试（增强版 vs 旧版）")
    print("="*80)
    
    choice = input("\n输入选项 (1/2/3): ").strip()
    
    if choice == '1':
        tester.interactive_mode()
    elif choice == '2':
        tester.batch_test(test_queries)
    elif choice == '3':
        print("\n加载旧版进行对比...")
        tester.load_old()
        tester.batch_test(test_queries[:3])  # 对比前3个
    else:
        print("默认进入交互模式...")
        tester.interactive_mode()


if __name__ == "__main__":
    main()
