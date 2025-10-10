#!/bin/bash

# PTT股票爬蟲系統安裝腳本

echo "=== PTT股票爬蟲系統安裝 ==="

# 檢查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "錯誤: 需要Python 3.8或更高版本，目前版本: $python_version"
    exit 1
fi

echo "Python版本檢查通過: $python_version"

# 建立虛擬環境（可選）
read -p "是否建立虛擬環境？(y/N): " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "建立虛擬環境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虛擬環境已啟動"
fi

# 安裝依賴
echo "安裝Python依賴套件..."
pip install --upgrade pip
pip install -r requirements.txt

# 檢查PostgreSQL
echo "檢查PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "警告: 未找到PostgreSQL，請確保已安裝並運行PostgreSQL"
    echo "macOS: brew install postgresql"
    echo "Ubuntu: sudo apt-get install postgresql postgresql-contrib"
    echo "Windows: 下載並安裝PostgreSQL"
fi

# 建立日誌目錄
echo "建立日誌目錄..."
mkdir -p logs

# 複製環境變數檔案
if [ ! -f .env ]; then
    echo "複製環境變數檔案..."
    cp env.example .env
    echo "請編輯 .env 檔案設定資料庫連線和其他配置"
fi

# 初始化資料庫
echo "初始化資料庫..."
python init_db.py

echo "=== 安裝完成 ==="
echo ""
echo "使用方式:"
echo "1. 編輯 .env 檔案設定資料庫連線"
echo "2. 執行測試: python test_crawler.py"
echo "3. 啟動爬蟲: python main.py --mode crawler"
echo "4. 啟動MCP服務器: python main.py --mode mcp"
echo ""
echo "詳細說明請參考 README.md"
