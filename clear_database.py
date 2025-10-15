#!/usr/bin/env python3
"""
清除資料庫中的所有文章和分析資料
"""

import asyncio
from database import DatabaseManager
from loguru import logger

async def clear_database():
    """清除所有資料"""
    db_manager = DatabaseManager()
    
    try:
        # 連接到資料庫
        await db_manager.connect()
        
        # 清除所有文章
        logger.info("正在清除所有文章...")
        result = await db_manager.execute_query("DELETE FROM ptt_articles")
        logger.info(f"已清除 {result.rowcount} 篇文章")
        
        # 清除所有爬蟲日誌
        logger.info("正在清除爬蟲日誌...")
        result = await db_manager.execute_query("DELETE FROM crawl_logs")
        logger.info(f"已清除 {result.rowcount} 條爬蟲日誌")
        
        # 重置序列號（如果有的話）
        logger.info("重置序列號...")
        await db_manager.execute_query("ALTER SEQUENCE IF EXISTS ptt_articles_id_seq RESTART WITH 1")
        await db_manager.execute_query("ALTER SEQUENCE IF EXISTS crawl_logs_id_seq RESTART WITH 1")
        
        logger.info("資料庫清除完成！")
        
    except Exception as e:
        logger.error(f"清除資料庫時發生錯誤: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(clear_database())
