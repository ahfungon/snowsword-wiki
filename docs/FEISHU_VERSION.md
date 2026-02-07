# 《雪中悍刀行》智能百科 - 项目实施方案

## 一、项目目标
构建**专家级AI问答系统**，实现：
- 深度理解小说内容，超越关键词匹配
- 具备文学评论家级别的分析能力
- 能回答复杂的人物关系、情节因果、主题象征问题

## 二、当前状态
| 状态 | 内容 |
|------|------|
| ✅ 已完成 | 基础问答、初步知识图谱(14人/3658事件)、专家级提示词 |
| ❌ 待优化 | 知识库深度不足、检索粒度粗、缺乏动态关系网络 |

## 三、技术架构（4层）

```
数据处理层(HanLP) 
    ↓
知识管理层(Neo4j + 向量库)
    ↓
应用服务层(专家AI)
    ↓
用户交互层(Streamlit)
```

### 核心组件
| 层级 | 技术选型 | 用途 |
|------|----------|------|
| 数据处理 | HanLP / BGE | NER抽取、语义嵌入 |
| 知识存储 | Neo4j + ChromaDB | 关系网络、向量检索 |
| 应用服务 | DeepSeek API | 专家级回答生成 |
| 用户界面 | Streamlit | Web交互 |

## 四、实施计划（4周）

### Week 1: 基础重构
**目标**: 用完整原文重建知识库
- Day 1-2: 集成HanLP，实现NER和关系抽取
- Day 3-4: 集成BGE，实现语义向量检索
- Day 5-7: 事件抽取（人物、对话、场景）

**交付物**: `text_processor.py`, `semantic_retriever.py`, `events.json`

### Week 2: 知识图谱
**目标**: 构建动态人物关系网络
- Day 1-2: 人物关系网络（亲属、师徒、敌对）
- Day 3-4: 情节因果图（伏笔、多线叙事）
- Day 5-7: Neo4j集成，图谱可视化

**交付物**: `knowledge_graph_v2.py`, `graph_visualizer.py`

### Week 3: 专家系统
**目标**: 实现专家级问答
- Day 1-2: 混合检索（语义+图谱）
- Day 3-4: 主题分析（强度曲线、象征追踪）
- Day 5-7: 回答优化（三段式结构、引用溯源）

**交付物**: `expert_ai_v2.py`, `hybrid_retriever.py`

### Week 4: 优化部署
**目标**: 性能优化，稳定上线
- Day 1-2: 性能优化（索引量化、缓存）
- Day 3-4: 界面优化（可视化、移动端）
- Day 5-7: 测试部署（单元测试、压力测试）

**交付物**: `app_v2.py`, 测试套件, 部署文档

## 五、技术选型详情

### 核心依赖
```
hanlp>=2.1.0              # 中文NLP
sentence-transformers     # Embedding
chromadb>=0.4.0          # 向量数据库
neo4j>=5.0.0             # 图数据库
streamlit>=1.28.0        # Web界面
```

### 模型选择
| 用途 | 模型 | 部署方式 |
|------|------|----------|
| NER/关系 | HanLP | 本地 |
| Embedding | BAAI/bge-large-zh | 本地(1.3GB) |
| 问答 | DeepSeek-V3 | API |

## 六、评估指标

### 检索质量
- 召回率@10: >80%
- 精确率@5: >60%

### 回答质量（人工评估）
- 准确性: >85%
- 深度: >75%
- 可追溯: >90%

### 性能
- 响应时间: <3秒
- 并发: >10 QPS

## 七、待决策事项

需要项目负责人确认：

1. **Embedding模型**
   - A. BGE-large-zh (效果好, 1.3GB)
   - B. BGE-base-zh (轻量, 400MB)

2. **图数据库**
   - A. Neo4j (功能完整, 需Docker)
   - B. NetworkX (轻量, JSON存储)

3. **向量数据库**
   - A. ChromaDB (简单, 嵌入式)
   - B. FAISS (性能更好)

4. **大模型**
   - A. DeepSeek API (按量付费)
   - B. ChatGLM3-6B本地 (一次性投入, 需12GB显存)

## 八、参考资料

### 开源项目
- HanLP: https://github.com/hankcs/HanLP
- LlamaIndex: https://github.com/jerryjliu/llama_index
- BGE: https://github.com/FlagOpen/FlagEmbedding

### 竞品参考
- SparkNotes: https://www.sparknotes.com/
- Shmoop: https://www.shmoop.com/
- AWoIaF: https://awoiaf.westeros.org/

---

**文档版本**: v1.0
**创建日期**: 2026-02-07
**文档路径**: `docs/IMPLEMENTATION_PLAN.md`
