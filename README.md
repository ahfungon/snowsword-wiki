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

#### 方式 1：一键脚本（推荐）

```bash
# 1. 进入项目目录
cd snowsword-wiki

# 2. 执行部署脚本
./deploy.sh
```

脚本会自动：
- 检查并安装 GitHub CLI
- 登录 GitHub（如未登录）
- 创建 GitHub 仓库
- 推送代码

#### 方式 2：手动部署

**步骤 1：创建 GitHub 仓库**
```bash
# 使用 GitHub CLI
gh repo create ahfungon/snowsword-wiki --public --source=. --remote=origin --push

# 或使用网页 https://github.com/new 创建后推送
git remote add origin https://github.com/ahfungon/snowsword-wiki.git
git push -u origin main
```

**步骤 2：部署到 Streamlit Cloud**

1. 访问 https://streamlit.io/cloud
2. 使用 GitHub 登录
3. 点击 **New app**
4. 选择仓库：`ahfungon/snowsword-wiki`
5. 主文件路径：`app.py`
6. 点击 **Advanced settings** → **Secrets**
7. 添加：
   ```
   DEEPSEEK_API_KEY = "sk-cdebe0fafcf9406d962e3e09a0404e4b"
   ```
8. 点击 **Deploy**

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
