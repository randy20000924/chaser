"""手動爬蟲腳本 - 用於測試和手動執行."""

import asyncio
import argparse
from datetime import datetime
from loguru import logger

from config import settings
from database import db_manager
from ptt_crawler import PTTCrawler
from crawl_orchestrator import CrawlOrchestrator

async def manual_crawl():
    """手動執行爬蟲和分析."""
    logger.info("Starting manual crawl...")
    
    # 初始化資料庫
    db_manager.create_tables()
    
    # 執行爬蟲
    orchestrator = CrawlOrchestrator()
    result = await orchestrator.run_crawl_session()
    
    logger.info(f"Manual crawl completed: {result}")
    return result

if __name__ == "__main__":
    asyncio.run(manual_crawl())
