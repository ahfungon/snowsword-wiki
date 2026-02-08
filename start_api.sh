#!/bin/bash
# 启动 API 服务脚本

cd /Users/ahfun/.openclaw/workspace/snowsword-wiki
export DEEPSEEK_API_KEY="sk-cdebe0fafcf9406d962e3e09a0404e4b"

echo "🚀 启动 API 服务..."
echo "服务将在 http://localhost:8000 运行"
echo "按 Ctrl+C 停止"
echo ""

python3 api.py
