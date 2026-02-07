"""
检索模块：基于关键词和语义检索相关文本块
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from collections import Counter
import jieba

class TextRetriever:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.chunks: List[Dict] = []
        self.keyword_index: Dict = {}
        self._load_data()
    
    def _load_data(self):
        """加载索引数据，支持分块文件合并"""
        chunks_path = self.data_dir / "chunks.json"
        index_path = self.data_dir / "keyword_index.json"
        
        # 检查是否有分块文件
        split_files = sorted(self.data_dir.glob("chunks_part_*"))
        
        if not chunks_path.exists() and split_files:
            print(f"发现 {len(split_files)} 个分块文件，正在合并...")
            self._merge_split_files(split_files, chunks_path)
        
        if not chunks_path.exists():
            print("索引文件不存在，正在自动构建...")
            self._build_index()
        else:
            with open(chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    self.keyword_index = json.load(index_path)
            
            # 创建 id 到 chunk 的映射
            self.chunk_map = {chunk['id']: chunk for chunk in self.chunks}
            
            print(f"加载了 {len(self.chunks)} 个文本块")
    
    def _merge_split_files(self, split_files: List[Path], output_path: Path):
        """合并分块文件"""
        import subprocess
        
        # 使用 cat 命令合并（比 Python 循环更快）
        files_str = ' '.join([str(f) for f in split_files])
        cmd = f"cat {files_str} > {output_path}"
        subprocess.run(cmd, shell=True, check=True)
        
        print(f"合并完成: {output_path}")
    
    def _build_index(self):
        """自动构建索引"""
        from .indexer import TextIndexer
        
        text_file = self.data_dir / "雪中悍刀行.txt"
        if not text_file.exists():
            raise FileNotFoundError(f"找不到小说文本文件: {text_file}")
        
        print(f"开始构建索引，文本文件: {text_file}")
        indexer = TextIndexer(chunk_size=800, overlap=100)
        
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        self.chunks = indexer.create_chunks(text)
        
        # 保存索引
        chunks_path = self.data_dir / "chunks.json"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False)
        
        # 构建关键词索引
        self.keyword_index = self._build_keyword_index()
        index_path = self.data_dir / "keyword_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(self.keyword_index, f, ensure_ascii=False)
        
        # 创建映射
        self.chunk_map = {chunk['id']: chunk for chunk in self.chunks}
        
        print(f"索引构建完成！共 {len(self.chunks)} 个文本块")
    
    def _build_keyword_index(self) -> Dict:
        """构建关键词索引"""
        from collections import defaultdict
        
        index = defaultdict(list)
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '怎么', '吗', '呢', '吧'}
        
        for chunk in self.chunks:
            words = jieba.lcut(chunk['content'])
            for word in words:
                word = word.strip()
                if len(word) >= 2 and word not in stop_words:
                    index[word].append(chunk['id'])
        
        # 去重
        for word in index:
            index[word] = list(set(index[word]))
        
        return dict(index)
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        """
        # 使用 jieba 分词
        words = jieba.lcut(query)
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '怎么', '吗', '呢', '吧', '吗'}
        
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word)
        
        # 如果没有提取到有效关键词，保留原词
        if not keywords:
            keywords = [w for w in words if len(w.strip()) >= 2]
        
        return keywords
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索与查询最相关的文本块
        
        Args:
            query: 用户查询
            top_k: 返回最相关的 k 个结果
            
        Returns:
            List of relevant chunks with scores
        """
        if not self.chunks:
            return []
        
        # 提取查询关键词
        keywords = self.extract_keywords(query)
        
        if not keywords:
            return []
        
        # 计算每个块的相关性分数
        chunk_scores = Counter()
        
        # 1. 基于关键词索引匹配
        for keyword in keywords:
            # 精确匹配
            if keyword in self.keyword_index:
                for chunk_id in self.keyword_index[keyword]:
                    chunk_scores[chunk_id] += 3  # 索引匹配给高分
            
            # 模糊匹配（部分匹配）
            for idx, chunk in enumerate(self.chunks):
                content = chunk['content']
                chapter = chunk['chapter']
                
                # 关键词在内容中
                if keyword in content:
                    chunk_scores[chunk['id']] += 2
                
                # 关键词在章节标题中（更高权重）
                if keyword in chapter:
                    chunk_scores[chunk['id']] += 5
        
        # 2. 添加人物名和地名匹配（特殊处理常见角色名）
        important_names = [
            '徐凤年', '黄蛮儿', '徐龙象', '徐骁', '北凉王',
            '姜泥', '南宫仆射', '陈芝豹', '褚禄山', '袁左宗',
            '李淳罡', '邓太阿', '曹长卿', '王仙芝',
            '北凉', '离阳', '龙虎山', '武当山', '武帝城'
        ]
        
        for name in important_names:
            if name in query:
                for chunk in self.chunks:
                    if name in chunk['content'] or name in chunk['chapter']:
                        chunk_scores[chunk['id']] += 4
        
        # 3. 基于查询词的连续匹配（ bonus）
        for chunk in self.chunks:
            # 如果查询词完整出现在内容中，给额外加分
            if query in chunk['content']:
                chunk_scores[chunk['id']] += 10
        
        # 获取 Top K
        top_chunks = chunk_scores.most_common(top_k)
        
        results = []
        for chunk_id, score in top_chunks:
            if chunk_id in self.chunk_map:
                chunk = self.chunk_map[chunk_id].copy()
                chunk['relevance_score'] = score
                results.append(chunk)
        
        return results
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        获取检索结果的上下文文本（用于 Prompt）
        """
        results = self.retrieve(query, top_k=top_k)
        
        if not results:
            return "未找到相关内容。"
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"【参考段落 {i}】\n"
                f"章节：{result['chapter']}\n"
                f"内容：{result['content'][:500]}...\n"  # 限制长度避免过长
                f"相关度：{result['relevance_score']}\n"
            )
        
        return "\n---\n".join(context_parts)

if __name__ == "__main__":
    retriever = TextRetriever()
    
    # 测试查询
    test_queries = [
        "徐凤年是谁",
        "北凉王府在哪里",
        "黄蛮儿有什么能力"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("=" * 60)
        results = retriever.retrieve(query, top_k=3)
        for r in results:
            print(f"[{r['chapter']}] (score: {r['relevance_score']})")
            print(f"{r['content'][:200]}...")
            print()
