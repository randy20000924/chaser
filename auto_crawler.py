"""自動爬蟲腳本 - 每天下午3點執行."""

import asyncio
import schedule
import time
from datetime import datetime
from loguru import logger

from config import settings
from database import db_manager
from ptt_crawler import PTTCrawler
from crawl_orchestrator import CrawlOrchestrator

async def daily_crawl():
    """每天下午3點執行的爬蟲任務."""
    logger.info(f"Starting daily crawl at {datetime.now()}")
    
    try:
        # 初始化資料庫
        db_manager.create_tables()
        
        # 執行爬蟲
        orchestrator = CrawlOrchestrator()
        result = await orchestrator.run_crawl_session()
        
        logger.info(f"Daily crawl completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Daily crawl failed: {e}")
        return None

def run_daily_crawl():
    """同步包裝器."""
    asyncio.run(daily_crawl())

def main():
    """主函數 - 設置定時任務."""
    logger.info("Setting up daily crawl schedule...")
    
    # 設置每天下午3點執行
    schedule.every().day.at("15:00").do(run_daily_crawl)
    
    logger.info("Daily crawl scheduler started. Waiting for 15:00...")
    
    # 保持程序運行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次

if __name__ == "__main__":
    main()
