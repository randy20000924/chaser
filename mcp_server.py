"""MCP Server for PTT Stock Crawler."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from loguru import logger

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, ListResourcesRequest, ReadResourceRequest
)

from database import db_manager
from models import PTTArticle, AuthorProfile, CrawlLog
from article_analyzer import ArticleAnalyzer


class PTTStockMCPServer:
    """PTT股票爬蟲MCP Server."""
    
    def __init__(self):
        self.server = Server("ptt-stock-crawler")
        self.analyzer = ArticleAnalyzer()
        self.setup_handlers()
    
    def setup_handlers(self):
        """設定MCP處理器."""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """列出可用資源."""
            return [
                Resource(
                    uri="ptt://articles",
                    name="PTT Articles",
                    description="PTT股票版文章資料",
                    mimeType="application/json"
                ),
                Resource(
                    uri="ptt://authors",
                    name="PTT Authors",
                    description="追蹤的作者列表",
                    mimeType="application/json"
                ),
                Resource(
                    uri="ptt://crawl-logs",
                    name="Crawl Logs",
                    description="爬蟲執行日誌",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """讀取資源內容."""
            if uri == "ptt://articles":
                return await self.get_articles_summary()
            elif uri == "ptt://authors":
                return await self.get_authors_summary()
            elif uri == "ptt://crawl-logs":
                return await self.get_crawl_logs_summary()
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出可用工具."""
            return [
                Tool(
                    name="search_articles",
                    description="搜尋PTT文章",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "author": {
                                "type": "string",
                                "description": "作者名稱"
                            },
                            "stock_symbol": {
                                "type": "string",
                                "description": "股票代碼"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "開始日期 (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "結束日期 (YYYY-MM-DD)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "結果數量限制",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="get_article_content",
                    description="取得特定文章內容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "article_id": {
                                "type": "string",
                                "description": "文章ID"
                            }
                        },
                        "required": ["article_id"]
                    }
                ),
                Tool(
                    name="analyze_author_activity",
                    description="分析作者活動模式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "author": {
                                "type": "string",
                                "description": "作者名稱"
                            },
                            "days": {
                                "type": "integer",
                                "description": "分析天數",
                                "default": 30
                            }
                        },
                        "required": ["author"]
                    }
                ),
                Tool(
                    name="get_stock_mentions",
                    description="取得股票提及統計",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "stock_symbol": {
                                "type": "string",
                                "description": "股票代碼"
                            },
                            "days": {
                                "type": "integer",
                                "description": "統計天數",
                                "default": 7
                            }
                        },
                        "required": ["stock_symbol"]
                    }
                ),
                       Tool(
                           name="classify_article",
                           description="分類文章內容",
                           inputSchema={
                               "type": "object",
                               "properties": {
                                   "article_id": {
                                       "type": "string",
                                       "description": "文章ID"
                                   }
                               },
                               "required": ["article_id"]
                           }
                       ),
                       Tool(
                           name="analyze_article",
                           description="深度分析文章內容，提取投資標的、策略和風險",
                           inputSchema={
                               "type": "object",
                               "properties": {
                                   "article_id": {
                                       "type": "string",
                                       "description": "文章ID"
                                   }
                               },
                               "required": ["article_id"]
                           }
                       ),
                       Tool(
                           name="analyze_author_profile",
                           description="分析作者投資偏好和風格",
                           inputSchema={
                               "type": "object",
                               "properties": {
                                   "author": {
                                       "type": "string",
                                       "description": "作者名稱"
                                   }
                               },
                               "required": ["author"]
                           }
                       ),
                       Tool(
                           name="batch_analyze_articles",
                           description="批量分析多篇文章",
                           inputSchema={
                               "type": "object",
                               "properties": {
                                   "author": {
                                       "type": "string",
                                       "description": "作者名稱（可選）"
                                   },
                                   "limit": {
                                       "type": "integer",
                                       "description": "分析文章數量限制",
                                       "default": 10
                                   }
                               }
                           }
                       )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """執行工具."""
            try:
                if name == "search_articles":
                    result = await self.search_articles(**arguments)
                elif name == "get_article_content":
                    result = await self.get_article_content(**arguments)
                elif name == "analyze_author_activity":
                    result = await self.analyze_author_activity(**arguments)
                elif name == "get_stock_mentions":
                    result = await self.get_stock_mentions(**arguments)
                elif name == "classify_article":
                    result = await self.classify_article(**arguments)
                elif name == "analyze_article":
                    result = self.analyzer.analyze_article(**arguments)
                elif name == "analyze_author_profile":
                    result = self.analyzer.get_author_investment_profile(**arguments)
                elif name == "batch_analyze_articles":
                    result = self.analyzer.batch_analyze_articles(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_articles_summary(self) -> str:
        """取得文章摘要."""
        with db_manager.get_session() as session:
            total_articles = session.query(PTTArticle).count()
            recent_articles = session.query(PTTArticle).order_by(desc(PTTArticle.publish_time)).limit(5).all()
            
            summary = {
                "total_articles": total_articles,
                "recent_articles": [
                    {
                        "title": article.title,
                        "author": article.author,
                        "publish_time": article.publish_time.isoformat(),
                        "stock_symbols": article.stock_symbols
                    }
                    for article in recent_articles
                ]
            }
            
            return json.dumps(summary, ensure_ascii=False, indent=2)
    
    async def get_authors_summary(self) -> str:
        """取得作者摘要."""
        with db_manager.get_session() as session:
            authors = session.query(AuthorProfile).all()
            
            summary = {
                "tracked_authors": [
                    {
                        "username": author.username,
                        "display_name": author.display_name,
                        "is_active": author.is_active,
                        "total_articles": author.total_articles,
                        "last_activity": author.last_activity.isoformat() if author.last_activity else None
                    }
                    for author in authors
                ]
            }
            
            return json.dumps(summary, ensure_ascii=False, indent=2)
    
    async def get_crawl_logs_summary(self) -> str:
        """取得爬蟲日誌摘要."""
        with db_manager.get_session() as session:
            recent_logs = session.query(CrawlLog).order_by(desc(CrawlLog.crawl_time)).limit(10).all()
            
            summary = {
                "recent_crawls": [
                    {
                        "crawl_time": log.crawl_time.isoformat(),
                        "target_authors": log.target_authors,
                        "articles_found": log.articles_found,
                        "articles_saved": log.articles_saved,
                        "status": log.status,
                        "duration_seconds": log.duration_seconds
                    }
                    for log in recent_logs
                ]
            }
            
            return json.dumps(summary, ensure_ascii=False, indent=2)
    
    async def search_articles(self, author: str = None, stock_symbol: str = None, 
                            start_date: str = None, end_date: str = None, limit: int = 10) -> Dict:
        """搜尋文章."""
        with db_manager.get_session() as session:
            query = session.query(PTTArticle)
            
            # 應用篩選條件
            if author:
                query = query.filter(PTTArticle.author == author)
            
            if stock_symbol:
                query = query.filter(PTTArticle.stock_symbols.contains([stock_symbol]))
            
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(PTTArticle.publish_time >= start_dt)
            
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(PTTArticle.publish_time <= end_dt)
            
            # 排序和限制
            articles = query.order_by(desc(PTTArticle.publish_time)).limit(limit).all()
            
            return {
                "articles": [
                    {
                        "article_id": article.article_id,
                        "title": article.title,
                        "author": article.author,
                        "publish_time": article.publish_time.isoformat(),
                        "stock_symbols": article.stock_symbols,
                        "push_count": article.push_count,
                        "url": article.url,
                        "content_preview": article.content[:200] + "..." if article.content and len(article.content) > 200 else article.content
                    }
                    for article in articles
                ],
                "total_found": len(articles)
            }
    
    async def get_article_content(self, article_id: str) -> Dict:
        """取得文章完整內容."""
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(PTTArticle.article_id == article_id).first()
            
            if not article:
                return {"error": "Article not found"}
            
            return {
                "article_id": article.article_id,
                "title": article.title,
                "author": article.author,
                "publish_time": article.publish_time.isoformat(),
                "content": article.content,
                "stock_symbols": article.stock_symbols,
                "push_count": article.push_count,
                "boo_count": article.boo_count,
                "arrow_count": article.arrow_count,
                "url": article.url,
                "category": article.category,
                "tags": article.tags,
                "sentiment": article.sentiment
            }
    
    async def analyze_author_activity(self, author: str, days: int = 30) -> Dict:
        """分析作者活動模式."""
        with db_manager.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            
            # 取得作者文章
            articles = session.query(PTTArticle).filter(
                and_(
                    PTTArticle.author == author,
                    PTTArticle.publish_time >= start_date
                )
            ).order_by(PTTArticle.publish_time).all()
            
            if not articles:
                return {"error": "No articles found for this author in the specified period"}
            
            # 統計分析
            total_articles = len(articles)
            stock_mentions = {}
            daily_activity = {}
            
            for article in articles:
                # 統計股票提及
                if article.stock_symbols:
                    for symbol in article.stock_symbols:
                        stock_mentions[symbol] = stock_mentions.get(symbol, 0) + 1
                
                # 統計每日活動
                date_key = article.publish_time.date().isoformat()
                daily_activity[date_key] = daily_activity.get(date_key, 0) + 1
            
            # 最常提及的股票
            top_stocks = sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "author": author,
                "period_days": days,
                "total_articles": total_articles,
                "avg_articles_per_day": round(total_articles / days, 2),
                "top_stocks": top_stocks,
                "daily_activity": daily_activity,
                "most_active_day": max(daily_activity.items(), key=lambda x: x[1]) if daily_activity else None
            }
    
    async def get_stock_mentions(self, stock_symbol: str, days: int = 7) -> Dict:
        """取得股票提及統計."""
        with db_manager.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            
            # 搜尋提及該股票的文章
            articles = session.query(PTTArticle).filter(
                and_(
                    PTTArticle.stock_symbols.contains([stock_symbol]),
                    PTTArticle.publish_time >= start_date
                )
            ).order_by(desc(PTTArticle.publish_time)).all()
            
            # 統計作者提及次數
            author_mentions = {}
            for article in articles:
                author_mentions[article.author] = author_mentions.get(article.author, 0) + 1
            
            # 最常提及的作者
            top_authors = sorted(author_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "stock_symbol": stock_symbol,
                "period_days": days,
                "total_mentions": len(articles),
                "unique_authors": len(author_mentions),
                "top_authors": top_authors,
                "recent_articles": [
                    {
                        "title": article.title,
                        "author": article.author,
                        "publish_time": article.publish_time.isoformat(),
                        "url": article.url
                    }
                    for article in articles[:10]
                ]
            }
    
    async def classify_article(self, article_id: str) -> Dict:
        """分類文章內容（預留給LLM整合）."""
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(PTTArticle.article_id == article_id).first()
            
            if not article:
                return {"error": "Article not found"}
            
            # 這裡預留給LLM分類邏輯
            # 目前返回基本分類資訊
            return {
                "article_id": article_id,
                "title": article.title,
                "author": article.author,
                "current_category": article.category,
                "current_tags": article.tags,
                "current_sentiment": article.sentiment,
                "content_preview": article.content[:500] + "..." if article.content and len(article.content) > 500 else article.content,
                "note": "LLM classification not yet implemented"
            }
    
    async def run(self):
        """執行MCP Server."""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="ptt-stock-crawler",
                        server_version="1.0.0"
                    )
                )
        except Exception as e:
            logger.error(f"MCP Server stdio error: {e}")
            # 如果 stdio 失敗，嘗試其他方式
            raise


async def main():
    """執行MCP Server."""
    server = PTTStockMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
