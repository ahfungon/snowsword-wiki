# 代码重构记录

## 重构时间
2026-02-11

## 重构目标
整合分散的 app.py 多个版本，统一代码架构，减少重复模块。

## 重构内容

### 1. app.py 版本整合 ✅

**问题**：存在 5 个 app.py 版本，功能分散
- `app.py` (440行) - 主版本
- `app_v2.py` (224行) - 专家级百科
- `app_enhanced.py` (214行) - 增强版
- `app_backup.py` (219行) - 备份
- `app_old.py` (219行) - 旧版本

**解决方案**：
- 保留 `app.py` 作为主版本（功能最完整）
- 将 `app_v2.py` 和 `app_enhanced.py` 的功能整合到 `app.py`
- 废弃版本移至 `archive/deprecated_apps/`

**整合功能**：
- ✅ API 模式支持 (GET/POST)
- ✅ 智能缓存系统 (TTL + LRU)
- ✅ 健康检查接口 (/health, /stats)
- ✅ 语义检索
- ✅ 知识图谱
- ✅ 深度分析
- ✅ 向量检索
- ✅ 章节摘要

### 2. src/ 模块清理 ✅

**问题**：存在 16 个模块，大量重复功能

**解决方案**：
- 保留核心模块（9个）
- 废弃模块移至 `archive/deprecated_src/`

**保留模块**：
- `expert_system_v2.py` - 专家系统主入口
- `expert_ai_v2.py` - 专家 AI 对话
- `lightweight_retriever.py` - 轻量级检索器
- `expert_kb.py` - 知识库构建
- `indexer.py` - 文本索引
- `vector_indexer.py` - 向量索引
- `knowledge_graph.py` - 知识图谱
- `chapter_summarizer.py` - 章节摘要
- `text_processor_v2.py` - 文本处理

**废弃模块**：
- `retriever.py` - 功能被 lightweight_retriever 替代
- `semantic_retriever.py` / `semantic_retriever_v2.py` - 功能整合
- `enhanced_retriever.py` - 功能整合
- `enhanced_chat.py` - 功能整合
- `chat.py` - 被 expert_ai_v2 替代
- `expert_ai.py` - 被 expert_ai_v2 替代
- `expert_retriever_v2.py` - 功能整合

## 目录结构

```
snowsword-wiki/
├── app.py                    # 主应用（统一入口）
├── api.py                    # API 接口
├── build_index.py            # 索引构建
├── archive/                  # 归档目录
│   ├── README.md
│   ├── deprecated_apps/      # 废弃的 app 版本
│   └── deprecated_src/       # 废弃的 src 模块
├── src/                      # 核心模块（精简后）
│   ├── expert_system_v2.py
│   ├── expert_ai_v2.py
│   ├── lightweight_retriever.py
│   ├── expert_kb.py
│   ├── indexer.py
│   ├── vector_indexer.py
│   ├── knowledge_graph.py
│   ├── chapter_summarizer.py
│   └── text_processor_v2.py
└── data/                     # 数据目录
```

## 后续计划

- [ ] 进一步整合 src/ 中的重复逻辑
- [ ] 添加单元测试
- [ ] 优化缓存持久化（考虑 Redis）
- [ ] 添加性能监控
- [ ] 完善文档
