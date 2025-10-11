#!/bin/bash
# 快速同步腳本 - 不檢查變更，直接推送

echo "⚡ 快速同步到 GitHub..."

# 添加所有變更
git add .

# 提交變更
git commit -m "Quick sync: $(date '+%Y-%m-%d %H:%M:%S')"

# 推送到 GitHub
echo "📤 推送到 GitHub..."
git push origin main

echo "✅ 快速同步完成！VPS 將在 2 分鐘內自動更新"
