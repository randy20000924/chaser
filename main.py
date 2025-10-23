"""PTT股票版爬蟲主應用程式."""

import asyncio
import argparse
from datetime import datetime
from typing import Optional
from loguru import logger

from config import settings
from database import db_manager
from ptt_crawler import PTTCrawler
from http_mcp_server import app as mcp_app
from crawl_orchestrator import CrawlOrchestrator
import uvicorn

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
    
    async def start_mcp_server(self):
        """啟動MCP Server."""
        logger.info("Starting MCP server...")
        try:
            # 使用 uvicorn 的 serve 方法而不是 run
            config = uvicorn.Config(mcp_app, host="0.0.0.0", port=8000)
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"MCP server error: {e}")
    
    async def start_crawler(self):
        """啟動爬蟲服務."""
        logger.info("Starting crawler service...")
        try:
            while self.running:
                try:
                    result = await self.orchestrator.run_crawl_session()
                    logger.info(f"Crawl session completed: {result}")
                except Exception as e:
                    logger.error(f"Crawl session failed: {e}")
                
                # 等待下次執行
                await asyncio.sleep(settings.CRAWL_INTERVAL)
        except Exception as e:
            logger.error(f"Crawler service error: {e}")
    
    async def run_once(self):
        """執行一次爬蟲."""
        logger.info("Running single crawl session...")
        try:
            result = await self.orchestrator.run_crawl_session()
            logger.info(f"Single crawl completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Single crawl failed: {e}")
            return None
    
    async def run(self, mode: str):
        """運行應用程式."""
        if not await self.initialize():
            return
        
        self.running = True
        
        try:
            if mode == "mcp":
                # 只運行 MCP 服務器
                await self.start_mcp_server()
            elif mode == "crawler":
                # 只運行爬蟲服務
                await self.start_crawler()
            elif mode == "once":
                # 執行一次爬蟲
                await self.run_once()
            elif mode == "both":
                # 同時運行爬蟲和 MCP 服務器
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
            else:
                logger.error(f"Unknown mode: {mode}")
                return
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """關閉應用程式."""
        logger.info("Shutting down application...")
        self.running = False
        
        # 取消任務
        if self.crawl_task and not self.crawl_task.done():
            self.crawl_task.cancel()
            try:
                await self.crawl_task
            except asyncio.CancelledError:
                pass
        
        if self.mcp_task and not self.mcp_task.done():
            self.mcp_task.cancel()
            try:
                await self.mcp_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Application shutdown complete")

async def main():
    """主函數."""
    parser = argparse.ArgumentParser(description="PTT Stock Crawler")
    parser.add_argument(
        "--mode",
        choices=["mcp", "crawler", "once", "both"],
        default="both",
        help="運行模式"
    )
    parser.add_argument(
        "--author",
        type=str,
        help="指定要爬取的作者名稱"
    )
    
    args = parser.parse_args()
    
    # 如果指定了作者，設置動態作者
    if args.author:
        settings.DYNAMIC_AUTHOR = args.author
        logger.info(f"Dynamic author set to: {args.author}")
    
    app = PTTStockCrawlerApp()
    await app.run(args.mode)

if __name__ == "__main__":
    asyncio.run(main())
