#!/usr/bin/env python3
"""HTTP MCP Server 實作."""

import asyncio
import json
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import db_manager
from models import PTTArticle, AuthorProfile, CrawlLog
from loguru import logger
from article_analyzer import ArticleAnalyzer
from config import settings

app = FastAPI(title="PTT Stock Crawler MCP Server", version="1.0.0")

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = ArticleAnalyzer()

@app.get("/")
async def root():
    return {"message": "PTT Stock Crawler MCP Server", "version": "1.0.0"}

@app.get("/tools")
async def list_tools():
    """列出可用工具."""
    return {
        "tools": [
            {
                "name": "search_articles",
                "description": "搜尋PTT文章",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "author": {"type": "string", "description": "作者名稱"},
                        "stock_code": {"type": "string", "description": "股票代碼"},
                        "days": {"type": "integer", "description": "搜尋天數", "default": 7},
                        "limit": {"type": "integer", "description": "結果數量限制", "default": 20}
                    }
                }
            },
            {
                "name": "analyze_article",
                "description": "分析文章內容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_id": {"type": "string", "description": "文章ID"}
                    },
                    "required": ["article_id"]
                }
            },
            {
                "name": "get_all_authors",
                "description": "取得所有作者列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

@app.post("/tools/search_articles")
async def search_articles(request: Dict[str, Any]):
    """搜尋文章."""
    try:
        author = request.get("author")
        stock_code = request.get("stock_code")
        days = request.get("days", 7)
        limit = request.get("limit", 20)
        
        with db_manager.get_session() as session:
            query = session.query(PTTArticle)
            
            if author:
                query = query.filter(PTTArticle.author == author)
            
            if stock_code:
                query = query.filter(PTTArticle.content.contains(stock_code))
            
            # 時間過濾
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(PTTArticle.publish_time >= cutoff_date)
            
            articles = query.order_by(PTTArticle.publish_time.desc()).limit(limit).all()
            
            result = []
            for article in articles:
                result.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "author": article.author,
                    "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                    "url": article.url,
                    "push_count": article.push_count
                })
            
            return {"articles": result, "total": len(result)}
            
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/analyze_article")
async def analyze_article(request: Dict[str, Any]):
    """分析文章."""
    try:
        article_id = request.get("article_id")
        if not article_id:
            raise HTTPException(status_code=400, detail="article_id is required")
        
        result = analyzer.analyze_article(article_id)
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing article: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/get_all_authors")
async def get_all_authors():
    """取得所有作者列表."""
    try:
        with db_manager.get_session() as session:
            from sqlalchemy import func
            authors = session.query(
                PTTArticle.author,
                func.count(PTTArticle.article_id).label('article_count'),
                func.max(PTTArticle.publish_time).label('last_activity')
            ).group_by(PTTArticle.author).order_by(
                func.count(PTTArticle.article_id).desc()
            ).all()
            
            authors_list = []
            for author, count, last_activity in authors:
                authors_list.append({
                    "author": author,
                    "article_count": count,
                    "last_activity": last_activity.isoformat() if last_activity else None
                })
            
            return {
                "authors": authors_list,
                "total": len(authors_list)
            }
            
    except Exception as e:
        logger.error(f"Error getting all authors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting HTTP MCP Server on {settings.mcp_server_host}:{settings.mcp_server_port}")
    uvicorn.run(app, host=settings.mcp_server_host, port=settings.mcp_server_port)
