"""智能自動爬蟲腳本 - 基於時間戳避免重複爬取."""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from loguru import logger

from config import settings
from database import db_manager
from crawl_orchestrator import CrawlOrchestrator

class SmartCrawler:
    """智能爬蟲類別，避免重複爬取."""
    
    def __init__(self):
        self.last_crawl_time = None
        self.load_last_crawl_time()
    
    def load_last_crawl_time(self):
        """載入最後一次爬取時間."""
        try:
            with db_manager.get_session() as session:
                from models import CrawlLog
                last_log = session.query(CrawlLog).order_by(CrawlLog.crawl_time.desc()).first()
                if last_log:
                    self.last_crawl_time = last_log.crawl_time
                    logger.info(f"Last crawl time: {self.last_crawl_time}")
                else:
                    # 如果沒有爬取記錄，設定為 24 小時前
                    self.last_crawl_time = datetime.utcnow() - timedelta(hours=24)
                    logger.info(f"No previous crawl found, setting to 24 hours ago: {self.last_crawl_time}")
        except Exception as e:
            logger.error(f"Error loading last crawl time: {e}")
            self.last_crawl_time = datetime.utcnow() - timedelta(hours=24)
    
    def should_crawl(self) -> bool:
        """判斷是否應該執行爬取."""
        if not self.last_crawl_time:
            return True
        
        # 如果距離上次爬取超過 12 小時，則執行爬取
        time_since_last = datetime.utcnow() - self.last_crawl_time
        should_run = time_since_last > timedelta(hours=12)
        
        logger.info(f"Time since last crawl: {time_since_last}")
        logger.info(f"Should crawl: {should_run}")
        
        return should_run
    
    async def smart_crawl(self):
        """智能爬取 - 只在需要時執行."""
        logger.info(f"Smart crawl check at {datetime.now()}")
        
        if not self.should_crawl():
            logger.info("Skipping crawl - too soon since last run")
            return None
        
        try:
            # 初始化資料庫
            db_manager.create_tables()
            
            # 執行爬蟲
            orchestrator = CrawlOrchestrator()
            result = await orchestrator.run_crawl_session()
            
            # 更新最後爬取時間
            self.last_crawl_time = datetime.utcnow()
            
            logger.info(f"Smart crawl completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Smart crawl failed: {e}")
            return None

# 全域智能爬蟲實例
smart_crawler = SmartCrawler()

async def daily_crawl():
    """每天執行的智能爬蟲任務."""
    return await smart_crawler.smart_crawl()

def run_daily_crawl():
    """同步包裝器."""
    asyncio.run(daily_crawl())

def main():
    """主函數 - 設置定時任務."""
    logger.info("Setting up smart crawl schedule...")
    
    # 設置每 6 小時檢查一次（但實際爬取頻率由 should_crawl 控制）
    schedule.every(6).hours.do(run_daily_crawl)
    
    # 也可以設置每天特定時間執行（作為備用）
    schedule.every().day.at("15:00").do(run_daily_crawl)
    schedule.every().day.at("03:00").do(run_daily_crawl)
    
    logger.info("Smart crawl scheduler started.")
    logger.info("Crawl frequency: Every 6 hours (but only if >12h since last crawl)")
    logger.info("Backup schedules: 15:00 and 03:00 daily")
    
    # 保持程序運行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次

if __name__ == "__main__":
    main()
