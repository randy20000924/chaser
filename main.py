"""PTT股票版爬蟲主應用程式."""

import asyncio
import signal
import sys
from datetime import datetime, time
from typing import Optional
from loguru import logger
import argparse
import pytz

from config import settings
from database import db_manager
from data_processor import CrawlOrchestrator


class PTTStockCrawlerApp:
    """PTT股票爬蟲主應用程式."""
    
    def __init__(self):
        self.orchestrator = CrawlOrchestrator()
        self.running = False
        self.crawl_task: Optional[asyncio.Task] = None
        self.mcp_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化應用程式."""
        logger.info("Initializing PTT Stock Crawler...")
        
        # 建立資料表
        db_manager.create_tables()
        logger.info("Database tables created/verified")
        
        # 檢查資料庫連線
        if not await db_manager.health_check():
            logger.error("Database connection failed")
            return False
        
        logger.info("Application initialized successfully")
        return True
    
    async def start_crawler(self):
        """啟動爬蟲服務."""
        logger.info("Starting crawler service...")
        
        while self.running:
            try:
                # 執行爬蟲會話
                result = await self.orchestrator.run_crawl_session()
                logger.info(f"Crawl session completed: {result}")
                
                # 處理未分類文章
                process_result = await self.orchestrator.process_unprocessed_articles()
                if process_result.get("processed_count", 0) > 0:
                    logger.info(f"Processed {process_result['processed_count']} unclassified articles")
                
                # 等待下次執行
                await asyncio.sleep(settings.crawl_interval)
                
            except Exception as e:
                logger.error(f"Crawler error: {e}")
                await asyncio.sleep(60)  # 錯誤後等待1分鐘再重試
    
    async def start_scheduled_crawler(self):
        """啟動定時爬蟲服務（每天台灣時區下午3點執行）."""
        logger.info("Starting scheduled crawler service (daily at 3:00 PM Taiwan time)...")
        
        # 設定台灣時區
        taiwan_tz = pytz.timezone('Asia/Taipei')
        
        while self.running:
            try:
                # 取得台灣時間
                now_taiwan = datetime.now(taiwan_tz)
                current_time = now_taiwan.time()
                target_time = time(15, 0)  # 下午3點
                
                # 計算距離下次執行的時間
                if current_time < target_time:
                    # 今天還沒到下午3點，等待到今天下午3點
                    next_run = now_taiwan.replace(hour=15, minute=0, second=0, microsecond=0)
                else:
                    # 今天已經過了下午3點，等待到明天下午3點
                    from datetime import timedelta
                    next_run = now_taiwan.replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(days=1)
                
                # 計算等待時間
                wait_seconds = (next_run - now_taiwan).total_seconds()
                logger.info(f"Next crawl scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')} Taiwan time (in {wait_seconds/3600:.1f} hours)")
                
                # 等待到執行時間
                await asyncio.sleep(wait_seconds)
                
                if not self.running:
                    break
                
                # 執行爬蟲
                logger.info("Starting scheduled crawl...")
                result = await self.orchestrator.run_crawl_session()
                logger.info(f"Scheduled crawl completed: {result}")
                
                # 處理未分類文章
                process_result = await self.orchestrator.process_unprocessed_articles()
                if process_result.get("processed_count", 0) > 0:
                    logger.info(f"Processed {process_result['processed_count']} unclassified articles")
                
            except Exception as e:
                logger.error(f"Scheduled crawler error: {e}")
                await asyncio.sleep(300)  # 錯誤後等待5分鐘再重試
    
    async def start_mcp_server(self):
        """啟動MCP Server."""
        logger.info("Starting MCP server...")
        logger.info("MCP server is now handled by http_mcp_server.py separately")
        # MCP服務器由 http_mcp_server.py 獨立運行
        while self.running:
            await asyncio.sleep(1)
    
    async def run(self, mode: str = "crawler"):
        """執行應用程式."""
        if not await self.initialize():
            return
        
        self.running = True
        
        # 設定信號處理
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            if mode == "crawler":
                # 只執行爬蟲
                await self.start_crawler()
            elif mode == "mcp":
                # 只執行MCP Server
                await self.start_mcp_server()
            elif mode == "both":
                # 同時執行爬蟲和MCP Server
                self.crawl_task = asyncio.create_task(self.start_crawler())
                self.mcp_task = asyncio.create_task(self.start_mcp_server())
                
                # 等待任一任務完成
                done, pending = await asyncio.wait(
                    [self.crawl_task, self.mcp_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 取消未完成的任務
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            elif mode == "scheduled":
                # 定時執行模式
                await self.start_scheduled_crawler()
            else:
                logger.error(f"Unknown mode: {mode}")
                return
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.running = False
            logger.info("Application shutdown complete")
    
    async def run_once(self):
        """執行一次爬蟲（用於測試或手動執行）."""
        if not await self.initialize():
            return
        
        logger.info("Running one-time crawl...")
        result = await self.orchestrator.run_crawl_session()
        logger.info(f"Crawl completed: {result}")
        
        # 處理未分類文章
        process_result = await self.orchestrator.process_unprocessed_articles()
        logger.info(f"Processing completed: {process_result}")


def setup_logging():
    """設定日誌系統."""
    # 移除預設的日誌處理器
    logger.remove()
    
    # 添加控制台輸出
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 添加檔案輸出
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )


async def main():
    """主函數."""
    parser = argparse.ArgumentParser(description="PTT Stock Crawler")
    parser.add_argument(
        "--mode",
        choices=["crawler", "mcp", "both", "once", "scheduled"],
        default="crawler",
        help="運行模式: crawler(爬蟲), mcp(MCP服務器), both(兩者), once(執行一次), scheduled(定時執行)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=settings.log_level,
        help="日誌級別"
    )
    
    args = parser.parse_args()
    
    # 設定日誌
    settings.log_level = args.log_level
    setup_logging()
    
    # 建立應用程式
    app = PTTStockCrawlerApp()
    
    # 執行應用程式
    if args.mode == "once":
        await app.run_once()
    else:
        await app.run(args.mode)


if __name__ == "__main__":
    asyncio.run(main())
