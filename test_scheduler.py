"""測試定時爬蟲腳本 - 5分鐘後執行."""

import asyncio
import schedule
import time
from datetime import datetime
from loguru import logger

from config import settings
from database import db_manager
from ptt_crawler import PTTCrawler
from crawl_orchestrator import CrawlOrchestrator

async def test_crawl():
    """測試爬蟲任務."""
    logger.info(f"Starting test crawl at {datetime.now()}")
    
    try:
        # 初始化資料庫
        db_manager.create_tables()
        
        # 執行爬蟲
        orchestrator = CrawlOrchestrator()
        result = await orchestrator.run_crawl_session()
        
        logger.info(f"Test crawl completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Test crawl failed: {e}")
        return None

def run_test_crawl():
    """同步包裝器."""
    asyncio.run(test_crawl())

def main():
    """主函數 - 設置測試定時任務."""
    logger.info("Setting up test crawl schedule...")
    
    # 獲取當前時間
    now = datetime.now()
    test_time = now.replace(minute=now.minute + 5, second=0, microsecond=0)
    
    # 如果超過 55 分鐘，則設定到下一小時
    if test_time.minute >= 60:
        test_time = test_time.replace(hour=test_time.hour + 1, minute=0)
    
    # 設置 5 分鐘後執行
    schedule.every().day.at(test_time.strftime("%H:%M")).do(run_test_crawl)
    
    logger.info(f"Test crawl scheduled for {test_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Test scheduler started. Waiting for scheduled time...")
    
    # 保持程序運行
    while True:
        schedule.run_pending()
        time.sleep(10)  # 每 10 秒檢查一次，更頻繁的檢查

if __name__ == "__main__":
    main()
