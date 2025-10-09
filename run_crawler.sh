#!/bin/bash

# VPS 爬蟲執行腳本
# 用於在 VPS 上執行爬蟲並將資料存入資料庫

set -e

echo "🕷️ 開始執行 PTT 爬蟲..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案目錄
PROJECT_DIR="/opt/chaser"

# 檢查是否在正確目錄
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo -e "${RED}❌ 錯誤：找不到專案目錄 $PROJECT_DIR${NC}"
    echo "請確保在正確的目錄執行此腳本"
    exit 1
fi

cd $PROJECT_DIR

# 檢查 Python 環境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 錯誤：找不到 Python 虛擬環境${NC}"
    echo "請先執行部署腳本：./deploy_vps.sh"
    exit 1
fi

# 啟動虛擬環境
source venv/bin/activate

# 檢查資料庫連接
echo -e "${BLUE}🗄️ 檢查資料庫連接...${NC}"
python -c "
from database import db_manager
try:
    with db_manager.get_session() as session:
        result = session.execute('SELECT 1').fetchone()
        print('✅ 資料庫連接正常')
except Exception as e:
    print(f'❌ 資料庫連接失敗: {e}')
    exit(1)
"

# 初始化資料庫表（如果不存在）
echo -e "${BLUE}🗄️ 初始化資料庫表...${NC}"
python -c "from database import db_manager; db_manager.create_tables()"

# 執行爬蟲（執行一次，爬取最近3天的資料）
echo -e "${BLUE}🕷️ 執行爬蟲（最近3天資料）...${NC}"
python main.py --mode once

# 檢查爬取結果
echo -e "${BLUE}📊 檢查爬取結果...${NC}"
python -c "
from database import db_manager
from models import PTTArticle
with db_manager.get_session() as session:
    count = session.query(PTTArticle).count()
    print(f'📈 資料庫中總共有 {count} 篇文章')
    
    # 顯示最近的文章
    recent_articles = session.query(PTTArticle).order_by(PTTArticle.created_at.desc()).limit(5).all()
    print('📰 最近的文章：')
    for article in recent_articles:
        print(f'  - {article.title} (作者: {article.author}, 時間: {article.created_at})')
"

# 執行文章分析
echo -e "${BLUE}🤖 執行文章分析...${NC}"
python -c "
from article_analyzer import ArticleAnalyzer
analyzer = ArticleAnalyzer()
result = analyzer.process_crawled_articles()
print(f'✅ 分析了 {result[\"processed\"]} 篇文章')
print(f'📊 成功: {result[\"success\"]}, 失敗: {result[\"failed\"]}')
"

echo -e "${GREEN}🎉 爬蟲執行完成！${NC}"
echo ""
echo -e "${BLUE}📋 下一步：${NC}"
echo "1. 檢查前端：https://www.chaser.cloud"
echo "2. 搜尋作者查看文章"
echo "3. 檢查分析結果"
echo ""
echo -e "${BLUE}🔍 查看日誌：${NC}"
echo "tail -f logs/crawler.log"
