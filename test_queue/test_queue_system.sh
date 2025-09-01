#!/bin/bash

# 获取admin token
echo "🔐 获取admin token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Token获取成功: ${TOKEN:0:50}..."

echo ""
echo "📊 当前队列状态:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/audit/queue/status | python3 -m json.tool

echo ""
echo "🚀 开始并发提交3个任务..."

# 并发提交3个任务
for i in {1..3}; do
  (
    echo "📤 提交任务 $i..."
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/upload \
      -H "Authorization: Bearer $TOKEN" \
      -F "project_name=Test Project $i" \
      -F "description=Queue test project $i" \
      -F "files=@test_project_$i.zip")
    
    echo "Task $i Response: $RESPONSE" | python3 -m json.tool
    
    # 提取task_id
    TASK_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'error'))")
    
    if [ "$TASK_ID" != "error" ]; then
      echo "🎯 启动任务 $i (ID: $TASK_ID)..."
      START_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/start/$TASK_ID \
        -H "Authorization: Bearer $TOKEN")
      echo "Start Task $i Response: $START_RESPONSE" | python3 -m json.tool
    fi
  ) &
done

# 等待所有后台任务完成
wait

echo ""
echo "⏱️ 等待3秒后查看队列状态..."
sleep 3

echo "📊 提交后的队列状态:"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/audit/queue/status | python3 -m json.tool

echo ""
echo "🔍 查看Redis队列数据:"
redis-cli ZRANGE audit_task_queue 0 -1 WITHSCORES
