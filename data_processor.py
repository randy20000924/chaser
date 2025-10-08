"""資料處理和LLM整合模組."""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from loguru import logger

from database import db_manager
from models import PTTArticle, AuthorProfile, CrawlLog
from ptt_crawler import PTTCrawler


class DataProcessor:
    """資料處理器."""
    
    def __init__(self):
        self.db = db_manager
    
    async def save_articles(self, articles: List[Dict]) -> int:
        """儲存文章到資料庫（去重），以 article_id/url 為唯一鍵跳過重複."""
        saved_count = 0
        
        with self.db.get_session() as session:
            for article_data in articles:
                try:
                    # 檢查文章是否已存在
                    existing = session.query(PTTArticle).filter(
                        (PTTArticle.article_id == article_data['article_id']) |
                        (PTTArticle.url == article_data['url'])
                    ).first()
                    
                    if existing:
                        logger.info(f"Article {article_data['article_id']} already exists, skipping")
                        continue
                    
                    # 建立新文章記錄
                    article = PTTArticle(
                        article_id=article_data['article_id'],
                        title=article_data['title'],
                        author=article_data['author'],
                        board='Stock',
                        url=article_data['url'],
                        content=article_data.get('content', ''),
                        publish_time=article_data.get('publish_time', datetime.now()),
                        push_count=article_data.get('push_count', 0),
                        stock_symbols=article_data.get('stock_symbols', []),
                        is_processed=False
                    )
                    
                    session.add(article)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving article {article_data.get('article_id', 'unknown')}: {e}")
                    continue
            
            try:
                session.commit()
                logger.info(f"Saved {saved_count} new articles")
            except Exception as e:
                session.rollback()
                logger.error(f"Commit failed: {e}")
                # 即使有錯誤，也記錄已處理的文章數量
                logger.info(f"Processed {saved_count} articles (some may be duplicates)")
        
        return saved_count
    
    async def update_author_profile(self, author: str, article_count: int = 0):
        """更新作者檔案."""
        with self.db.get_session() as session:
            profile = session.query(AuthorProfile).filter(
                AuthorProfile.username == author
            ).first()
            
            if not profile:
                # 建立新作者檔案
                profile = AuthorProfile(
                    username=author,
                    display_name=author,
                    is_active=True,
                    total_articles=article_count,
                    last_activity=datetime.now()
                )
                session.add(profile)
            else:
                # 更新現有檔案
                profile.total_articles += article_count
                profile.last_activity = datetime.now()
            
            session.commit()
    
    async def log_crawl_session(self, target_authors: List[str], articles_found: int, 
                               articles_saved: int, errors: List[str] = None, 
                               duration_seconds: int = 0) -> None:
        """記錄爬蟲執行日誌."""
        with self.db.get_session() as session:
            log = CrawlLog(
                target_authors=target_authors,
                articles_found=articles_found,
                articles_saved=articles_saved,
                errors=errors or [],
                duration_seconds=duration_seconds,
                status="success" if not errors else "error" if articles_saved == 0 else "partial"
            )
            session.add(log)
            session.commit()
    
    async def process_articles_for_llm(self, article_ids: List[str]) -> List[Dict]:
        """準備文章資料供LLM處理."""
        with self.db.get_session() as session:
            articles = session.query(PTTArticle).filter(
                PTTArticle.article_id.in_(article_ids)
            ).all()
            
            processed_articles = []
            for article in articles:
                processed_articles.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "author": article.author,
                    "content": article.content,
                    "publish_time": article.publish_time.isoformat(),
                    "stock_symbols": article.stock_symbols,
                    "push_count": article.push_count,
                    "url": article.url
                })
            
            return processed_articles


class LLMClassifier:
    """LLM分類器（預留給未來整合）."""
    
    def __init__(self):
        self.classification_prompts = {
            "sentiment": """
            請分析以下PTT股票版文章的投資情緒：
            文章標題：{title}
            文章內容：{content}
            
            請判斷文章的情緒傾向：
            1. 看多 (bullish)
            2. 看空 (bearish) 
            3. 中性 (neutral)
            4. 無法判斷 (unknown)
            
            請只回答選項編號。
            """,
            
            "category": """
            請將以下PTT股票版文章分類：
            文章標題：{title}
            文章內容：{content}
            
            請選擇最適合的分類：
            1. 個股分析 (stock_analysis)
            2. 市場評論 (market_commentary)
            3. 技術分析 (technical_analysis)
            4. 基本面分析 (fundamental_analysis)
            5. 新聞分享 (news_share)
            6. 討論交流 (discussion)
            7. 其他 (other)
            
            請只回答選項編號。
            """,
            
            "relevance": """
            請判斷以下文章是否與股票投資相關：
            文章標題：{title}
            文章內容：{content}
            
            請回答：
            1. 高度相關 (highly_relevant)
            2. 相關 (relevant)
            3. 低度相關 (lowly_relevant)
            4. 不相關 (irrelevant)
            
            請只回答選項編號。
            """
        }
    
    async def classify_article(self, article: Dict) -> Dict:
        """分類單篇文章."""
        # 這裡預留給實際的LLM API調用
        # 目前返回模擬結果
        
        logger.info(f"Classifying article: {article['title'][:50]}...")
        
        # 模擬分類結果
        classification = {
            "article_id": article["article_id"],
            "sentiment": "neutral",  # 預設中性
            "category": "discussion",  # 預設討論
            "relevance": "relevant",  # 預設相關
            "confidence": 0.5,  # 預設信心度
            "tags": ["stock", "ptt"],  # 預設標籤
            "processed_at": datetime.now().isoformat()
        }
        
        return classification
    
    async def batch_classify(self, articles: List[Dict]) -> List[Dict]:
        """批量分類文章."""
        results = []
        
        for article in articles:
            try:
                classification = await self.classify_article(article)
                results.append(classification)
            except Exception as e:
                logger.error(f"Error classifying article {article.get('article_id', 'unknown')}: {e}")
                continue
        
        return results
    
    async def update_article_classification(self, classifications: List[Dict]) -> None:
        """更新文章分類結果到資料庫."""
        from database import db_manager
        with db_manager.get_session() as session:
            for classification in classifications:
                try:
                    article = session.query(PTTArticle).filter(
                        PTTArticle.article_id == classification["article_id"]
                    ).first()
                    
                    if article:
                        article.sentiment = classification["sentiment"]
                        article.category = classification["category"]
                        article.tags = classification["tags"]
                        article.is_processed = True
                        
                except Exception as e:
                    logger.error(f"Error updating classification for {classification.get('article_id', 'unknown')}: {e}")
                    continue
            
            session.commit()


class CrawlOrchestrator:
    """爬蟲協調器."""
    
    def __init__(self):
        self.crawler = None
        self.processor = DataProcessor()
        self.classifier = LLMClassifier()
    
    async def run_crawl_session(self) -> Dict:
        """執行完整的爬蟲會話."""
        start_time = datetime.now()
        errors = []
        
        try:
            # 初始化爬蟲
            self.crawler = PTTCrawler()
            
            # 執行爬蟲
            async with self.crawler as crawler:
                # 直接從看板爬取，過濾目標作者
                articles = await crawler.crawl_all_authors()
            
            # 儲存文章
            saved_count = await self.processor.save_articles(articles)
            
            # 更新作者檔案
            for author in self.crawler.target_authors:
                author_articles = [a for a in articles if a['author'] == author]
                await self.processor.update_author_profile(author, len(author_articles))
            
            # 記錄爬蟲日誌
            duration = int((datetime.now() - start_time).total_seconds())
            await self.processor.log_crawl_session(
                target_authors=self.crawler.target_authors,
                articles_found=len(articles),
                articles_saved=saved_count,
                errors=errors,
                duration_seconds=duration
            )
            
            return {
                "status": "success",
                "articles_found": len(articles),
                "articles_saved": saved_count,
                "duration_seconds": duration,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Crawl session failed: {e}")
            errors.append(str(e))
            
            duration = int((datetime.now() - start_time).total_seconds())
            await self.processor.log_crawl_session(
                target_authors=getattr(self.crawler, 'target_authors', []),
                articles_found=0,
                articles_saved=0,
                errors=errors,
                duration_seconds=duration
            )
            
            return {
                "status": "error",
                "articles_found": 0,
                "articles_saved": 0,
                "duration_seconds": duration,
                "errors": errors
            }
    
    async def process_unprocessed_articles(self) -> Dict:
        """處理未分類的文章."""
        from database import db_manager as _db
        with _db.get_session() as session:
            unprocessed_articles = session.query(PTTArticle).filter(
                PTTArticle.is_processed == False
            ).limit(10).all()
            
            if not unprocessed_articles:
                return {"status": "no_unprocessed_articles"}
            
            # 準備文章資料
            articles_data = []
            for article in unprocessed_articles:
                articles_data.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "content": article.content,
                    "author": article.author,
                    "publish_time": article.publish_time.isoformat(),
                    "stock_symbols": article.stock_symbols
                })
            
            # 執行分類
            classifications = await self.classifier.batch_classify(articles_data)
            
            # 更新資料庫
            await self.classifier.update_article_classification(classifications)
            
            return {
                "status": "success",
                "processed_count": len(classifications)
            }


async def main():
    """測試資料處理功能."""
    orchestrator = CrawlOrchestrator()
    
    # 執行爬蟲會話
    result = await orchestrator.run_crawl_session()
    print(f"Crawl result: {result}")
    
    # 處理未分類文章
    process_result = await orchestrator.process_unprocessed_articles()
    print(f"Processing result: {process_result}")


if __name__ == "__main__":
    asyncio.run(main())
