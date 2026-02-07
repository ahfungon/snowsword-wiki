#!/usr/bin/env python3
"""
文本处理器 V2 (轻量版) - 不依赖大模型
使用规则 + 自定义词典实现NER
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessorV2:
    """
    轻量版文本处理器
    - 智能分块
    - 规则-based NER
    - 场景检测
    - 事件抽取
    """
    
    def __init__(self):
        # 核心人物词典（可扩展）
        self.characters = {
            '徐凤年', '姜泥', '徐骁', '李淳罡', '南宫仆射', 
            '王仙芝', '邓太阿', '拓跋菩萨', '曹长卿', '陈芝豹',
            '褚禄山', '袁左宗', '齐练华', '吴素', '徐龙象',
            '温华', '呵呵姑娘', '徐婴', '韩貂寺', '赵楷',
            '红薯', '青鸟', '老黄', '魏叔阳'
        }
        
        # 地点词典
        self.locations = {
            '北凉', '离阳', '太安城', '武帝城', '清凉山', 
            '北莽', '广陵江', '西楚', '两禅寺', '龙虎山',
            '听潮阁', '北凉王府', '武当山', '吴家剑冢'
        }
        
        # 武功/势力
        self.techniques = {
            '两袖青蛇', '剑开天门', '一剑仙人跪', '指玄',
            '天象', '金刚', '陆地神仙', '大黄庭', '龙象波若功'
        }
        
        self.organizations = {
            '北凉王府', '听潮阁', '吴家剑冢', '不良人',
            '离阳王朝', '北莽皇帐', '西楚', '两禅寺', '龙虎山'
        }
    
    def split_into_paragraphs(self, text: str) -> List[Dict]:
        """将文本分割成段落，保留章节结构"""
        paragraphs = []
        current_chapter = "未知章节"
        
        lines = text.split('\n')
        current_para = []
        para_idx = 0
        chapter_idx = 0
        
        for line in lines:
            line = line.strip()
            
            # 识别章节标题
            chapter_match = re.match(r'(第[一二三四五六七八九十百千万零\d]+章)\s*(.+)?', line)
            if chapter_match:
                # 保存之前的段落
                if current_para:
                    paragraphs.append({
                        'chapter': current_chapter,
                        'chapter_idx': chapter_idx,
                        'paragraph_idx': para_idx,
                        'content': '\n'.join(current_para),
                        'length': len(''.join(current_para))
                    })
                    para_idx += 1
                    current_para = []
                
                current_chapter = line
                chapter_idx += 1
                continue
            
            # 收集段落内容
            if line and len(line) > 5:
                current_para.append(line)
                
                # 段落长度超过300字或遇到空行，保存
                if len(''.join(current_para)) > 300:
                    paragraphs.append({
                        'chapter': current_chapter,
                        'chapter_idx': chapter_idx,
                        'paragraph_idx': para_idx,
                        'content': '\n'.join(current_para),
                        'length': len(''.join(current_para))
                    })
                    para_idx += 1
                    current_para = []
        
        # 保存最后一个段落
        if current_para:
            paragraphs.append({
                'chapter': current_chapter,
                'chapter_idx': chapter_idx,
                'paragraph_idx': para_idx,
                'content': '\n'.join(current_para),
                'length': len(''.join(current_para))
            })
        
        return paragraphs
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取命名实体（基于词典匹配）"""
        entities = {
            '人物': [],
            '地点': [],
            '武功': [],
            '势力': []
        }
        
        # 匹配人物
        for char in self.characters:
            if char in text:
                entities['人物'].append(char)
        
        # 匹配地点
        for loc in self.locations:
            if loc in text:
                entities['地点'].append(loc)
        
        # 匹配武功
        for tech in self.techniques:
            if tech in text:
                entities['武功'].append(tech)
        
        # 匹配势力
        for org in self.organizations:
            if org in text:
                entities['势力'].append(org)
        
        # 去重
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def detect_scene_type(self, text: str) -> str:
        """检测场景类型"""
        # 战斗场景
        battle_kw = ['战', '斗', '杀', '刀', '剑', '拳', '掌', '死', '血', '伤']
        battle_score = sum(1 for kw in battle_kw if kw in text)
        
        # 对话场景
        dialogue_kw = ['说', '道', '问', '答', '曰', '"', '"', '「', '」']
        dialogue_score = sum(1 for kw in dialogue_kw if kw in text)
        
        # 心理场景
        mental_kw = ['想', '觉得', '感觉', '心中', '暗道', '暗想']
        mental_score = sum(1 for kw in mental_kw if kw in text)
        
        scores = {'战斗': battle_score, '对话': dialogue_score, '心理': mental_score, '叙事': 0}
        
        if max(scores.values()) == 0:
            return '叙事'
        return max(scores, key=scores.get)
    
    def extract_dialogues(self, text: str) -> List[Dict]:
        """提取对话内容"""
        dialogues = []
        
        # 匹配引号内容
        patterns = [
            r'[""]([^""]{10,200})[""]',  # 中文引号
            r'「([^」]{10,200})」',       # 日式引号
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 找到说话人（简单的就近匹配）
                speaker = None
                before = text[:text.find(match)]
                for char in self.characters:
                    if char in before[-50:]:  # 往前50字找
                        speaker = char
                        break
                
                dialogues.append({
                    'speaker': speaker,
                    'content': match,
                    'length': len(match)
                })
        
        return dialogues
    
    def extract_events(self, paragraph: Dict) -> List[Dict]:
        """从段落中提取事件"""
        text = paragraph['content']
        events = []
        entities = self.extract_entities(text)
        scene_type = self.detect_scene_type(text)
        
        # 提取对话事件
        if scene_type == '对话':
            dialogues = self.extract_dialogues(text)
            for dia in dialogues:
                if dia['speaker']:
                    events.append({
                        'type': '对话',
                        'character': dia['speaker'],
                        'content': dia['content'][:100],
                        'chapter': paragraph['chapter'],
                        'chapter_idx': paragraph['chapter_idx'],
                        'paragraph_idx': paragraph['paragraph_idx']
                    })
        
        # 提取战斗/互动事件
        elif scene_type == '战斗':
            chars = entities.get('人物', [])
            if len(chars) >= 2:
                events.append({
                    'type': '战斗/互动',
                    'characters': chars[:3],
                    'location': entities.get('地点', ['未知'])[0] if entities.get('地点') else '未知',
                    'context': text[:150],
                    'chapter': paragraph['chapter'],
                    'chapter_idx': paragraph['chapter_idx'],
                    'paragraph_idx': paragraph['paragraph_idx']
                })
        
        return events
    
    def process_novel(self, text_path: Path, output_dir: Path):
        """处理整本小说"""
        logger.info(f"📖 处理小说: {text_path}")
        
        # 读取
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"   文本长度: {len(text):,} 字符")
        
        # 1. 分割段落
        logger.info("✂️  分割段落...")
        paragraphs = self.split_into_paragraphs(text)
        
        # 2. 提取信息
        logger.info("🔍 提取实体和事件...")
        all_entities = []
        all_events = []
        
        for i, para in enumerate(paragraphs):
            if (i + 1) % 1000 == 0:
                logger.info(f"   进度: {i+1}/{len(paragraphs)}")
            
            # 实体
            entities = self.extract_entities(para['content'])
            if any(entities.values()):
                all_entities.append({
                    'paragraph_idx': i,
                    **para,
                    'entities': entities
                })
            
            # 事件
            events = self.extract_events(para)
            all_events.extend(events)
        
        # 3. 保存
        output_dir.mkdir(exist_ok=True, parents=True)
        
        with open(output_dir / 'paragraphs_v2.json', 'w', encoding='utf-8') as f:
            json.dump(paragraphs, f, ensure_ascii=False, indent=2)
        
        with open(output_dir / 'entities_v2.json', 'w', encoding='utf-8') as f:
            json.dump(all_entities, f, ensure_ascii=False, indent=2)
        
        with open(output_dir / 'events_v2.json', 'w', encoding='utf-8') as f:
            json.dump(all_events, f, ensure_ascii=False, indent=2)
        
        # 4. 统计
        stats = {
            'paragraphs': len(paragraphs),
            'entities_records': len(all_entities),
            'events': len(all_events),
            'character_mentions': sum(len(e['entities'].get('人物', [])) for e in all_entities),
            'dialogues': len([e for e in all_events if e['type'] == '对话']),
            'battles': len([e for e in all_events if e['type'] == '战斗/互动'])
        }
        
        with open(output_dir / 'stats_v2.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ 处理完成:")
        for key, val in stats.items():
            logger.info(f"   {key}: {val:,}")
        
        return stats


if __name__ == "__main__":
    # 快速测试
    print("🧪 测试轻量版文本处理器")
    
    processor = TextProcessorV2()
    
    test_text = """
第一章 小二上酒

徐凤年站在北凉王府门口，望着远处的清凉山。

"小二，上酒！"徐凤年大声喊道。

姜泥从旁边走过，冷冷地看了他一眼。

徐凤年笑道："小泥人，一起去喝酒？"

姜泥哼了一声，转身就走。

第二章 白狐儿脸

南宫仆射来到听潮阁，要找徐凤年比试剑法。
"""
    
    # 测试
    paragraphs = processor.split_into_paragraphs(test_text)
    print(f"\n段落数: {len(paragraphs)}")
    
    for i, p in enumerate(paragraphs[:3]):
        print(f"\n段落 {i+1}:")
        print(f"  章节: {p['chapter']}")
        print(f"  内容: {p['content'][:50]}...")
        
        entities = processor.extract_entities(p['content'])
        if any(entities.values()):
            print(f"  实体: {entities}")
        
        scene = processor.detect_scene_type(p['content'])
        print(f"  场景: {scene}")
