#!/bin/bash
# 檔案監控同步腳本

echo "👀 開始監控檔案變更..."

# 安裝 fswatch (如果沒有安裝)
if ! command -v fswatch &> /dev/null; then
    echo "📦 安裝 fswatch..."
    brew install fswatch
fi

# 監控檔案變更並自動同步
fswatch -o /Users/randychang/Documents/chaser | while read f; do
    echo "🔄 檢測到檔案變更，開始同步..."
    ./rsync_sync.sh
done
