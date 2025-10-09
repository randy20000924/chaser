#!/bin/bash

# 快速爬蟲腳本 - 爬取最近3天的資料

echo "🕷️ 快速爬蟲 - 爬取最近3天資料..."

cd /opt/chaser
source venv/bin/activate

# 執行爬蟲
echo "開始爬蟲..."
python main.py --mode once

# 檢查結果
echo "檢查結果..."
python -c "
from database import db_manager
from models import PTTArticle
with db_manager.get_session() as session:
    count = session.query(PTTArticle).count()
    print(f'資料庫中總共有 {count} 篇文章')
"

echo "✅ 爬蟲完成！"
