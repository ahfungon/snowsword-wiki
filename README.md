# 雪中悍刀行 - 智能百科问答系统

基于 DeepSeek 大模型的《雪中悍刀行》精准知识库问答系统。

## 特点

- 📚 **精准回答**：严格基于小说原文，零幻觉
- 🔍 **智能检索**：自动匹配最相关的原文段落
- 📖 **来源追溯**：每个答案都附带原文出处
- 🚀 **一键部署**：支持 Streamlit Cloud 免费部署

## 快速开始

### 本地运行

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 设置 DeepSeek API Key
```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

3. 运行应用
```bash
streamlit run app.py
```

### 在线部署

1. Fork 本仓库到 GitHub
2. 在 Streamlit Cloud 连接 GitHub 仓库
3. 在 Secrets 中添加 `DEEPSEEK_API_KEY`
4. 部署完成！

## 使用说明

在输入框中提问关于《雪中悍刀行》的问题，例如：
- "徐凤年是谁？"
- "北凉王府在哪里？"
- "黄蛮儿有什么特殊能力？"

系统会自动搜索相关原文，并基于原文生成精准回答。

## 技术架构

- **文本处理**：将小说分块建立索引
- **检索模块**：基于关键词和语义的混合检索
- **生成模块**：DeepSeek Chat API + 严格约束 Prompt
- **前端**：Streamlit

## 数据来源

《雪中悍刀行》完整文本（含番外）

## License

仅供学习研究使用
