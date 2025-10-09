#!/bin/bash
# VPS 自動同步腳本

echo "🔄 VPS 同步腳本啟動..."

# 進入專案目錄
cd /var/www/chaser

# 拉取最新變更
echo "📥 拉取最新變更..."
git pull origin main

# 更新 Python 依賴
echo "🐍 更新 Python 依賴..."
source venv/bin/activate
pip install -r requirements.txt

# 重啟服務
echo "🔄 重啟服務..."
pm2 restart all

echo "✅ VPS 同步完成！"
