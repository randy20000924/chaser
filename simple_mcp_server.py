#!/usr/bin/env python3
"""簡化的 MCP Server 實作."""

import asyncio
import json
import sys
from typing import List, Dict, Any
from database import db_manager
from models import PTTArticle, AuthorProfile, CrawlLog
from loguru import logger
from article_analyzer import ArticleAnalyzer


class SimpleMCPServer:
    """簡化的 MCP Server."""
    
    def __init__(self):
        self.name = "ptt-stock-crawler"
        self.version = "1.0.0"
        self.analyzer = ArticleAnalyzer()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """處理 MCP 請求."""
        try:
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "tools/list":
                return await self.list_tools()
            elif method == "tools/call":
                return await self.call_tool(params)
            elif method == "resources/list":
                return await self.list_resources()
            elif method == "resources/read":
                return await self.read_resource(params)
            else:
                return {"error": f"Unknown method: {method}"}
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {"error": str(e)}
    
    async def list_tools(self) -> Dict[str, Any]:
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
                            "limit": {"type": "integer", "description": "結果數量限制", "default": 10}
                        }
                    }
                },
                {
                    "name": "analyze_author_activity",
                    "description": "分析作者活動模式",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "author": {"type": "string", "description": "作者名稱"},
                            "days": {"type": "integer", "description": "分析天數", "default": 30}
                        }
                    }
                },
                {
                    "name": "get_stock_mentions",
                    "description": "取得股票提及統計",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "統計天數", "default": 7}
                        }
                    }
                },
                {
                    "name": "analyze_article",
                    "description": "深度分析文章內容，提取投資標的、策略和風險",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "article_id": {
                                "type": "string",
                                "description": "文章ID"
                            }
                        },
                        "required": ["article_id"]
                    }
                },
                {
                    "name": "analyze_author_profile",
                    "description": "分析作者投資偏好和風格",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "author": {
                                "type": "string",
                                "description": "作者名稱"
                            }
                        },
                        "required": ["author"]
                    }
                }
            ]
        }
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """調用工具."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "search_articles":
                return await self.search_articles(arguments)
            elif tool_name == "analyze_author_activity":
                return await self.analyze_author_activity(arguments)
            elif tool_name == "get_stock_mentions":
                return await self.get_stock_mentions(arguments)
            elif tool_name == "analyze_article":
                return self.analyzer.analyze_article(arguments["article_id"])
            elif tool_name == "analyze_author_profile":
                return self.analyzer.get_author_investment_profile(arguments["author"])
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def search_articles(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """搜尋文章."""
        author = args.get("author")
        limit = args.get("limit", 10)
        
        with db_manager.get_session() as session:
            query = session.query(PTTArticle)
            if author:
                query = query.filter(PTTArticle.author == author)
            
            articles = query.order_by(PTTArticle.publish_time.desc()).limit(limit).all()
            
            results = []
            for article in articles:
                results.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "author": article.author,
                    "publish_time": article.publish_time.isoformat(),
                    "stock_symbols": article.stock_symbols,
                    "push_count": article.push_count,
                    "url": article.url
                })
            
            return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)}]}
    
    async def analyze_author_activity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """分析作者活動."""
        author = args.get("author")
        days = args.get("days", 30)
        
        with db_manager.get_session() as session:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            articles = session.query(PTTArticle).filter(
                PTTArticle.author == author,
                PTTArticle.publish_time >= cutoff_date
            ).all()
            
            if not articles:
                return {"content": [{"type": "text", "text": f"作者 {author} 在最近 {days} 天內沒有發文"}]}
            
            # 統計分析
            total_articles = len(articles)
            total_push = sum(article.push_count for article in articles)
            avg_push = total_push / total_articles if total_articles > 0 else 0
            
            # 股票提及統計
            stock_mentions = {}
            for article in articles:
                if article.stock_symbols:
                    for symbol in article.stock_symbols:
                        stock_mentions[symbol] = stock_mentions.get(symbol, 0) + 1
            
            analysis = {
                "author": author,
                "period_days": days,
                "total_articles": total_articles,
                "total_push_count": total_push,
                "average_push_count": round(avg_push, 2),
                "stock_mentions": stock_mentions,
                "most_mentioned_stocks": sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            return {"content": [{"type": "text", "text": json.dumps(analysis, ensure_ascii=False, indent=2)}]}
    
    async def get_stock_mentions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """取得股票提及統計."""
        days = args.get("days", 7)
        
        with db_manager.get_session() as session:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            articles = session.query(PTTArticle).filter(
                PTTArticle.publish_time >= cutoff_date
            ).all()
            
            stock_stats = {}
            for article in articles:
                if article.stock_symbols:
                    for symbol in article.stock_symbols:
                        stock_stats[symbol] = stock_stats.get(symbol, 0) + 1
            
            ranking = sorted(stock_stats.items(), key=lambda x: x[1], reverse=True)
            
            result = {
                "period_days": days,
                "total_unique_stocks": len(stock_stats),
                "stock_ranking": ranking[:10]  # 前10名
            }
            
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}
    
    async def list_resources(self) -> Dict[str, Any]:
        """列出資源."""
        return {
            "resources": [
                {
                    "uri": "ptt://articles",
                    "name": "PTT Articles",
                    "description": "PTT股票版文章資料",
                    "mimeType": "application/json"
                }
            ]
        }
    
    async def read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """讀取資源."""
        uri = params.get("uri")
        if uri == "ptt://articles":
            with db_manager.get_session() as session:
                articles = session.query(PTTArticle).limit(5).all()
                data = []
                for article in articles:
                    data.append({
                        "article_id": article.article_id,
                        "title": article.title,
                        "author": article.author,
                        "publish_time": article.publish_time.isoformat()
                    })
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(data, ensure_ascii=False, indent=2)}]}
        else:
            return {"error": f"Unknown resource: {uri}"}
    
    async def run(self):
        """執行簡化的 MCP Server."""
        logger.info("Starting Simple MCP Server...")
        
        # 簡單的 JSON-RPC 處理
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                
                # 添加請求ID
                if "id" in request:
                    response["id"] = request["id"]
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Server error: {e}")
                break
        
        logger.info("Simple MCP Server stopped")


async def main():
    """主函數."""
    server = SimpleMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
