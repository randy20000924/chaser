#!/bin/bash

# VPS 清除資料庫並重新爬取腳本

echo "=== 清除資料庫並重新爬取 ==="

# 進入專案目錄
cd /var/www/chaser

# 拉取最新代碼
echo "拉取最新代碼..."
git pull origin main

# 激活虛擬環境
echo "激活虛擬環境..."
source venv/bin/activate

# 清除資料庫
echo "清除資料庫..."
python clear_database.py

# 重新爬取
echo "開始重新爬取..."
python manual_crawler.py

echo "=== 完成 ==="
