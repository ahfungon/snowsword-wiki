#!/bin/bash
# 雪中悍刀行 Wiki - 一键部署脚本
# 用法: ./deploy.sh

set -e

echo "🚀 雪中悍刀行 Wiki - 部署脚本"
echo "=============================="
echo ""

# 检查 GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "📦 安装 GitHub CLI..."
    brew install gh
fi

# 检查登录状态
if ! gh auth status &>/dev/null; then
    echo "🔐 请先登录 GitHub..."
    gh auth login --web
fi

echo "✅ GitHub 已登录"
echo ""

# 创建 GitHub 仓库
echo "📦 创建 GitHub 仓库..."
cd "$(dirname "$0")"

if gh repo view ahfungon/snowsword-wiki &>/dev/null; then
    echo "⚠️ 仓库已存在，跳过创建"
else
    gh repo create ahfungon/snowsword-wiki --public --source=. --remote=origin --push
    echo "✅ 仓库创建成功"
fi

echo ""
echo "📤 推送代码..."
git push -u origin main || true

echo ""
echo "=============================="
echo "✅ GitHub 部署完成！"
echo ""
echo "🔗 仓库地址: https://github.com/ahfungon/snowsword-wiki"
echo ""
echo "🚀 下一步 - 部署到 Streamlit Cloud:"
echo ""
echo "方法 1 - 网页部署（推荐）:"
echo "  1. 访问 https://streamlit.io/cloud"
echo "  2. 使用 GitHub 账号登录"
echo "  3. 点击 'New app'"
echo "  4. 选择: ahfungon/snowsword-wiki"
echo "  5. 主文件路径: app.py"
echo "  6. 点击 Advanced settings → Secrets"
echo "  7. 添加: DEEPSEEK_API_KEY = sk-cdebe0..."
echo "  8. 点击 Deploy"
echo ""
echo "方法 2 - CLI 部署:"
echo "  streamlit deploy app.py"
echo ""
