#!/usr/bin/env python3
"""
清除資料庫中的所有文章和分析資料
"""

from database import db_manager
from loguru import logger
from sqlalchemy import text

def clear_database():
    """清除所有資料"""
    try:
        # 清除所有文章
        logger.info("正在清除所有文章...")
        with db_manager.get_session() as session:
            result = session.execute(text("DELETE FROM ptt_articles"))
            session.commit()
            logger.info(f"已清除 {result.rowcount} 篇文章")
        
        # 清除所有爬蟲日誌
        logger.info("正在清除爬蟲日誌...")
        with db_manager.get_session() as session:
            result = session.execute(text("DELETE FROM crawl_logs"))
            session.commit()
            logger.info(f"已清除 {result.rowcount} 條爬蟲日誌")
        
        # 重置序列號（如果有的話）
        logger.info("重置序列號...")
        with db_manager.get_session() as session:
            session.execute(text("ALTER SEQUENCE IF EXISTS ptt_articles_id_seq RESTART WITH 1"))
            session.execute(text("ALTER SEQUENCE IF EXISTS crawl_logs_id_seq RESTART WITH 1"))
            session.commit()
        
        logger.info("資料庫清除完成！")
        
    except Exception as e:
        logger.error(f"清除資料庫時發生錯誤: {e}")

if __name__ == "__main__":
    clear_database()
