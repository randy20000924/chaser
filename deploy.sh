#!/bin/bash

# 一鍵部署腳本
echo "🚀 開始一鍵部署 Chaser 專案..."

# 檢查目錄結構
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 錯誤: 找不到 backend 或 frontend 目錄"
    exit 1
fi

# 部署 Backend
echo "📦 部署 Backend..."
cd backend
chmod +x deploy.sh
./deploy.sh
cd ..

# 部署 Frontend
echo "🌐 部署 Frontend..."
cd frontend
chmod +x deploy.sh
./deploy.sh
cd ..

echo "✅ 一鍵部署完成！"
echo ""
echo "📋 部署摘要:"
echo "  Backend:  ./backend/"
echo "  Frontend: ./frontend/"
echo ""
echo "🔧 下一步:"
echo "  1. 編輯 backend/.env 設定資料庫連線"
echo "  2. 編輯 frontend/.env.local 設定 MCP Server URL"
echo "  3. 啟動 Backend: cd backend && python main.py --mode crawler"
echo "  4. 啟動 Frontend: cd frontend && npm start"
echo ""
echo "🌐 預設端口:"
echo "  Backend (MCP Server): http://localhost:8000"
echo "  Frontend: http://localhost:3000"
