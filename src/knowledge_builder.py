#!/usr/bin/env python3
"""
知识构建器 - 整合章节摘要和专家知识库构建
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


class KnowledgeBuilder:
    """
    统一知识构建器
    - 章节解析和摘要生成
    - 人物时间线构建
    - 情节因果分析
    - 主题象征识别
    - 精确引用索引
    """
    
    def __init__(self):
        self.chapters = []
        self.summaries = []
        
        # 专家知识库数据
        self.character_timeline = {}
        self.character_relations = {}
        self.character_traits = {}
        self.plot_causes = {}
        self.key_scenes = []
        self.themes = {}
        self.symbols = {}
        self.quote_index = {}
    
    # ==================== 章节解析和摘要 ====================
    
    def parse_chapters(self, text: str) -> List[Dict]:
        """解析章节结构"""
        print("📚 正在解析章节结构...")
        
        chapter_patterns = [
            r'第[一二三四五六七八九十百千万零\d]+章\s+.',
            r'第[\d]+章\s+.',
        ]
        
        chapters = []
        lines = text.split('\n')
        current_chapter = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_chapter = False
            for pattern in chapter_patterns:
                if re.match(pattern, line):
                    if current_chapter and current_content:
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
        sentences = re.split(r'[。！？\n]', chapter_content)
        
        action_keywords = ['杀', '战', '斗', '遇', '见', '说', '问', '答', '走', '来', '去', '死', '伤', '胜', '败']
        main_chars = ['徐凤年', '徐骁', '姜泥', '李淳罡', '邓太阿', '王仙芝', '拓跋菩萨']
        
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 100:
                continue
            
            has_main_char = any(char in sent for char in main_chars)
            has_action = any(kw in sent for kw in action_keywords)
            
            if has_main_char and has_action:
                events.append(sent)
        
        return events[:5]
    
    def extract_characters_in_chapter(self, chapter_content: str) -> List[str]:
        """提取章节中出现的人物"""
        main_chars = ['徐凤年', '徐骁', '姜泥', '南宫仆射', '李淳罡', '邓太阿', 
                     '王仙芝', '拓跋菩萨', '曹长卿', '陈芝豹', '褚禄山', '袁左宗']
        return [char for char in main_chars if char in chapter_content]
    
    def generate_summary(self, chapter: Dict) -> Dict:
        """生成单章摘要"""
        content = chapter['content']
        key_events = self.extract_key_events(content)
        characters = self.extract_characters_in_chapter(content)
        
        locations = [loc for loc in ['北凉', '离阳', '太安城', '武帝城', '清凉山', '北莽'] 
                    if loc in content]
        
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
        
        self.summaries = summaries
        print(f"✅ 章节摘要生成完成")
        return summaries
    
    # ==================== 专家知识库构建 ====================
    
    def build_expert_knowledge(self):
        """构建专家级知识库"""
        print("📚 构建专家级知识库...")
        
        self._build_character_timelines()
        self._extract_key_scenes()
        self._analyze_plot_causality()
        self._identify_themes_and_symbols()
        self._build_quote_index()
        
        print(f"✅ 专家知识库构建完成")
        self._print_stats()
    
    def _build_character_timelines(self):
        """构建人物完整时间线"""
        print("  🕐 构建人物时间线...")
        
        main_chars = [
            "徐凤年", "姜泥", "徐骁", "李淳罡", "南宫仆射", 
            "王仙芝", "邓太阿", "拓跋菩萨", "曹长卿", "陈芝豹",
            "褚禄山", "袁左宗", "齐练华", "吴素"
        ]
        
        for char in main_chars:
            self.character_timeline[char] = []
            self.character_traits[char] = {"initial": {}, "evolution": [], "final": {}}
        
        for ch_idx, chapter in enumerate(self.chapters):
            ch_title = chapter.get('title', f'第{ch_idx+1}章')
            content = chapter.get('content', '')
            
            for char in main_chars:
                if char not in content:
                    continue
                
                paragraphs = content.split('\n')
                for p_idx, para in enumerate(paragraphs):
                    if char in para and len(para) > 20:
                        event = self._extract_character_action(para, char)
                        if event:
                            self.character_timeline[char].append({
                                "chapter": ch_title,
                                "chapter_idx": ch_idx,
                                "paragraph_idx": p_idx,
                                "event": event,
                                "context": para[:300],
                                "word_count": chapter.get('word_count', 0)
                            })
        
        for char in self.character_timeline:
            self.character_timeline[char].sort(key=lambda x: x['chapter_idx'])
    
    def _extract_character_action(self, paragraph: str, character: str) -> str:
        """提取人物行为"""
        sentences = re.split(r'[。！？]', paragraph)
        for sent in sentences:
            if character in sent:
                actions = ['杀', '战', '斗', '说', '问', '答', '走', '来', '去', 
                          '救', '伤', '死', '胜', '败', '见', '遇', '离', '归']
                for act in actions:
                    if act in sent:
                        return sent.strip()[:100]
        return ""
    
    def _extract_key_scenes(self):
        """提取关键场景"""
        print("  🎬 提取关键场景...")
        
        scene_patterns = [
            ("生死战", ["死", "杀", "战", "斗"], 500),
            ("重要对话", ["说", "问", "答", "道"], 400),
            ("突破", ["突破", "境界", "入", "悟"], 400),
            ("离别", ["离", "别", "走", "去", "归"], 400),
            ("重逢", ["见", "遇", "来", "归"], 400),
        ]
        
        scenes = []
        for ch_idx, chapter in enumerate(self.chapters[:200]):
            content = chapter.get('content', '')
            ch_title = chapter.get('title', f'第{ch_idx+1}章')
            paragraphs = content.split('\n\n')
            
            for p_idx, para in enumerate(paragraphs):
                if len(para) < 200:
                    continue
                
                for scene_type, keywords, min_len in scene_patterns:
                    if len(para) >= min_len and any(kw in para for kw in keywords):
                        main_chars = ['徐凤年', '姜泥', '李淳罡', '王仙芝', '邓太阿']
                        if any(char in para for char in main_chars):
                            scenes.append({
                                "type": scene_type,
                                "chapter": ch_title,
                                "chapter_idx": ch_idx,
                                "paragraph_idx": p_idx,
                                "content": para[:800],
                                "keywords": [kw for kw in keywords if kw in para][:3]
                            })
                            break
        
        self.key_scenes = sorted(scenes, key=lambda x: x['chapter_idx'])[:200]
    
    def _analyze_plot_causality(self):
        """分析情节因果关系"""
        print("  🔗 分析情节因果...")
        
        self.plot_causes = {
            "京城白衣案": {
                "cause": "离阳皇室忌惮北凉，吴素怀孕引发猜忌",
                "result": "吴素重伤，徐凤年与离阳结仇",
                "impact": "徐凤年一生复仇的起点，北凉与离阳关系破裂",
                "chapter": "回忆章节"
            },
            "徐凤年游历江湖": {
                "cause": "徐骁安排，让徐凤年了解民间疾苦，增长见识",
                "result": "徐凤年见识江湖险恶，结识温华、老黄等人",
                "impact": "徐凤年性格转变，从纨绔到成熟",
                "chapter": "早期章节"
            },
            "老黄战死武帝城": {
                "cause": "老黄挑战王仙芝，为徐凤年铺武道之路",
                "result": "徐凤年决心习武，继承老黄遗志",
                "impact": "徐凤年正式踏上武道，性格更加坚毅",
                "chapter": "中期章节"
            },
            "李淳罡重出江湖": {
                "cause": "徐凤年第二次游历，李淳罡被其打动",
                "result": "李淳罡成为徐凤年武道引路人",
                "impact": "徐凤年剑道大成，李淳罡重回剑神境界",
                "chapter": "中期章节"
            },
            "韩貂寺之死": {
                "cause": "徐凤年为母报仇，韩貂寺参与白衣案",
                "result": "韩貂寺被击杀，徐凤年大仇得报一部分",
                "impact": "徐凤年与离阳皇室彻底决裂",
                "chapter": "中后期"
            },
            "徐凤年世袭北凉王": {
                "cause": "徐骁去世，徐凤年继承王位",
                "result": "徐凤年正式成为北凉之主",
                "impact": "徐凤年承担起北凉三十万铁甲的责任",
                "chapter": "中后期"
            },
            "拒北城之战": {
                "cause": "北莽南下，北凉面临灭国之危",
                "result": "徐凤年击败拓跋菩萨，守住北凉",
                "impact": "徐凤年成为真正的北凉王，武道登顶",
                "chapter": "大结局"
            }
        }
    
    def _identify_themes_and_symbols(self):
        """识别主题和象征"""
        print("  🎭 分析主题象征...")
        
        self.themes = {
            "复仇与救赎": {
                "description": "徐凤年为母复仇的主线，以及最终在守护北凉中获得救赎",
                "key_events": ["京城白衣案", "韩貂寺之死", "拒北城之战"],
                "symbols": ["北凉刀", "母亲的剑"]
            },
            "成长与责任": {
                "description": "从纨绔世子到北凉王的蜕变，承担责任的过程",
                "key_events": ["游历江湖", "老黄之死", "世袭王位", "拒北城之战"],
                "symbols": ["王府", "铁甲"]
            },
            "江湖与庙堂": {
                "description": "个人武道追求与家国大义之间的冲突与融合",
                "key_events": ["李淳罡传剑", "武帝城之战", "最终归隐"],
                "symbols": ["剑", "王座"]
            },
            "情义与背叛": {
                "description": "兄弟情义、师徒情谊，以及政治中的背叛与忠诚",
                "key_events": ["温华断臂", "褚禄山忠心", "陈芝豹出走"],
                "symbols": ["酒", "书信"]
            }
        }
        
        self.symbols = {
            "北凉刀": {"meaning": "北凉王的权力象征，也是守护之责", 
                      "appearances": ["徐凤年世袭", "拒北城之战"], 
                      "related_chars": ["徐凤年", "徐骁"]},
            "桃花": {"meaning": "邓太阿的标志，也象征江湖儿女情长", 
                    "appearances": ["邓太阿出场", "武帝城之战"], 
                    "related_chars": ["邓太阿"]},
            "剑": {"meaning": "武道追求，李淳罡精神的传承", 
                  "appearances": ["李淳罡传剑", "徐凤年悟剑"], 
                  "related_chars": ["李淳罡", "徐凤年", "邓太阿"]},
            "铁甲": {"meaning": "北凉三十万铁甲，责任与牺牲", 
                    "appearances": ["大阅兵", "拒北城之战"], 
                    "related_chars": ["徐凤年", "褚禄山", "袁左宗"]}
        }
    
    def _build_quote_index(self):
        """构建精确引用索引"""
        print("  📇 构建引用索引...")
        
        key_concepts = {
            "徐凤年": [], "姜泥": [], "李淳罡": [], "王仙芝": [],
            "北凉": [], "离阳": [], "北莽": [],
            "剑": [], "刀": [], "武道": [],
            "报仇": [], "守护": [], "责任": []
        }
        
        for ch_idx, chapter in enumerate(self.chapters[:100]):
            content = chapter.get('content', '')
            ch_title = chapter.get('title', f'第{ch_idx+1}章')
            paragraphs = content.split('\n')
            
            for p_idx, para in enumerate(paragraphs):
                if len(para) < 50:
                    continue
                
                for concept in key_concepts:
                    if concept in para:
                        key_concepts[concept].append({
                            "chapter": ch_title,
                            "chapter_idx": ch_idx,
                            "paragraph_idx": p_idx,
                            "text": para[:200]
                        })
        
        for concept in key_concepts:
            key_concepts[concept] = key_concepts[concept][:10]
        
        self.quote_index = key_concepts
    
    def _print_stats(self):
        """打印统计信息"""
        print("\n📊 知识库统计:")
        print(f"   章节数: {len(self.chapters)}")
        print(f"   人物时间线: {len(self.character_timeline)} 人")
        total_events = sum(len(t) for t in self.character_timeline.values())
        print(f"   人物事件: {total_events} 条")
        print(f"   关键场景: {len(self.key_scenes)} 个")
        print(f"   因果事件: {len(self.plot_causes)} 个")
        print(f"   主题: {len(self.themes)} 个")
        print(f"   象征物: {len(self.symbols)} 个")
        print(f"   引用索引: {len(self.quote_index)} 个概念")
    
    # ==================== 查询接口 ====================
    
    def query_character_timeline(self, character: str) -> List[Dict]:
        """查询人物时间线"""
        return self.character_timeline.get(character, [])[:20]
    
    def query_plot_cause(self, event: str) -> Dict:
        """查询事件因果"""
        return self.plot_causes.get(event, {})
    
    def query_theme(self, theme_name: str) -> Dict:
        """查询主题"""
        return self.themes.get(theme_name, {})
    
    def query_quotes(self, keyword: str) -> List[Dict]:
        """查询原文引用"""
        return self.quote_index.get(keyword, [])
    
    # ==================== 保存接口 ====================
    
    def save_summaries(self, output_path: Path):
        """保存章节摘要"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.summaries, f, ensure_ascii=False, indent=2)
        print(f"💾 章节摘要已保存: {output_path}")
    
    def save_knowledge_base(self, output_path: Path):
        """保存专家知识库"""
        data = {
            "character_timeline": self.character_timeline,
            "character_traits": self.character_traits,
            "plot_causes": self.plot_causes,
            "key_scenes": self.key_scenes,
            "themes": self.themes,
            "symbols": self.symbols,
            "quote_index": self.quote_index
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 专家知识库已保存: {output_path}")


# 保持向后兼容的别名
ChapterSummarizer = KnowledgeBuilder
ExpertKnowledgeBase = KnowledgeBuilder

if __name__ == "__main__":
    data_dir = Path("data")
    
    # 加载小说
    print("📖 加载小说...")
    with open(data_dir / "雪中悍刀行.txt", 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 创建知识构建器
    builder = KnowledgeBuilder()
    
    # 解析章节
    chapters = builder.parse_chapters(text)
    
    # 生成摘要
    summaries = builder.generate_all_summaries()
    builder.save_summaries(data_dir / "chapter_summaries.json")
    
    # 构建专家知识库
    builder.build_expert_knowledge()
    builder.save_knowledge_base(data_dir / "knowledge_base.json")
    
    # 测试查询
    print("\n" + "="*60)
    print("🔍 测试查询")
    print("="*60)
    
    print("\n徐凤年的时间线（前3个事件）:")
    timeline = builder.query_character_timeline("徐凤年")
    for i, event in enumerate(timeline[:3], 1):
        print(f"  {i}. {event['chapter']}: {event['event'][:50]}...")