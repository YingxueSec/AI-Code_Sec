#!/bin/bash

echo "🧪 测试多用户优先级队列系统"
echo "================================"

# 获取不同用户的token
echo "🔐 获取用户tokens..."

# Admin用户 (优先级4)
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 普通用户 (优先级1)
USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"123","password":"123456"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Admin token: ${ADMIN_TOKEN:0:30}..."
echo "✅ User token: ${USER_TOKEN:0:30}..."

echo ""
echo "📊 初始队列状态:"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/v1/audit/queue/status | python3 -m json.tool

echo ""
echo "🚀 步骤1: 普通用户先提交2个任务（占满槽位）"

for i in {1..2}; do
  echo "📤 普通用户提交任务 $i..."
  RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/upload \
    -H "Authorization: Bearer $USER_TOKEN" \
    -F "project_name=User Task $i" \
    -F "description=Normal user task $i" \
    -F "files=@test_project_$i.zip")
  
  TASK_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'error'))")
  
  if [ "$TASK_ID" != "error" ]; then
    echo "🎯 启动普通用户任务 $i (ID: $TASK_ID)..."
    curl -s -X POST http://localhost:8000/api/v1/audit/start/$TASK_ID \
      -H "Authorization: Bearer $USER_TOKEN" > /dev/null
  fi
  
  sleep 1
done

echo ""
echo "📊 普通用户任务提交后的队列状态:"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/v1/audit/queue/status | python3 -m json.tool

echo ""
echo "🚀 步骤2: 普通用户再提交1个任务（应该排队）"

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/upload \
  -H "Authorization: Bearer $USER_TOKEN" \
  -F "project_name=User Task 3" \
  -F "description=Normal user task 3 (should queue)" \
  -F "files=@test_project_3.zip")

TASK_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'error'))")

if [ "$TASK_ID" != "error" ]; then
  echo "🎯 启动普通用户任务3 (ID: $TASK_ID) - 应该进入队列..."
  START_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/start/$TASK_ID \
    -H "Authorization: Bearer $USER_TOKEN")
  echo "队列响应: $START_RESPONSE" | python3 -m json.tool
fi

echo ""
echo "🚀 步骤3: 管理员提交高优先级任务（应该插队）"

cp test_project_1.zip admin_priority_task.zip

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "project_name=Admin Priority Task" \
  -F "description=High priority admin task" \
  -F "files=@admin_priority_task.zip")

TASK_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'error'))")

if [ "$TASK_ID" != "error" ]; then
  echo "🎯 启动管理员高优先级任务 (ID: $TASK_ID) - 应该插队到队列前面..."
  START_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/audit/start/$TASK_ID \
    -H "Authorization: Bearer $ADMIN_TOKEN")
  echo "管理员任务队列响应: $START_RESPONSE" | python3 -m json.tool
fi

echo ""
echo "📊 最终队列状态（管理员任务应该在前面）:"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/v1/audit/queue/status | python3 -m json.tool

echo ""
echo "🔍 Redis队列数据（按优先级排序）:"
redis-cli ZREVRANGE audit_task_queue 0 -1 WITHSCORES

echo ""
echo "🔍 运行中的任务："
redis-cli SMEMBERS audit_running_tasks

echo ""
echo "✅ 优先级队列测试完成！"
