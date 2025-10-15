#!/bin/bash

# 設定前端環境變數腳本

echo "=== 設定前端環境變數 ==="

# 進入前端目錄
cd /var/www/chaser/frontend

# 創建 .env.local 文件
echo "NEXT_PUBLIC_BACKEND_URL=https://www.chaser.cloud/api" > .env.local

echo "環境變數已設定："
cat .env.local

# 重新建置前端
echo "重新建置前端..."
npm run build

# 重啟 PM2 前端服務
echo "重啟前端服務..."
pm2 reload chaser-frontend

echo "=== 完成 ==="
