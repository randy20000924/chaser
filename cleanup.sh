#!/bin/bash

# 清理腳本 - 清理不需要的檔案和資料

echo "🧹 開始清理不需要的檔案和資料..."
echo "=================================="

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

# 3. 清理臨時檔案
echo "🗑️  清理臨時檔案..."
rm -f .DS_Store 2>/dev/null || true
rm -f Thumbs.db 2>/dev/null || true
rm -f *.tmp 2>/dev/null || true
rm -f *.temp 2>/dev/null || true

# 4. 清理前端建置檔案 (如果存在)
echo "🏗️  清理前端建置檔案..."
rm -rf frontend/.next 2>/dev/null || true
rm -rf frontend/out 2>/dev/null || true
rm -rf frontend/dist 2>/dev/null || true

# 5. 清理測試資料庫 (如果存在)
echo "🗄️  清理測試資料庫..."
rm -f test.db 2>/dev/null || true
rm -f *.db 2>/dev/null || true

# 6. 清理備份檔案
echo "💾 清理備份檔案..."
rm -f *.bak 2>/dev/null || true
rm -f *.backup 2>/dev/null || true
rm -f *~ 2>/dev/null || true

# 7. 清理 IDE 設定檔案
echo "⚙️  清理 IDE 設定檔案..."
rm -rf .vscode/settings.json 2>/dev/null || true
rm -rf .idea/ 2>/dev/null || true
rm -f .project 2>/dev/null || true
rm -f .classpath 2>/dev/null || true

# 8. 清理 Git 相關
echo "🔧 清理 Git 相關..."
git gc --prune=now 2>/dev/null || true

# 9. 顯示清理結果
echo ""
echo "✅ 清理完成！"
echo "=================================="
echo "📊 清理後的目錄大小:"
du -sh . 2>/dev/null || echo "無法計算目錄大小"

echo ""
echo "📁 剩餘的主要檔案:"
ls -la | grep -E "\.(py|js|ts|json|md|sh)$|^[A-Z]" | head -20

echo ""
echo "🎉 清理腳本執行完成！"
