#!/bin/bash

# Backend 部署腳本
echo "🚀 開始部署 Backend..."

# 檢查 Python 版本
python3 --version

# 創建虛擬環境
echo "📦 創建虛擬環境..."
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
echo "📥 安裝依賴..."
pip install --upgrade pip
pip install -r requirements.txt

# 創建環境變數文件
if [ ! -f .env ]; then
    echo "📝 創建環境變數文件..."
    cp env.example .env
    echo "⚠️  請編輯 .env 文件設定資料庫連線等參數"
fi

# 初始化資料庫
echo "🗄️  初始化資料庫..."
python -c "from database import db_manager; db_manager.create_tables()"

# 創建日誌目錄
mkdir -p logs

echo "✅ Backend 部署完成！"
echo "🔧 請編輯 .env 文件設定資料庫連線"
echo "🚀 啟動命令: python main.py --mode crawler"
