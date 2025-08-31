#!/bin/bash

# AI代码安全审计系统启动脚本
echo "🚀 启动AI代码安全审计系统..."

# 检查MySQL服务
echo "📊 检查MySQL服务..."
if ! pgrep -x "mysqld" > /dev/null; then
    echo "启动MySQL服务..."
    sudo mysql.server start
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend
source venv/bin/activate
python run_server.py &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 5

# 启动前端服务
echo "🎨 启动前端服务..."
cd ../frontend
BROWSER=none npm start &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"

echo ""
echo "✅ 系统启动完成！"
echo "前端地址: http://localhost:3000"
echo "后端API: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
