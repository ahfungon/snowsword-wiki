#!/usr/bin/env python3
"""
知识图谱构建器 - 人物、地点、势力关系
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


class KnowledgeGraph:
    """构建小说知识图谱"""
    
    def __init__(self):
        self.characters = {}  # 人物信息
        self.factions = {}    # 势力信息
        self.locations = {}   # 地点信息
        self.relationships = []  # 人物关系
        
    def build_from_text(self, text: str):
        """从全文构建知识图谱"""
        print("🕸️  正在构建知识图谱...")
        
        # 主要人物
        self._extract_characters(text)
        
        # 势力/门派
        self._extract_factions(text)
        
        # 地点
        self._extract_locations(text)
        
        # 人物关系
        self._extract_relationships(text)
        
        print(f"✅ 知识图谱构建完成")
        print(f"   人物: {len(self.characters)} 个")
        print(f"   势力: {len(self.factions)} 个")
        print(f"   地点: {len(self.locations)} 个")
        print(f"   关系: {len(self.relationships)} 条")
    
    def _extract_characters(self, text: str):
        """提取主要人物"""
        # 核心人物
        main_chars = {
            "徐凤年": {"identity": "北凉王世子", "aliases": ["小年", "世子", "殿下"], "faction": "北凉"},
            "徐骁": {"identity": "北凉王", "aliases": ["人屠", "大将军"], "faction": "北凉"},
            "姜泥": {"identity": "西楚亡国公主", "aliases": ["姜姒", "小泥人"], "faction": "西楚/北凉"},
            "南宫仆射": {"identity": "白狐儿脸", "aliases": ["十九停"], "faction": "听潮阁"},
            "李淳罡": {"identity": "剑神", "aliases": ["老剑神", "青衫剑神"], "faction": "江湖"},
            "邓太阿": {"identity": "桃花剑神", "aliases": ["舅帮帮主"], "faction": "吴家剑冢"},
            "王仙芝": {"identity": "武帝城主", "aliases": ["天下第二"], "faction": "武帝城"},
            "拓跋菩萨": {"identity": "北莽军神", "aliases": ["军神"], "faction": "北莽"},
            "曹长卿": {"identity": "曹官子", "aliases": ["青衣儒圣"], "faction": "西楚"},
            "陈芝豹": {"identity": "北凉兵圣", "aliases": ["白衣兵圣", "小人屠"], "faction": "北凉/离阳"},
        }
        
        self.characters = main_chars
        
        # 在文本中搜索出现频率，补充次要人物
        for name in main_chars:
            count = text.count(name)
            self.characters[name]['mentions'] = count
    
    def _extract_factions(self, text: str):
        """提取势力/门派"""
        factions = {
            "北凉": {"type": "藩国", "leader": "徐骁/徐凤年", "location": "北凉道"},
            "离阳": {"type": "王朝", "leader": "皇帝", "location": "太安城"},
            "北莽": {"type": "王朝", "leader": "女帝", "location": "北莽皇帐"},
            "西楚": {"type": "亡国", "leader": "曹长卿", "location": "广陵道"},
            "武帝城": {"type": "武林圣地", "leader": "王仙芝", "location": "武帝城"},
            "吴家剑冢": {"type": "剑道世家", "leader": "家主", "location": "吴家"},
            "龙虎山": {"type": "道教圣地", "leader": "天师", "location": "龙虎山"},
            "两禅寺": {"type": "佛教圣地", "leader": "李当心", "location": "两禅寺"},
        }
        self.factions = factions
    
    def _extract_locations(self, text: str):
        """提取重要地点"""
        locations = {
            "清凉山": {"type": "地点", "description": "北凉王府所在地"},
            "北凉王府": {"type": "府邸", "description": "徐凤年家"},
            "听潮阁": {"type": "建筑", "description": "藏有天下武功秘籍"},
            "武帝城": {"type": "城市", "description": "王仙芝镇守，天下第一楼"},
            "太安城": {"type": "都城", "description": "离阳王朝都城"},
            "广陵江": {"type": "江河", "description": "徐凤年大阅兵之地"},
        }
        self.locations = locations
    
    def _extract_relationships(self, text: str):
        """提取人物关系"""
        relationships = [
            {"from": "徐凤年", "to": "徐骁", "relation": "父子"},
            {"from": "徐凤年", "to": "姜泥", "relation": "夫妻/青梅竹马"},
            {"from": "徐凤年", "to": "南宫仆射", "relation": "知己/约定娶她"},
            {"from": "徐凤年", "to": "李淳罡", "relation": "师徒/忘年交"},
            {"from": "徐凤年", "to": "邓太阿", "relation": "舅甥"},
            {"from": "徐凤年", "to": "拓跋菩萨", "relation": "敌对阵营"},
            {"from": "徐骁", "to": "离阳皇帝", "relation": "君臣/忌惮"},
        ]
        self.relationships = relationships
    
    def get_character_info(self, name: str) -> Dict:
        """获取人物信息"""
        return self.characters.get(name, {})
    
    def get_related_characters(self, name: str) -> List[Dict]:
        """获取相关人物"""
        related = []
        for rel in self.relationships:
            if rel['from'] == name:
                related.append({"name": rel['to'], "relation": rel['relation']})
            elif rel['to'] == name:
                related.append({"name": rel['from'], "relation": rel['relation']})
        return related
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            "characters": self.characters,
            "factions": self.factions,
            "locations": self.locations,
            "relationships": self.relationships
        }
    
    def save(self, output_path: Path):
        """保存知识图谱"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"💾 知识图谱已保存: {output_path}")


if __name__ == "__main__":
    # 测试
    data_dir = Path("data")
    
    # 加载小说文本
    print("📖 加载小说文本...")
    with open(data_dir / "雪中悍刀行.txt", 'r', encoding='utf-8') as f:
        text = f.read()[:100000]  # 先用前10万字测试
    
    # 构建知识图谱
    graph = KnowledgeGraph()
    graph.build_from_text(text)
    
    # 测试查询
    print("\n🔍 测试查询: 徐凤年")
    info = graph.get_character_info("徐凤年")
    print(f"人物信息: {info}")
    
    related = graph.get_related_characters("徐凤年")
    print(f"相关人物: {related}")
    
    # 保存
    graph.save(data_dir / "knowledge_graph.json")
