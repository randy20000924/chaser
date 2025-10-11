#!/bin/bash

# Frontend 部署腳本
echo "🚀 開始部署 Frontend..."

# 檢查 Node.js 版本
node --version
npm --version

# 安裝依賴
echo "📥 安裝依賴..."
npm install

# 創建環境變數文件
if [ ! -f .env.local ]; then
    echo "📝 創建環境變數文件..."
    cat > .env.local << EOF
# MCP Server URL
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
EOF
    echo "⚠️  請編輯 .env.local 文件設定 MCP Server URL"
fi

# 建構生產版本
echo "🔨 建構生產版本..."
npm run build

echo "✅ Frontend 部署完成！"
echo "🔧 請編輯 .env.local 文件設定 MCP Server URL"
echo "🚀 啟動命令: npm start"
