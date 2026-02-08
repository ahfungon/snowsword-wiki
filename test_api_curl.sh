#!/bin/bash
# API 测试脚本

BASE_URL="http://localhost:8000"

echo "🧪 API 测试"
echo "==========="
echo ""

# 1. 健康检查
echo "1️⃣ 健康检查..."
curl -s $BASE_URL/health | python3 -m json.tool
echo ""

# 2. 统计信息
echo "2️⃣ 统计信息..."
curl -s $BASE_URL/stats | python3 -m json.tool
echo ""

# 3. 检索测试
echo "3️⃣ 检索测试..."
curl -s "$BASE_URL/search?q=徐凤年杀韩貂寺&top_k=2" | python3 -m json.tool
echo ""

# 4. 问答测试
echo "4️⃣ 专家问答（需要等待10-15秒）..."
curl -s -X POST $BASE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "徐凤年为什么要杀韩貂寺？"}' | python3 -m json.tool
echo ""

echo "✅ 测试完成！"
