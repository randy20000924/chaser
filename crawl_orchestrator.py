"""爬蟲協調器 - 避免重複分析."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
from ptt_crawler import PTTCrawler
from database import db_manager
from models import PTTArticle, CrawlLog

class CrawlOrchestrator:
    """協調爬蟲和文章處理的類別."""
    
    def __init__(self):
        self.crawler = PTTCrawler()
    
    async def run_crawl_session(self) -> Dict[str, Any]:
        """執行一次完整的爬蟲會話."""
        logger.info("Starting crawl session...")
        start_time = datetime.now()
        
        articles_found = 0
        articles_saved = 0
        articles_analyzed = 0
        errors = []
        
        try:
            async with self.crawler as crawler_instance:
                # 爬取所有目標作者的文章
                crawled_articles = await crawler_instance.crawl_all_authors()
                articles_found = len(crawled_articles)
                logger.info(f"Found {articles_found} new articles.")
                
                # 保存文章到資料庫，包含分析結果
                saved_count, analyzed_count = await self._save_articles_with_analysis(crawled_articles)
                articles_saved = saved_count
                articles_analyzed = analyzed_count
                
        except Exception as e:
            logger.error(f"Crawl session failed: {e}")
            errors.append(str(e))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_entry = {
            "crawl_time": start_time.isoformat(),
            "target_authors": self.crawler.target_authors,
            "articles_found": articles_found,
            "articles_saved": articles_saved,
            "articles_analyzed": articles_analyzed,
            "errors": errors,
            "duration_seconds": int(duration),
            "status": "error" if errors else "success"
        }
        
        with db_manager.get_session() as session:
            session.add(CrawlLog(**log_entry))
            session.commit()
        
        logger.info(f"Crawl session completed: Found {articles_found}, Saved {articles_saved}, Analyzed {articles_analyzed}, Duration: {duration:.2f}s")
        return {
            "status": log_entry["status"], 
            "articles_found": articles_found, 
            "articles_saved": articles_saved,
            "articles_analyzed": articles_analyzed,
            "duration_seconds": int(duration)
        }
    
    async def _save_articles_with_analysis(self, articles_data: List[Dict]) -> tuple[int, int]:
        """將文章資料（包含LLM分析結果）保存到資料庫."""
        saved_count = 0
        analyzed_count = 0
        
        with db_manager.get_session() as session:
            for article_data in articles_data:
                try:
                    # 再次檢查是否重複（雙重保險）
                    from sqlalchemy import or_
                    existing_article = session.query(PTTArticle).filter(
                        or_(
                            PTTArticle.article_id == article_data['article_id'],
                            PTTArticle.url == article_data.get('url', '')
                        )
                    ).first()
                    
                    if existing_article:
                        logger.info(f"Article {article_data['article_id']} or URL already exists, skipping")
                        continue
                    
                    logger.info(f"Saving new article: {article_data['article_id']}")
                    new_article = PTTArticle(
                        article_id=article_data['article_id'],
                        title=article_data.get('title', 'N/A'),
                        author=article_data.get('author', 'N/A'),
                        board=self.crawler.stock_board,
                        url=article_data.get('url', ''),
                        content=article_data.get('content', ''),
                        publish_time=article_data.get('publish_time', datetime.utcnow()),
                        push_count=article_data.get('push_count', 0),
                        stock_symbols=article_data.get('stock_symbols', []),
                        crawl_time=datetime.utcnow()
                    )
                    
                    # 添加 LLM 分析結果
                    analysis = article_data.get('analysis_result')
                    if analysis:
                        new_article.analysis_result = analysis
                        new_article.analysis_time = datetime.utcnow()
                        new_article.recommended_stocks = analysis.get('recommended_stocks')
                        new_article.analysis_reason = analysis.get('reason')
                        new_article.llm_sentiment = analysis.get('sentiment')
                        new_article.llm_sectors = analysis.get('sectors')
                        new_article.llm_strategy = analysis.get('strategy')
                        new_article.llm_risk_level = analysis.get('risk_level')
                        new_article.is_analyzed = True
                        analyzed_count += 1
                    
                    session.add(new_article)
                    session.commit()
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving article {article_data.get('article_id', 'N/A')}: {e}")
                    session.rollback()
                    # 如果是重複鍵錯誤，記錄但不中斷處理
                    if "duplicate key value violates unique constraint" in str(e):
                        logger.warning(f"Duplicate article detected, skipping: {article_data.get('article_id', 'N/A')}")
                        continue
            
            logger.info(f"Saved {saved_count} articles, analyzed {analyzed_count} articles")
            return saved_count, analyzed_count
    
    async def crawl_single_author(self, author: str) -> Dict[str, Any]:
        """爬取單一作者的文章."""
        logger.info(f"Starting crawl for single author: {author}")
        start_time = datetime.now()
        
        articles_found = 0
        articles_saved = 0
        articles_analyzed = 0
        errors = []
        
        try:
            async with self.crawler as crawler_instance:
                # 爬取單一作者的文章
                crawled_articles = await crawler_instance.crawl_author_articles(author)
                articles_found = len(crawled_articles)
                logger.info(f"Found {articles_found} articles for author {author}.")
                
                # 保存文章到資料庫，包含分析結果
                saved_count, analyzed_count = await self._save_articles_with_analysis(crawled_articles)
                articles_saved = saved_count
                articles_analyzed = analyzed_count
                
        except Exception as e:
            logger.error(f"Crawl for author {author} failed: {e}")
            errors.append(str(e))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_entry = {
            "crawl_time": start_time.isoformat(),
            "target_authors": [author],
            "articles_found": articles_found,
            "articles_saved": articles_saved,
            "articles_analyzed": articles_analyzed,
            "errors": errors,
            "duration_seconds": int(duration),
            "status": "error" if errors else "success"
        }
        
        with db_manager.get_session() as session:
            session.add(CrawlLog(**log_entry))
            session.commit()
        
        logger.info(f"Crawl for author {author} completed: Found {articles_found}, Saved {articles_saved}, Analyzed {articles_analyzed}, Duration: {duration:.2f}s")
        return {
            "status": log_entry["status"], 
            "author": author,
            "articles_found": articles_found, 
            "articles_saved": articles_saved,
            "articles_analyzed": articles_analyzed,
            "duration_seconds": int(duration)
        }
    
    async def process_unprocessed_articles(self) -> Dict[str, Any]:
        """處理資料庫中未經 LLM 分析的文章."""
        logger.info("Processing unprocessed articles...")
        processed_count = 0
        
        with db_manager.get_session() as session:
            unprocessed_articles = session.query(PTTArticle).filter(
                PTTArticle.is_analyzed == False
            ).all()
            
            for article in unprocessed_articles:
                try:
                    # 這裡可以添加分析邏輯
                    # 目前先標記為已處理
                    article.is_analyzed = True
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing article {article.article_id}: {e}")
            
            session.commit()
        
        logger.info(f"Processed {processed_count} unprocessed articles")
        return {"processed_count": processed_count, "status": "success"}
