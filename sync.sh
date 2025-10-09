#!/bin/bash
# 自動同步腳本

echo "🔄 開始同步到 VPS..."

# 檢查是否有變更
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 發現變更，正在提交..."
    
    # 添加所有變更
    git add .
    
    # 提交變更
    git commit -m "Auto sync: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # 推送到 GitHub
    echo "📤 推送到 GitHub..."
    git push origin main
    
    # 在 VPS 上拉取更新
    echo "📥 在 VPS 上拉取更新..."
    ssh root@159.198.37.93 "cd /var/www/chaser && git pull origin main && pm2 restart all"
    
    echo "✅ 同步完成！"
else
    echo "ℹ️ 沒有變更需要同步"
fi
