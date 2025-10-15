#!/bin/bash

# 修復依賴套件腳本

echo "🔧 修復 Python 依賴套件..."
echo "=================================="

# 進入專案目錄
cd /var/www/chaser

# 激活虛擬環境
source venv/bin/activate

echo "📦 檢查當前 Python 版本..."
python --version

echo ""
echo "🔄 重新安裝核心依賴套件..."

# 重新安裝 pydantic 相關套件
echo "1. 修復 pydantic 套件..."
pip uninstall pydantic pydantic-core pydantic-settings -y
pip install pydantic pydantic-settings

# 重新安裝 psycopg2
echo "2. 修復 psycopg2 套件..."
pip uninstall psycopg2 psycopg2-binary -y
pip install psycopg2-binary

# 重新安裝其他可能問題的套件
echo "3. 修復其他核心套件..."
pip install --upgrade --force-reinstall sqlalchemy
pip install --upgrade --force-reinstall fastapi
pip install --upgrade --force-reinstall uvicorn

echo ""
echo "🧪 測試套件導入..."

# 測試關鍵套件導入
python -c "
try:
    from database import db_manager
    print('✅ Database import successful!')
except Exception as e:
    print(f'❌ Database import failed: {e}')

try:
    from config import settings
    print('✅ Config import successful!')
except Exception as e:
    print(f'❌ Config import failed: {e}')

try:
    from models import PTTArticle
    print('✅ Models import successful!')
except Exception as e:
    print(f'❌ Models import failed: {e}')
"

echo ""
echo "✅ 依賴套件修復完成！"
echo "=================================="
