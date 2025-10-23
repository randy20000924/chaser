"""MCP 服務器 - 提供 PTT 股票爬蟲和分析功能給 AI 助手."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from config import settings
from database import db_manager
from models import PTTArticle, AuthorProfile
from crawl_orchestrator import CrawlOrchestrator
from article_analyzer import analyzer
from system_detector import system_detector

# 創建 MCP 服務器
mcp_server = Server("ptt-stock-crawler")

class PTTMCPService:
    """PTT 股票爬蟲 MCP 服務."""
    
    def __init__(self):
        self.orchestrator = CrawlOrchestrator()
        self.system_info = system_detector.detect_system()
    
    async def get_system_info(self) -> Dict[str, Any]:
        """獲取系統硬體資訊."""
        return self.system_info
    
    async def crawl_author_articles(self, author: str, days: int = 90) -> Dict[str, Any]:
        """爬取指定作者的文章."""
        try:
            logger.info(f"Crawling articles for author: {author}")
            
            # 動態設置作者
            settings.DYNAMIC_AUTHOR = author
            
            # 執行爬蟲
            result = await self.orchestrator.run_crawl_session()
            
            # 獲取最近的文章
            with db_manager.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days)
                articles = session.query(PTTArticle).filter(
                    PTTArticle.author == author,
                    PTTArticle.publish_time >= cutoff_date
                ).order_by(PTTArticle.publish_time.desc()).all()
                
                articles_data = []
                for article in articles:
                    articles_data.append({
                        "article_id": article.article_id,
                        "title": article.title,
                        "url": article.url,
                        "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                        "push_count": article.push_count,
                        "stock_symbols": article.stock_symbols,
                        "is_analyzed": article.is_analyzed,
                        "recommended_stocks": article.recommended_stocks
                    })
                
                return {
                    "author": author,
                    "articles_found": len(articles_data),
                    "articles": articles_data,
                    "crawl_result": result
                }
                
        except Exception as e:
            logger.error(f"Error crawling author {author}: {e}")
            return {"error": str(e)}
    
    async def analyze_author_recommendations(self, author: str, months: int = 3) -> Dict[str, Any]:
        """分析作者的推薦標的和行業類別."""
        try:
            logger.info(f"Analyzing recommendations for author: {author}")
            
            # 獲取指定時間範圍的文章
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            
            with db_manager.get_session() as session:
                articles = session.query(PTTArticle).filter(
                    PTTArticle.author == author,
                    PTTArticle.publish_time >= cutoff_date,
                    PTTArticle.is_analyzed == True
                ).order_by(PTTArticle.publish_time.desc()).all()
                
                if not articles:
                    return {
                        "author": author,
                        "message": f"未找到作者 {author} 在過去 {months} 個月的分析資料",
                        "recommendations": [],
                        "sectors": [],
                        "market_trends": "無資料"
                    }
                
                # 統計推薦標的
                all_recommendations = []
                all_sectors = []
                market_insights = []
                
                for article in articles:
                    if article.recommended_stocks:
                        all_recommendations.extend(article.recommended_stocks)
                    if hasattr(article, 'llm_sectors') and article.llm_sectors:
                        all_sectors.extend(article.llm_sectors)
                    if hasattr(article, 'llm_strategy') and article.llm_strategy:
                        market_insights.append(article.llm_strategy)
                
                # 統計最常推薦的標的
                from collections import Counter
                recommendation_counts = Counter(all_recommendations)
                top_recommendations = recommendation_counts.most_common(10)
                
                # 統計行業類別
                sector_counts = Counter(all_sectors)
                top_sectors = sector_counts.most_common(5)
                
                return {
                    "author": author,
                    "period": f"過去 {months} 個月",
                    "articles_analyzed": len(articles),
                    "top_recommendations": [{"stock": stock, "count": count} for stock, count in top_recommendations],
                    "top_sectors": [{"sector": sector, "count": count} for sector, count in top_sectors],
                    "market_trends": market_insights[-5:] if market_insights else ["無市場分析資料"],
                    "analysis_summary": f"作者 {author} 在過去 {months} 個月共發表 {len(articles)} 篇分析文章，"
                                     f"最常推薦的標的為 {top_recommendations[0][0] if top_recommendations else '無'}，"
                                     f"主要關注 {top_sectors[0][0] if top_sectors else '無'} 行業"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing author {author}: {e}")
            return {"error": str(e)}
    
    async def get_author_list(self) -> Dict[str, Any]:
        """獲取所有作者列表."""
        try:
            with db_manager.get_session() as session:
                authors = session.query(PTTArticle.author).distinct().all()
                author_list = [author[0] for author in authors]
                
                return {
                    "authors": author_list,
                    "total": len(author_list)
                }
        except Exception as e:
            logger.error(f"Error getting author list: {e}")
            return {"error": str(e)}

# 創建服務實例
ptt_service = PTTMCPService()

# 註冊 MCP 工具
@mcp_server.tool()
async def get_system_info() -> str:
    """獲取系統硬體資訊和推薦的 Qwen 模型."""
    try:
        system_info = await ptt_service.get_system_info()
        return json.dumps(system_info, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp_server.tool()
async def crawl_author_articles(author: str, days: int = 90) -> str:
    """爬取指定作者的文章。
    
    Args:
        author: 作者名稱
        days: 爬取天數，預設 90 天
    """
    try:
        result = await ptt_service.crawl_author_articles(author, days)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp_server.tool()
async def analyze_author_recommendations(author: str, months: int = 3) -> str:
    """分析作者的推薦標的、行業類別和市場動向。
    
    Args:
        author: 作者名稱
        months: 分析月份數，預設 3 個月
    """
    try:
        result = await ptt_service.analyze_author_recommendations(author, months)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp_server.tool()
async def get_author_list() -> str:
    """獲取所有作者列表."""
    try:
        result = await ptt_service.get_author_list()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp_server.tool()
async def search_author_articles(author: str, limit: int = 50) -> str:
    """搜尋指定作者的文章。
    
    Args:
        author: 作者名稱
        limit: 返回文章數量限制
    """
    try:
        with db_manager.get_session() as session:
            articles = session.query(PTTArticle).filter(
                PTTArticle.author == author
            ).order_by(PTTArticle.publish_time.desc()).limit(limit).all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "url": article.url,
                    "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                    "push_count": article.push_count,
                    "stock_symbols": article.stock_symbols,
                    "is_analyzed": article.is_analyzed,
                    "recommended_stocks": article.recommended_stocks
                })
            
            return json.dumps({
                "author": author,
                "articles": articles_data,
                "total": len(articles_data)
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# 註冊 MCP 資源
@mcp_server.resource("ptt://authors")
async def get_authors_resource() -> str:
    """獲取所有作者的資源."""
    try:
        result = await ptt_service.get_author_list()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp_server.resource("ptt://articles/{author}")
async def get_author_articles_resource(author: str) -> str:
    """獲取指定作者文章的資源."""
    try:
        result = await ptt_service.search_author_articles(author)
        return result
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# 註冊 MCP 提示詞
@mcp_server.prompt()
async def stock_analysis_prompt(article_content: str) -> str:
    """股票分析提示詞模板."""
    return f"""
請分析以下 PTT 股票版文章，並提供投資建議：

文章內容：
{article_content}

請從以下角度分析：
1. 技術面分析
2. 基本面分析  
3. 消息面影響
4. 推薦標的
5. 風險評估
6. 投資策略

請用繁體中文回答，並提供具體的投資建議。
"""

@mcp_server.prompt()
async def author_summary_prompt(author: str) -> str:
    """作者摘要提示詞."""
    return f"""
請分析作者 {author} 的投資風格和推薦模式：

1. 投資風格分析
2. 推薦標的偏好
3. 行業關注重點
4. 市場觀點
5. 投資策略特點

請提供詳細的分析報告。
"""

async def main():
    """啟動 MCP 服務器."""
    logger.info("Starting PTT Stock Crawler MCP Server...")
    
    # 初始化資料庫
    db_manager.create_tables()
    
    # 檢測系統硬體
    system_info = system_detector.detect_system()
    logger.info(f"System detected: {system_info['recommended_model']}")
    
    # 啟動 MCP 服務器
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
