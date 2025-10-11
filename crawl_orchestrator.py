#!/usr/bin/env python3
"""爬蟲協調器 - 管理爬蟲執行和文章保存."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from config import settings
from database import db_manager
from models import PTTArticle, CrawlLog
from ptt_crawler import PTTCrawler


class CrawlOrchestrator:
    """爬蟲協調器."""
    
    def __init__(self):
        self.target_authors = settings.target_authors
        self.max_articles_per_crawl = settings.max_articles_per_crawl
        self.search_days = settings.search_days
    
    async def run_crawl_session(self) -> Dict:
        """執行一次完整的爬蟲會話."""
        logger.info("Starting crawl session...")
        start_time = datetime.now()
        
        try:
            async with PTTCrawler() as crawler:
                # 爬取所有目標作者的文章
                all_articles = await crawler.crawl_all_authors()
                
                # 保存文章到資料庫（包含分析結果）
                saved_count = await self._save_articles_with_analysis(all_articles)
                
                # 記錄爬蟲日誌
                duration = (datetime.now() - start_time).total_seconds()
                await self._log_crawl_session(
                    articles_found=len(all_articles),
                    articles_saved=saved_count,
                    duration_seconds=int(duration)
                )
                
                result = {
                    "status": "success",
                    "articles_found": len(all_articles),
                    "articles_saved": saved_count,
                    "duration_seconds": int(duration)
                }
                
                logger.info(f"Crawl session completed: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Crawl session failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            await self._log_crawl_session(
                articles_found=0,
                articles_saved=0,
                duration_seconds=int(duration),
                status="error",
                errors=[str(e)]
            )
            return {
                "status": "error",
                "error": str(e),
                "duration_seconds": int(duration)
            }
    
    async def _save_articles_with_analysis(self, articles: List[Dict]) -> int:
        """保存文章到資料庫，包含分析結果."""
        saved_count = 0
        
        with db_manager.get_session() as session:
            for article_data in articles:
                try:
                    # 檢查文章是否已存在
                    existing_article = session.query(PTTArticle).filter(
                        PTTArticle.article_id == article_data['article_id']
                    ).first()
                    
                    if existing_article:
                        # 如果文章已存在但沒有分析結果，更新分析結果
                        if not existing_article.is_analyzed and article_data.get('analysis_result'):
                            self._update_article_with_analysis(existing_article, article_data['analysis_result'])
                            saved_count += 1
                        continue
                    
                    # 創建新文章記錄
                    article = PTTArticle(
                        article_id=article_data['article_id'],
                        title=article_data['title'],
                        author=article_data['author'],
                        board=settings.ptt_stock_board,
                        url=article_data['url'],
                        content=article_data['content'],
                        publish_time=article_data['publish_time'],
                        push_count=article_data.get('push_count', 0),
                        stock_symbols=article_data.get('stock_symbols', []),
                        is_processed=True,
                        is_relevant=True
                    )
                    
                    # 如果有分析結果，添加到文章記錄中
                    if article_data.get('analysis_result'):
                        self._update_article_with_analysis(article, article_data['analysis_result'])
                    
                    session.add(article)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving article {article_data.get('article_id', 'unknown')}: {e}")
                    continue
            
            session.commit()
        
        logger.info(f"Saved {saved_count} articles with analysis results")
        return saved_count
    
    def _update_article_with_analysis(self, article: PTTArticle, analysis_result: Dict):
        """更新文章記錄，添加分析結果."""
        try:
            # 更新分析結果欄位
            article.analysis_result = analysis_result
            article.analysis_time = datetime.now()
            article.is_analyzed = True
            
            # 提取分析結果中的具體欄位
            if 'recommended_stocks' in analysis_result:
                article.recommended_stocks = analysis_result['recommended_stocks']
            
            if 'reason' in analysis_result:
                article.analysis_reason = analysis_result['reason']
            
            if 'llm_analysis' in analysis_result:
                llm_analysis = analysis_result['llm_analysis']
                
                if 'sentiment' in llm_analysis:
                    article.llm_sentiment = llm_analysis['sentiment']
                
                if 'sectors' in llm_analysis:
                    article.llm_sectors = llm_analysis['sectors']
                
                if 'strategy' in llm_analysis:
                    article.llm_strategy = llm_analysis['strategy']
                
                if 'risk_level' in llm_analysis:
                    article.llm_risk_level = llm_analysis['risk_level']
            
            logger.debug(f"Updated article {article.article_id} with analysis results")
            
        except Exception as e:
            logger.error(f"Error updating article with analysis: {e}")
    
    async def _log_crawl_session(self, articles_found: int, articles_saved: int, 
                                duration_seconds: int, status: str = "success", 
                                errors: Optional[List[str]] = None):
        """記錄爬蟲會話日誌."""
        try:
            with db_manager.get_session() as session:
                log_entry = CrawlLog(
                    target_authors=self.target_authors,
                    articles_found=articles_found,
                    articles_saved=articles_saved,
                    duration_seconds=duration_seconds,
                    status=status,
                    errors=errors or []
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            logger.error(f"Error logging crawl session: {e}")
    
    async def process_unprocessed_articles(self) -> Dict:
        """處理未處理的文章（這個方法現在不需要了，因為我們在爬蟲時就處理了）."""
        logger.info("All articles are processed during crawling, no unprocessed articles to handle")
        return {
            "processed_count": 0,
            "status": "no_unprocessed_articles"
        }
