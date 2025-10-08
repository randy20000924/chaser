#!/usr/bin/env python3
"""查看系統輸出的腳本."""

import asyncio
from article_analyzer import ArticleAnalyzer
from simple_mcp_server import SimpleMCPServer


def show_articles():
    """顯示文章列表."""
    from quick_query import show_mrp_articles
    show_mrp_articles()


def show_stats():
    """顯示統計資訊."""
    from quick_query import show_stats
    show_stats()


def show_analysis():
    """顯示文章分析."""
    analyzer = ArticleAnalyzer()
    
    # 分析特定文章
    analysis = analyzer.analyze_article_by_url("https://www.ptt.cc/bbs/Stock/M.1759822323.A.E44.html")
    
    print("📊 文章分析結果:")
    print(f"標題: {analysis['title']}")
    print(f"作者: {analysis['author']}")
    print(f"推文數: {analysis['push_count']}")
    print()
    print("🔍 深度分析:")
    print(f"股票代碼: {analysis['analysis']['stocks']['mentioned_stocks']}")
    print(f"投資策略: {analysis['analysis']['strategy']['strategy_type']}")
    print(f"情感傾向: {analysis['analysis']['sentiment']['sentiment']}")
    print(f"產業類別: {analysis['analysis']['sectors']}")
    print(f"投資建議: {len(analysis['analysis']['recommendations'])} 項")
    print(f"風險提示: {analysis['analysis']['risks']}")
    print(f"時間框架: {analysis['analysis']['time_horizon']}")


async def show_mcp_analysis():
    """顯示 MCP 分析結果."""
    server = SimpleMCPServer()
    
    # 測試搜尋文章
    print("🔍 MCP Server 搜尋結果:")
    response = await server.handle_request({
        "method": "tools/call",
        "params": {
            "name": "search_articles",
            "arguments": {"author": "mrp", "limit": 3}
        }
    })
    
    if "content" in response:
        import json
        articles = json.loads(response["content"][0]["text"])
        print(f"找到 {len(articles)} 篇文章:")
        for article in articles:
            print(f"📰 {article['title']} (推文: {article['push_count']})")
    
    # 測試分析文章
    print("\n📊 MCP Server 分析結果:")
    analysis_response = await server.handle_request({
        "method": "tools/call",
        "params": {
            "name": "analyze_article",
            "arguments": {"article_id": "M.1759822323.A.E44"}
        }
    })
    
    if "error" not in analysis_response:
        analysis = analysis_response
        print(f"✅ 分析完成: {analysis['title']}")
        print(f"股票代碼: {analysis['analysis']['stocks']['mentioned_stocks']}")
        print(f"投資策略: {analysis['analysis']['strategy']['strategy_type']}")
        print(f"產業類別: {analysis['analysis']['sectors']}")


def main():
    """主選單."""
    print("🔍 PTT 股票爬蟲系統 - 查看輸出")
    print("=" * 50)
    print("1. 查看 mrp 作者文章")
    print("2. 查看統計資訊")
    print("3. 查看文章分析")
    print("4. 查看 MCP 分析結果")
    print("5. 查看所有輸出")
    print("0. 退出")
    
    choice = input("\n請選擇 (0-5): ").strip()
    
    if choice == "1":
        show_articles()
    elif choice == "2":
        show_stats()
    elif choice == "3":
        show_analysis()
    elif choice == "4":
        asyncio.run(show_mcp_analysis())
    elif choice == "5":
        print("\n📰 1. mrp 作者文章:")
        show_articles()
        print("\n📊 2. 統計資訊:")
        show_stats()
        print("\n🔍 3. 文章分析:")
        show_analysis()
        print("\n🤖 4. MCP 分析結果:")
        asyncio.run(show_mcp_analysis())
    elif choice == "0":
        print("👋 再見！")
    else:
        print("❌ 無效選擇")


if __name__ == "__main__":
    main()
