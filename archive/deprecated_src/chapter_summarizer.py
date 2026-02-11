#!/usr/bin/env python3
"""
章节摘要生成器 - 提取每章核心内容
"""

import json
import re
from pathlib import Path
from typing import Dict, List


class ChapterSummarizer:
    """生成章节摘要"""
    
    def __init__(self):
        self.chapters = []  # 章节列表
        
    def parse_chapters(self, text: str) -> List[Dict]:
        """解析章节结构"""
        print("📚 正在解析章节结构...")
        
        # 匹配章节标题（多种格式）
        chapter_patterns = [
            r'第[一二三四五六七八九十百千万零\d]+章\s+.+',  # 第一章 标题
            r'第[\d]+章\s+.+',  # 第1章 标题
        ]
        
        chapters = []
        lines = text.split('\n')
        current_chapter = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是章节标题
            is_chapter = False
            for pattern in chapter_patterns:
                if re.match(pattern, line):
                    # 保存上一章
                    if current_chapter:
                        chapters.append({
                            'title': current_chapter,
                            'content': '\n'.join(current_content),
                            'word_count': len(''.join(current_content))
                        })
                    
                    current_chapter = line
                    current_content = []
                    is_chapter = True
                    break
            
            if not is_chapter and current_chapter:
                current_content.append(line)
        
        # 保存最后一章
        if current_chapter and current_content:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content),
                'word_count': len(''.join(current_content))
            })
        
        self.chapters = chapters
        print(f"✅ 解析完成，共 {len(chapters)} 章")
        return chapters
    
    def extract_key_events(self, chapter_content: str) -> List[str]:
        """提取章节关键事件"""
        events = []
        
        # 提取关键句（包含人物动作的句子）
        sentences = re.split(r'[。！？\n]', chapter_content)
        
        # 关键词权重
        action_keywords = ['杀', '战', '斗', '遇', '见', '说', '问', '答', '走', '来', '去', '死', '伤', '胜', '败']
        
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 100:
                continue
            
            # 包含主要人物的句子更可能是关键事件
            main_chars = ['徐凤年', '徐骁', '姜泥', '李淳罡', '邓太阿', '王仙芝', '拓跋菩萨']
            has_main_char = any(char in sent for char in main_chars)
            
            # 包含动作关键词
            has_action = any(kw in sent for kw in action_keywords)
            
            if has_main_char and has_action:
                events.append(sent)
        
        # 返回前5个关键事件
        return events[:5]
    
    def extract_characters_in_chapter(self, chapter_content: str) -> List[str]:
        """提取章节中出现的人物"""
        main_chars = ['徐凤年', '徐骁', '姜泥', '南宫仆射', '李淳罡', '邓太阿', 
                     '王仙芝', '拓跋菩萨', '曹长卿', '陈芝豹', '褚禄山', '袁左宗']
        
        found = []
        for char in main_chars:
            if char in chapter_content:
                found.append(char)
        
        return found
    
    def generate_summary(self, chapter: Dict) -> Dict:
        """生成单章摘要"""
        content = chapter['content']
        
        # 提取关键事件
        key_events = self.extract_key_events(content)
        
        # 提取人物
        characters = self.extract_characters_in_chapter(content)
        
        # 提取地点（简单匹配）
        locations = []
        location_keywords = ['北凉', '离阳', '太安城', '武帝城', '清凉山', '北莽']
        for loc in location_keywords:
            if loc in content:
                locations.append(loc)
        
        return {
            'title': chapter['title'],
            'word_count': chapter['word_count'],
            'key_events': key_events,
            'characters': characters,
            'locations': list(set(locations))
        }
    
    def generate_all_summaries(self) -> List[Dict]:
        """生成所有章节摘要"""
        print(f"📝 正在生成 {len(self.chapters)} 章的摘要...")
        
        summaries = []
        for i, chapter in enumerate(self.chapters):
            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(self.chapters)}")
            
            summary = self.generate_summary(chapter)
            summaries.append(summary)
        
        print(f"✅ 章节摘要生成完成")
        return summaries
    
    def save(self, summaries: List[Dict], output_path: Path):
        """保存摘要"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
        print(f"💾 章节摘要已保存: {output_path}")


if __name__ == "__main__":
    # 测试
    data_dir = Path("data")
    
    # 加载小说
    print("📖 加载小说...")
    with open(data_dir / "雪中悍刀行.txt", 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 解析章节
    summarizer = ChapterSummarizer()
    chapters = summarizer.parse_chapters(text)
    
    # 生成摘要
    summaries = summarizer.generate_all_summaries()
    
    # 显示前3章示例
    print("\n📋 前3章摘要示例:")
    for s in summaries[:3]:
        print(f"\n{s['title']}")
        print(f"  字数: {s['word_count']}")
        print(f"  人物: {', '.join(s['characters'])}")
        print(f"  关键事件: {s['key_events'][0] if s['key_events'] else '无'}")
    
    # 保存
    summarizer.save(summaries, data_dir / "chapter_summaries.json")
