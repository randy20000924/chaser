#!/bin/bash
# VPS 自動同步腳本

echo "🔄 VPS 檢查 GitHub 更新..."

# 進入專案目錄
cd /var/www/chaser

# 檢查是否有更新
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "📥 發現更新，正在拉取..."
    
    # 拉取最新變更
    git pull origin main
    
    # 更新 Python 依賴
    echo "🐍 更新 Python 依賴..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    # 重啟服務
    echo "🔄 重啟服務..."
    pm2 restart all
    
    echo "✅ VPS 同步完成！"
else
    echo "ℹ️ 沒有更新需要同步"
fi
