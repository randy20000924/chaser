"""HTTP MCP Server for PTT Stock Crawler."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from database import db_manager
from models import PTTArticle, AuthorProfile, CrawlLog

app = FastAPI(title="PTT Stock Crawler API", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路徑."""
    return {"message": "PTT Stock Crawler API", "status": "running"}

@app.get("/health")
async def health_check():
    """健康檢查."""
    try:
        # 檢查資料庫連接
        if await db_manager.health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/articles")
async def get_articles(
    author: Optional[str] = Query(None, description="作者名稱"),
    limit: int = Query(50, description="返回數量限制"),
    offset: int = Query(0, description="偏移量")
):
    """獲取文章列表."""
    try:
        with db_manager.get_session() as session:
            query = session.query(PTTArticle)
            
            if author:
                query = query.filter(PTTArticle.author == author)
            
            articles = query.order_by(PTTArticle.publish_time.desc()).offset(offset).limit(limit).all()
            
            result = []
            for article in articles:
                result.append({
                    "id": str(article.id),
                    "article_id": article.article_id,
                    "title": article.title,
                    "author": article.author,
                    "board": article.board,
                    "url": article.url,
                    "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                    "push_count": article.push_count,
                    "stock_symbols": article.stock_symbols,
                    "is_analyzed": article.is_analyzed,
                    "llm_sentiment": article.llm_sentiment,
                    "llm_strategy": article.llm_strategy,
                    "recommended_stocks": article.recommended_stocks
                })
            
            return {
                "articles": result,
                "total": len(result),
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articles/{article_id}")
async def get_article(article_id: str):
    """獲取單篇文章詳情."""
    try:
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(
                PTTArticle.article_id == article_id
            ).first()
            
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            
            return {
                "id": str(article.id),
                "article_id": article.article_id,
                "title": article.title,
                "author": article.author,
                "board": article.board,
                "url": article.url,
                "content": article.content,
                "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                "push_count": article.push_count,
                "boo_count": article.boo_count,
                "arrow_count": article.arrow_count,
                "stock_symbols": article.stock_symbols,
                "stock_mentions": article.stock_mentions,
                "category": article.category,
                "tags": article.tags,
                "sentiment": article.sentiment,
                "analysis_result": article.analysis_result,
                "analysis_time": article.analysis_time.isoformat() if article.analysis_time else None,
                "recommended_stocks": article.recommended_stocks,
                "analysis_reason": article.analysis_reason,
                "llm_sentiment": article.llm_sentiment,
                "llm_sectors": article.llm_sectors,
                "llm_strategy": article.llm_strategy,
                "llm_risk_level": article.llm_risk_level,
                "is_processed": article.is_processed,
                "is_analyzed": article.is_analyzed,
                "is_relevant": article.is_relevant
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articles/{article_id}/analysis")
async def get_article_analysis(article_id: str):
    """獲取文章分析結果."""
    try:
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(
                PTTArticle.article_id == article_id
            ).first()
            
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            
            if not article.is_analyzed or not article.analysis_result:
                raise HTTPException(status_code=404, detail="Article analysis not available")
            
            return {
                "author": article.author,
                "date": article.publish_time.strftime('%Y-%m-%d') if article.publish_time else 'N/A',
                "url": article.url,
                "recommended_stocks": article.recommended_stocks or [],
                "reason": article.analysis_reason or "技術分析",
                "llm_analysis": article.analysis_result
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/authors")
async def get_authors():
    """獲取作者列表."""
    try:
        with db_manager.get_session() as session:
            authors = session.query(PTTArticle.author).distinct().all()
            author_list = [author[0] for author in authors]
            
            return {
                "authors": author_list,
                "total": len(author_list)
            }
    except Exception as e:
        logger.error(f"Error getting authors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/authors/{author_name}/articles")
async def get_author_articles(
    author_name: str,
    limit: int = Query(50, description="返回數量限制"),
    offset: int = Query(0, description="偏移量")
):
    """獲取特定作者的文章."""
    try:
        with db_manager.get_session() as session:
            articles = session.query(PTTArticle).filter(
                PTTArticle.author == author_name
            ).order_by(PTTArticle.publish_time.desc()).offset(offset).limit(limit).all()
            
            result = []
            for article in articles:
                result.append({
                    "id": str(article.id),
                    "article_id": article.article_id,
                    "title": article.title,
                    "url": article.url,
                    "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                    "push_count": article.push_count,
                    "stock_symbols": article.stock_symbols,
                    "is_analyzed": article.is_analyzed,
                    "llm_sentiment": article.llm_sentiment,
                    "llm_strategy": article.llm_strategy,
                    "recommended_stocks": article.recommended_stocks
                })
            
            return {
                "author": author_name,
                "articles": result,
                "total": len(result),
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error getting author articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """獲取統計信息."""
    try:
        with db_manager.get_session() as session:
            total_articles = session.query(PTTArticle).count()
            analyzed_articles = session.query(PTTArticle).filter(PTTArticle.is_analyzed == True).count()
            total_authors = session.query(PTTArticle.author).distinct().count()
            
            return {
                "total_articles": total_articles,
                "analyzed_articles": analyzed_articles,
                "total_authors": total_authors,
                "analysis_rate": f"{(analyzed_articles / total_articles * 100):.1f}%" if total_articles > 0 else "0%"
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
