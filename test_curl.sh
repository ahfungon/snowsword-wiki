#!/bin/bash
# 本地 curl 测试脚本
# 用法: ./test_curl.sh [API_URL]

API_URL=${1:-"http://localhost:8000"}

echo "🧪 测试雪中悍刀行 API"
echo "======================"
echo "API地址: $API_URL"
echo ""

# 测试1: 根路径
echo "1️⃣ 测试根路径..."
curl -s "$API_URL/" | python3 -m json.tool 2>/dev/null || curl -s "$API_URL/"
echo ""
echo ""

# 测试2: 健康检查
echo "2️⃣ 测试健康检查..."
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败"
fi
echo ""

# 测试3: 搜索
echo "3️⃣ 测试搜索接口..."
SEARCH=$(curl -s "$API_URL/search?q=徐凤年&top_k=2")
echo "$SEARCH" | python3 -m json.tool 2>/dev/null || echo "$SEARCH"
echo ""

# 测试4: 问答
echo "4️⃣ 测试问答接口..."
echo "发送问题: 徐凤年为什么要杀韩貂寺？"
QUERY=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{"query":"徐凤年为什么要杀韩貂寺","top_k":5}')
echo "$QUERY" | python3 -m json.tool 2>/dev/null || echo "$QUERY"
echo ""

echo "======================"
echo "✅ 测试完成！"
