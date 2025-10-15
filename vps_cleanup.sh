#!/bin/bash

# VPS 清理腳本 - 清理不需要的檔案和資料

echo "🧹 開始 VPS 清理..."
echo "=================================="

# 進入專案目錄
cd /var/www/chaser

# 1. 清理 Python 快取檔案
echo "📁 清理 Python 快取檔案..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
find . -name "*.so" -delete 2>/dev/null || true
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# 2. 清理日誌檔案
echo "📄 清理日誌檔案..."
rm -f *.log 2>/dev/null || true
rm -f logs/*.log 2>/dev/null || true
rm -f frontend-combined-*.log 2>/dev/null || true

# 3. 清理 PM2 日誌 (保留最近 100 行)
echo "📊 清理 PM2 日誌..."
pm2 flush 2>/dev/null || true

# 4. 清理系統日誌 (保留最近 1000 行)
echo "🗄️  清理系統日誌..."
journalctl --vacuum-size=100M 2>/dev/null || true

# 5. 清理前端建置檔案
echo "🏗️  清理前端建置檔案..."
rm -rf frontend/.next 2>/dev/null || true
rm -rf frontend/out 2>/dev/null || true
rm -rf frontend/dist 2>/dev/null || true

# 6. 清理臨時檔案
echo "🗑️  清理臨時檔案..."
rm -f .DS_Store 2>/dev/null || true
rm -f Thumbs.db 2>/dev/null || true
rm -f *.tmp 2>/dev/null || true
rm -f *.temp 2>/dev/null || true

# 7. 清理備份檔案
echo "💾 清理備份檔案..."
rm -f *.bak 2>/dev/null || true
rm -f *.backup 2>/dev/null || true
rm -f *~ 2>/dev/null || true

# 8. 清理 Git 相關
echo "🔧 清理 Git 相關..."
git gc --prune=now 2>/dev/null || true

# 9. 清理 Docker 相關 (如果存在)
echo "🐳 清理 Docker 相關..."
docker system prune -f 2>/dev/null || true

# 10. 清理 APT 快取
echo "📦 清理 APT 快取..."
apt-get clean 2>/dev/null || true
apt-get autoclean 2>/dev/null || true

# 11. 顯示清理結果
echo ""
echo "✅ VPS 清理完成！"
echo "=================================="

# 顯示磁碟使用情況
echo "📊 磁碟使用情況:"
df -h

echo ""
echo "📁 專案目錄大小:"
du -sh /var/www/chaser

echo ""
echo "📊 記憶體使用情況:"
free -h

echo ""
echo "🔄 PM2 服務狀態:"
pm2 status

echo ""
echo "🎉 VPS 清理腳本執行完成！"
