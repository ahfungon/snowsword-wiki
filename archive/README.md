# 归档说明

## deprecated_apps/
此目录包含已废弃的 app.py 历史版本，仅供备份参考。

### 文件列表
- `app_backup.py` - 早期备份版本
- `app_old.py` - 旧版本
- `app_v2.py` - 专家级百科版本（功能已合并到主 app.py）
- `app_enhanced.py` - 增强版（功能已合并到主 app.py）

### 整合说明
这些版本的功能已整合到根目录的 `app.py` 中：
- ✅ API 模式支持
- ✅ 智能缓存系统
- ✅ 健康检查接口
- ✅ 语义检索
- ✅ 知识图谱
- ✅ 深度分析
- ✅ 向量检索
- ✅ 章节摘要

## deprecated_src/
此目录包含已废弃的 src 模块历史版本。

### 文件列表
- `retriever.py` - 基础检索器（被 lightweight_retriever 替代）
- `semantic_retriever.py` / `semantic_retriever_v2.py` - 语义检索器（功能已合并）
- `enhanced_retriever.py` - 增强检索器（功能已合并）
- `enhanced_chat.py` - 增强对话模块（功能已合并）
- `chat.py` - 基础对话模块（被 expert_ai_v2 替代）
- `expert_ai.py` - 专家 AI 旧版本（被 expert_ai_v2 替代）
- `expert_retriever_v2.py` - 专家检索器（功能已合并）

### 保留的核心模块
当前 `src/` 目录保留以下模块：
- `expert_system_v2.py` - 专家系统主入口
- `expert_ai_v2.py` - 专家 AI 对话
- `lightweight_retriever.py` - 轻量级检索器
- `expert_kb.py` - 知识库构建
- `indexer.py` - 文本索引
- `vector_indexer.py` - 向量索引
- `knowledge_graph.py` - 知识图谱
- `chapter_summarizer.py` - 章节摘要
- `text_processor_v2.py` - 文本处理

## 重构时间
2026-02-11
