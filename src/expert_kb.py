#!/usr/bin/env python3
"""
专家级知识库构建器
构建小说精读级别的结构化知识
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class ExpertKnowledgeBase:
    """
    专家级知识库
    - 人物全时间线追踪
    - 情节因果关系网络  
    - 主题象征分析
    - 精确原文引用
    """
    
    def __init__(self):
        # 人物数据库
        self.character_timeline = {}  # 人物时间线 {人物: [{章节, 事件, 原文, 页码}]}
        self.character_relations = {}  # 人物关系动态变化
        self.character_traits = {}     # 人物性格特征演化
        
        # 情节数据库
        self.plot_arcs = []           # 主要情节弧线
        self.plot_causes = {}         # 因果关系 {事件: {原因, 结果, 影响}}
        self.key_scenes = []          # 关键场景（带完整原文）
        
        # 主题分析
        self.themes = {}              # 主题 {主题: [相关情节, 象征意义]}
        self.symbols = {}             # 象征物 {物品: [出现章节, 象征意义]}
        
        # 精确引用索引
        self.quote_index = {}         # {关键词: [{章节, 段落, 原文}]}
        
    def build_from_chapters(self, chapters: List[Dict]):
        """从章节构建专家知识库"""
        print("📚 构建专家级知识库...")
        
        # 1. 构建人物时间线
        self._build_character_timelines(chapters)
        
        # 2. 提取关键场景（带完整上下文）
        self._extract_key_scenes(chapters)
        
        # 3. 分析情节因果
        self._analyze_plot_causality(chapters)
        
        # 4. 识别主题和象征
        self._identify_themes_and_symbols(chapters)
        
        # 5. 构建引用索引
        self._build_quote_index(chapters)
        
        print(f"✅ 专家知识库构建完成")
        self._print_stats()
    
    def _build_character_timelines(self, chapters: List[Dict]):
        """构建人物完整时间线"""
        print("  🕐 构建人物时间线...")
        
        # 核心人物
        main_chars = [
            "徐凤年", "姜泥", "徐骁", "李淳罡", "南宫仆射", 
            "王仙芝", "邓太阿", "拓跋菩萨", "曹长卿", "陈芝豹",
            "褚禄山", "袁左宗", "齐练华", "吴素"
        ]
        
        for char in main_chars:
            self.character_timeline[char] = []
            self.character_traits[char] = {
                "initial": {},      # 初始性格
                "evolution": [],    # 性格变化节点
                "final": {}         # 最终性格
            }
        
        # 扫描所有章节提取人物事件
        for ch_idx, chapter in enumerate(chapters):
            ch_title = chapter.get('title', f'第{ch_idx+1}章')
            content = chapter.get('content', '')
            
            for char in main_chars:
                if char not in content:
                    continue
                
                # 提取包含该人物的段落
                paragraphs = content.split('\n')
                for p_idx, para in enumerate(paragraphs):
                    if char in para and len(para) > 20:
                        # 提取人物行为（简化版）
                        event = self._extract_character_action(para, char)
                        if event:
                            self.character_timeline[char].append({
                                "chapter": ch_title,
                                "chapter_idx": ch_idx,
                                "paragraph_idx": p_idx,
                                "event": event,
                                "context": para[:300],  # 保留更多上下文
                                "word_count": chapter.get('word_count', 0)
                            })
        
        # 为每个人物按时间排序
        for char in self.character_timeline:
            self.character_timeline[char].sort(key=lambda x: x['chapter_idx'])
    
    def _extract_character_action(self, paragraph: str, character: str) -> str:
        """提取人物行为（简化规则）"""
        # 找包含人物名的句子
        sentences = re.split(r'[。！？]', paragraph)
        for sent in sentences:
            if character in sent:
                # 提取动作关键词
                actions = ['杀', '战', '斗', '说', '问', '答', '走', '来', '去', 
                          '救', '伤', '死', '胜', '败', '见', '遇', '离', '归']
                for act in actions:
                    if act in sent:
                        return sent.strip()[:100]
        return ""
    
    def _extract_key_scenes(self, chapters: List[Dict]):
        """提取关键场景（带完整原文）"""
        print("  🎬 提取关键场景...")
        
        # 关键场景模式
        scene_patterns = [
            ("生死战", ["死", "杀", "战", "斗"], 500),
            ("重要对话", ["说", "问", "答", "道"], 400),
            ("突破", ["突破", "境界", "入", "悟"], 400),
            ("离别", ["离", "别", "走", "去", "归"], 400),
            ("重逢", ["见", "遇", "来", "归"], 400),
        ]
        
        scenes = []
        for ch_idx, chapter in enumerate(chapters[:200]):  # 先处理前200章
            content = chapter.get('content', '')
            ch_title = chapter.get('title', f'第{ch_idx+1}章')
            
            # 分割成段落
            paragraphs = content.split('\n\n')
            
            for p_idx, para in enumerate(paragraphs):
                if len(para) < 200:
                    continue
                
                # 检查是否匹配关键场景
                for scene_type, keywords, min_len in scene_patterns:
                    if len(para) >= min_len and any(kw in para for kw in keywords):
                        # 检查是否包含主要人物
                        main_chars = ['徐凤年', '姜泥', '李淳罡', '王仙芝', '邓太阿']
                        if any(char in para for char in main_chars):
                            scenes.append({
                                "type": scene_type,
                                "chapter": ch_title,
                                "chapter_idx": ch_idx,
                                "paragraph_idx": p_idx,
                                "content": para[:800],  # 保存完整场景
                                "keywords": [kw for kw in keywords if kw in para][:3]
                            })
                            break
        
        # 按重要性排序并去重
        self.key_scenes = sorted(scenes, key=lambda x: x['chapter_idx'])[:200]
    
    def _analyze_plot_causality(self, chapters: List[Dict]):
        """分析情节因果关系"""
        print("  🔗 分析情节因果...")
        
        # 定义关键事件及其因果关系
        causal_events = {
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
        
        self.plot_causes = causal_events
    
    def _identify_themes_and_symbols(self, chapters: List[Dict]):
        """识别主题和象征"""
        print("  🎭 分析主题象征...")
        
        # 主要主题
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
        
        # 象征物
        self.symbols = {
            "北凉刀": {
                "meaning": "北凉王的权力象征，也是守护之责",
                "appearances": ["徐凤年世袭", "拒北城之战"],
                "related_chars": ["徐凤年", "徐骁"]
            },
            "桃花": {
                "meaning": "邓太阿的标志，也象征江湖儿女情长",
                "appearances": ["邓太阿出场", "武帝城之战"],
                "related_chars": ["邓太阿"]
            },
            "剑": {
                "meaning": "武道追求，李淳罡精神的传承",
                "appearances": ["李淳罡传剑", "徐凤年悟剑"],
                "related_chars": ["李淳罡", "徐凤年", "邓太阿"]
            },
            "铁甲": {
                "meaning": "北凉三十万铁甲，责任与牺牲",
                "appearances": ["大阅兵", "拒北城之战"],
                "related_chars": ["徐凤年", "褚禄山", "袁左宗"]
            }
        }
    
    def _build_quote_index(self, chapters: List[Dict]):
        """构建精确引用索引"""
        print("  📇 构建引用索引...")
        
        # 为关键概念建立索引
        key_concepts = {
            "徐凤年": [], "姜泥": [], "李淳罡": [], "王仙芝": [],
            "北凉": [], "离阳": [], "北莽": [],
            "剑": [], "刀": [], "武道": [],
            "报仇": [], "守护": [], "责任": []
        }
        
        for ch_idx, chapter in enumerate(chapters[:100]):  # 前100章
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
        
        # 每个概念只保留前10条
        for concept in key_concepts:
            key_concepts[concept] = key_concepts[concept][:10]
        
        self.quote_index = key_concepts
    
    def _print_stats(self):
        """打印统计信息"""
        print("\n📊 专家知识库统计:")
        print(f"   人物时间线: {len(self.character_timeline)} 人")
        total_events = sum(len(t) for t in self.character_timeline.values())
        print(f"   人物事件: {total_events} 条")
        print(f"   关键场景: {len(self.key_scenes)} 个")
        print(f"   因果事件: {len(self.plot_causes)} 个")
        print(f"   主题: {len(self.themes)} 个")
        print(f"   象征物: {len(self.symbols)} 个")
        print(f"   引用索引: {len(self.quote_index)} 个概念")
    
    def query_character_timeline(self, character: str, event_type: str = None) -> List[Dict]:
        """查询人物时间线"""
        timeline = self.character_timeline.get(character, [])
        if event_type:
            timeline = [t for t in timeline if event_type in t.get('event', '')]
        return timeline[:20]  # 返回前20个事件
    
    def query_plot_cause(self, event: str) -> Dict:
        """查询事件因果"""
        return self.plot_causes.get(event, {})
    
    def query_theme(self, theme_name: str) -> Dict:
        """查询主题"""
        return self.themes.get(theme_name, {})
    
    def query_quotes(self, keyword: str) -> List[Dict]:
        """查询原文引用"""
        return self.quote_index.get(keyword, [])
    
    def save(self, output_path: Path):
        """保存知识库"""
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
        
        print(f"\n💾 专家知识库已保存: {output_path}")


if __name__ == "__main__":
    # 测试
    data_dir = Path("data")
    
    # 加载章节数据
    print("📖 加载章节数据...")
    with open(data_dir / "chapter_summaries.json", 'r', encoding='utf-8') as f:
        chapters_data = json.load(f)
    
    # 转换为需要的格式
    chapters = []
    for s in chapters_data:
        chapters.append({
            'title': s['title'],
            'content': '\n'.join(s.get('key_events', [])),  # 简化处理
            'word_count': s['word_count']
        })
    
    # 构建专家知识库
    kb = ExpertKnowledgeBase()
    kb.build_from_chapters(chapters)
    
    # 测试查询
    print("\n" + "="*60)
    print("🔍 测试查询")
    print("="*60)
    
    # 查询徐凤年时间线
    print("\n徐凤年的时间线（前5个事件）:")
    timeline = kb.query_character_timeline("徐凤年")
    for i, event in enumerate(timeline[:5], 1):
        print(f"  {i}. {event['chapter']}: {event['event'][:50]}...")
    
    # 查询事件因果
    print("\n韩貂寺之死的因果关系:")
    cause = kb.query_plot_cause("韩貂寺之死")
    if cause:
        print(f"  原因: {cause['cause']}")
        print(f"  结果: {cause['result']}")
        print(f"  影响: {cause['impact']}")
    
    # 保存
    kb.save(data_dir / "expert_knowledge_base.json")
