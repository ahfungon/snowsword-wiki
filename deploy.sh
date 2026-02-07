#!/bin/bash
# 雪中悍刀行 Wiki - 一键部署脚本
# 用法: ./deploy.sh YOUR_DEEPSEEK_API_KEY

set -e

API_KEY=$1

if [ -z "$API_KEY" ]; then
    echo "❌ 错误: 请提供 DeepSeek API Key"
    echo "用法: ./deploy.sh sk-xxxxxxxxxxxxxxxx"
    exit 1
fi

echo "🚀 开始部署雪中悍刀行 Wiki..."
echo ""

# 1. 创建 GitHub 仓库
echo "📦 创建 GitHub 仓库..."
cd /Users/ahfun/.openclaw/workspace/snowsword-wiki

gh repo create ahfungon/snowsword-wiki --public --source=. --remote=origin --push || {
    echo "⚠️ 仓库可能已存在，尝试直接推送..."
    git remote add origin https://github.com/ahfungon/snowsword-wiki.git 2>/dev/null || true
    git push -u origin main
}

echo "✅ GitHub 仓库创建完成"
echo ""

# 2. 检查 Streamlit Cloud 登录
echo "☁️ 检查 Streamlit Cloud..."
which streamlit || pip install streamlit

# 3. 创建部署配置
echo "📝 创建部署配置..."
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
DEEPSEEK_API_KEY = "${API_KEY}"
EOF

# 4. 创建 GitHub Actions 自动部署
echo "🤖 配置 GitHub Actions..."
mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install jieba
    
    - name: Build index
      run: python init.py
      
    - name: Test import
      run: python -c "from src.retriever import TextRetriever; print('✅ Index OK')"
EOF

# 5. 提交并推送所有更改
echo "📤 推送代码到 GitHub..."
git add -A
git commit -m "Add deployment config and GitHub Actions" || true
git push origin main

echo ""
echo "✅ GitHub 仓库已更新！"
echo ""
echo "🔗 仓库地址: https://github.com/ahfungon/snowsword-wiki"
echo ""
echo "🚀 下一步 - 部署到 Streamlit Cloud:"
echo ""
echo "1. 访问 https://streamlit.io/cloud"
echo "2. 使用 GitHub 登录"
echo "3. 点击 'New app'"
echo "4. 选择: ahfungon/snowsword-wiki"
echo "5. 主文件路径: app.py"
echo "6. 点击 Advanced settings → Secrets"
echo "7. 添加: DEEPSEEK_API_KEY = ${API_KEY:0:10}..."
echo "8. 点击 Deploy"
echo ""
echo "📖 或者使用 Streamlit CLI 部署:"
echo "   streamlit deploy app.py"
