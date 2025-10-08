"""測試爬蟲功能的腳本."""

import asyncio
import sys
from loguru import logger

# 添加專案根目錄到Python路徑
sys.path.append('.')

from ptt_crawler import PTTCrawler
from data_processor import DataProcessor
from database import db_manager


async def test_crawler():
    """測試爬蟲功能."""
    logger.info("開始測試PTT爬蟲...")
    
    try:
        # 測試爬蟲
        async with PTTCrawler() as crawler:
            logger.info(f"目標作者: {crawler.target_authors}")
            
            # 爬取文章
            articles = await crawler.crawl_all_authors()
            logger.info(f"找到 {len(articles)} 篇文章")
            
            # 顯示文章資訊
            for i, article in enumerate(articles, 1):
                logger.info(f"文章 {i}:")
                logger.info(f"  標題: {article['title']}")
                logger.info(f"  作者: {article['author']}")
                logger.info(f"  股票代碼: {article.get('stock_symbols', [])}")
                logger.info(f"  推文數: {article.get('push_count', 0)}")
                logger.info("---")
    
    except Exception as e:
        logger.error(f"爬蟲測試失敗: {e}")
        return False
    
    return True


async def test_database():
    """測試資料庫功能."""
    logger.info("開始測試資料庫...")
    
    try:
        # 檢查資料庫連線
        if not await db_manager.health_check():
            logger.error("資料庫連線失敗")
            return False
        
        logger.info("資料庫連線正常")
        
        # 建立資料表
        db_manager.create_tables()
        logger.info("資料表建立完成")
        
        return True
    
    except Exception as e:
        logger.error(f"資料庫測試失敗: {e}")
        return False


async def test_data_processor():
    """測試資料處理功能."""
    logger.info("開始測試資料處理...")
    
    try:
        processor = DataProcessor()
        
        # 模擬文章資料
        test_articles = [
            {
                "article_id": "test_001",
                "title": "測試文章1",
                "author": "mrp",
                "url": "https://www.ptt.cc/bbs/Stock/test1.html",
                "content": "這是測試內容，包含股票代碼 2330 和 2317",
                "publish_time": "2024-01-01T10:00:00",
                "push_count": 5,
                "stock_symbols": ["2330", "2317"]
            }
        ]
        
        # 測試儲存文章
        saved_count = await processor.save_articles(test_articles)
        logger.info(f"儲存了 {saved_count} 篇文章")
        
        # 測試更新作者檔案
        await processor.update_author_profile("mrp", 1)
        logger.info("作者檔案更新完成")
        
        return True
    
    except Exception as e:
        logger.error(f"資料處理測試失敗: {e}")
        return False


async def main():
    """執行所有測試."""
    logger.info("=== PTT股票爬蟲系統測試 ===")
    
    # 測試資料庫
    if not await test_database():
        logger.error("資料庫測試失敗，停止測試")
        return
    
    # 測試資料處理
    if not await test_data_processor():
        logger.error("資料處理測試失敗，停止測試")
        return
    
    # 測試爬蟲（可選，因為需要網路連線）
    test_crawl = input("是否測試爬蟲功能？(y/N): ").lower() == 'y'
    if test_crawl:
        if not await test_crawler():
            logger.error("爬蟲測試失敗")
        else:
            logger.info("爬蟲測試完成")
    
    logger.info("=== 測試完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
