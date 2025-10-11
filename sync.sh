#!/bin/bash
# 本地同步腳本 - 推送到 GitHub

echo "🔄 開始同步到 GitHub..."

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
    
    echo "✅ 本地同步完成！VPS 將在下次檢查時自動更新"
    echo "💡 VPS 每 2 分鐘檢查一次 GitHub 更新"
else
    echo "ℹ️ 沒有變更需要同步"
fi
