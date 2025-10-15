#!/usr/bin/env python3
"""
快速性能測試腳本 - 只測試少量文章
"""

import asyncio
import time
import logging
from datetime import datetime
from crawl_orchestrator import CrawlOrchestrator
from database import DatabaseManager
from models import PTTArticle

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

async def quick_test():
    """快速測試 - 只爬取和分析少量文章"""
    logger.info("🚀 開始快速性能測試...")
    
    # 記錄開始時間
    start_time = time.time()
    start_datetime = datetime.now()
    
    # 初始化
    db_manager = DatabaseManager()
    orchestrator = CrawlOrchestrator()
    
    # 清理測試數據
    logger.info("清理測試數據...")
    with db_manager.get_session() as session:
        session.query(PTTArticle).delete()
        session.commit()
    
    # 獲取初始統計
    with db_manager.get_session() as session:
        initial_count = session.query(PTTArticle).count()
    
    logger.info(f"初始文章數: {initial_count}")
    
    try:
        # 運行爬蟲和分析
        logger.info("開始爬蟲和分析...")
        crawl_start = time.time()
        
        await orchestrator.run_crawl_session()
        
        crawl_end = time.time()
        crawl_duration = crawl_end - crawl_start
        
        # 獲取最終統計
        with db_manager.get_session() as session:
            final_count = session.query(PTTArticle).count()
            analyzed_count = session.query(PTTArticle).filter(PTTArticle.is_analyzed == True).count()
        
        # 計算總耗時
        total_duration = time.time() - start_time
        
        # 生成報告
        new_articles = final_count - initial_count
        avg_time_per_article = crawl_duration / new_articles if new_articles > 0 else 0
        
        print("\n" + "="*50)
        print("📊 快速性能測試報告")
        print("="*50)
        print(f"🕐 開始時間: {start_datetime.strftime('%H:%M:%S')}")
        print(f"⏱️  總耗時: {int(total_duration // 60)}分{int(total_duration % 60)}秒")
        print(f"🕷️  爬蟲+分析耗時: {int(crawl_duration // 60)}分{int(crawl_duration % 60)}秒")
        print(f"📈 新增文章數: {new_articles}")
        print(f"📈 已分析文章數: {analyzed_count}")
        print(f"⚡ 平均每篇文章: {avg_time_per_article:.2f} 秒")
        print(f"📊 分析成功率: {(analyzed_count/new_articles*100):.1f}%" if new_articles > 0 else "📊 分析成功率: N/A")
        print("="*50)
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
