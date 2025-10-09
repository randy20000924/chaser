#!/bin/bash
# rsync 實時同步腳本

echo "🔄 使用 rsync 同步到 VPS..."

# 排除不需要同步的檔案
rsync -avz --delete \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude 'logs/' \
    --exclude '.env' \
    /Users/randychang/Documents/chaser/ \
    root@159.198.37.93:/var/www/chaser/

echo "✅ rsync 同步完成！"
