#!/usr/bin/env python3
"""
PTT 爬蟲和分析性能測試腳本
測試使用當前 Ollama 模型進行爬蟲和分析的總耗時
"""

import asyncio
import time
import logging
from datetime import datetime
from crawl_orchestrator import CrawlOrchestrator
from database import DatabaseManager
from models import PTTArticle, CrawlLog
from sqlalchemy import func

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTester:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.orchestrator = CrawlOrchestrator()
        
    async def clear_test_data(self):
        """清理測試數據"""
        logger.info("清理測試數據...")
        with self.db_manager.get_session() as session:
            # 刪除測試期間的文章
            session.query(PTTArticle).delete()
            session.query(CrawlLog).delete()
            session.commit()
        logger.info("測試數據清理完成")
    
    async def get_initial_stats(self):
        """獲取初始統計數據"""
        with self.db_manager.get_session() as session:
            total_articles = session.query(PTTArticle).count()
            analyzed_articles = session.query(PTTArticle).filter(PTTArticle.is_analyzed == True).count()
            return total_articles, analyzed_articles
    
    async def run_performance_test(self, test_name="性能測試"):
        """運行性能測試"""
        logger.info(f"開始 {test_name}...")
        
        # 記錄開始時間
        start_time = time.time()
        start_datetime = datetime.now()
        
        # 清理測試數據
        await self.clear_test_data()
        
        # 獲取初始統計
        initial_total, initial_analyzed = await self.get_initial_stats()
        logger.info(f"初始狀態 - 總文章數: {initial_total}, 已分析: {initial_analyzed}")
        
        # 運行爬蟲和分析
        logger.info("開始爬蟲和分析...")
        crawl_start = time.time()
        
        try:
            # 運行爬蟲會話
            await self.orchestrator.run_crawl_session()
            crawl_end = time.time()
            crawl_duration = crawl_end - crawl_start
            
            logger.info(f"爬蟲和分析完成，耗時: {crawl_duration:.2f} 秒")
            
        except Exception as e:
            logger.error(f"爬蟲過程中發生錯誤: {e}")
            crawl_end = time.time()
            crawl_duration = crawl_end - crawl_start
            logger.info(f"爬蟲中斷，已耗時: {crawl_duration:.2f} 秒")
        
        # 獲取最終統計
        final_total, final_analyzed = await self.get_initial_stats()
        
        # 計算總耗時
        total_end_time = time.time()
        total_duration = total_end_time - start_time
        
        # 生成測試報告
        report = self.generate_report(
            test_name=test_name,
            start_datetime=start_datetime,
            total_duration=total_duration,
            crawl_duration=crawl_duration,
            initial_stats=(initial_total, initial_analyzed),
            final_stats=(final_total, final_analyzed)
        )
        
        return report
    
    def generate_report(self, test_name, start_datetime, total_duration, crawl_duration, 
                       initial_stats, final_stats):
        """生成測試報告"""
        initial_total, initial_analyzed = initial_stats
        final_total, final_analyzed = final_stats
        
        new_articles = final_total - initial_total
        new_analyzed = final_analyzed - initial_analyzed
        
        # 計算平均處理時間
        avg_time_per_article = crawl_duration / new_articles if new_articles > 0 else 0
        avg_time_per_analysis = crawl_duration / new_analyzed if new_analyzed > 0 else 0
        
        report = {
            "test_name": test_name,
            "start_time": start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration_seconds": round(total_duration, 2),
            "total_duration_formatted": f"{int(total_duration // 60)}分{int(total_duration % 60)}秒",
            "crawl_duration_seconds": round(crawl_duration, 2),
            "crawl_duration_formatted": f"{int(crawl_duration // 60)}分{int(crawl_duration % 60)}秒",
            "initial_articles": initial_total,
            "final_articles": final_total,
            "new_articles": new_articles,
            "initial_analyzed": initial_analyzed,
            "final_analyzed": final_analyzed,
            "new_analyzed": new_analyzed,
            "avg_time_per_article_seconds": round(avg_time_per_article, 2),
            "avg_time_per_analysis_seconds": round(avg_time_per_analysis, 2),
            "analysis_success_rate": f"{(new_analyzed / new_articles * 100):.1f}%" if new_articles > 0 else "0%"
        }
        
        return report
    
    def print_report(self, report):
        """打印測試報告"""
        print("\n" + "="*60)
        print(f"📊 {report['test_name']} 測試報告")
        print("="*60)
        print(f"🕐 開始時間: {report['start_time']}")
        print(f"⏱️  總耗時: {report['total_duration_formatted']} ({report['total_duration_seconds']} 秒)")
        print(f"🕷️  爬蟲+分析耗時: {report['crawl_duration_formatted']} ({report['crawl_duration_seconds']} 秒)")
        print()
        print("📈 數據統計:")
        print(f"   • 初始文章數: {report['initial_articles']}")
        print(f"   • 最終文章數: {report['final_articles']}")
        print(f"   • 新增文章數: {report['new_articles']}")
        print(f"   • 初始已分析: {report['initial_analyzed']}")
        print(f"   • 最終已分析: {report['final_analyzed']}")
        print(f"   • 新增分析數: {report['new_analyzed']}")
        print()
        print("⚡ 性能指標:")
        print(f"   • 平均每篇文章處理時間: {report['avg_time_per_article_seconds']} 秒")
        print(f"   • 平均每次分析耗時: {report['avg_time_per_analysis_seconds']} 秒")
        print(f"   • 分析成功率: {report['analysis_success_rate']}")
        print("="*60)
    
    async def run_multiple_tests(self, num_tests=3):
        """運行多次測試以獲取平均性能"""
        logger.info(f"開始運行 {num_tests} 次性能測試...")
        
        results = []
        for i in range(num_tests):
            logger.info(f"\n--- 第 {i+1} 次測試 ---")
            report = await self.run_performance_test(f"測試 {i+1}")
            results.append(report)
            self.print_report(report)
            
            # 如果不是最後一次測試，等待一下再進行下一次
            if i < num_tests - 1:
                logger.info("等待 5 秒後進行下一次測試...")
                await asyncio.sleep(5)
        
        # 計算平均性能
        if results:
            avg_total_duration = sum(r['total_duration_seconds'] for r in results) / len(results)
            avg_crawl_duration = sum(r['crawl_duration_seconds'] for r in results) / len(results)
            avg_articles = sum(r['new_articles'] for r in results) / len(results)
            avg_analyzed = sum(r['new_analyzed'] for r in results) / len(results)
            
            print("\n" + "="*60)
            print("📊 平均性能統計")
            print("="*60)
            print(f"⏱️  平均總耗時: {int(avg_total_duration // 60)}分{int(avg_total_duration % 60)}秒 ({avg_total_duration:.2f} 秒)")
            print(f"🕷️  平均爬蟲+分析耗時: {int(avg_crawl_duration // 60)}分{int(avg_crawl_duration % 60)}秒 ({avg_crawl_duration:.2f} 秒)")
            print(f"📈 平均新增文章數: {avg_articles:.1f}")
            print(f"📈 平均新增分析數: {avg_analyzed:.1f}")
            print(f"⚡ 平均每篇文章處理時間: {avg_crawl_duration/avg_articles:.2f} 秒" if avg_articles > 0 else "⚡ 平均每篇文章處理時間: N/A")
            print("="*60)

async def main():
    """主函數"""
    tester = PerformanceTester()
    
    print("🚀 PTT 爬蟲和分析性能測試")
    print("=" * 50)
    
    try:
        # 運行單次測試
        print("選擇測試模式:")
        print("1. 單次測試")
        print("2. 多次測試 (3次)")
        
        choice = input("請選擇 (1 或 2): ").strip()
        
        if choice == "2":
            await tester.run_multiple_tests(3)
        else:
            report = await tester.run_performance_test("單次性能測試")
            tester.print_report(report)
            
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
    finally:
        logger.info("測試完成")

if __name__ == "__main__":
    asyncio.run(main())
