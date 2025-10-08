#!/usr/bin/env python3
"""文章選擇器 - 自由選擇文章進行分析."""

import sys
from database import db_manager
from models import PTTArticle
from sqlalchemy import desc, func
from article_analyzer import ArticleAnalyzer
from datetime import datetime, timedelta


class ArticleSelector:
    """文章選擇器."""
    
    def __init__(self):
        self.analyzer = ArticleAnalyzer()
    
    def list_articles(self, author=None, limit=20):
        """列出文章."""
        with db_manager.get_session() as session:
            query = session.query(PTTArticle)
            
            if author:
                query = query.filter(PTTArticle.author == author)
            
            articles = query.order_by(desc(PTTArticle.publish_time)).limit(limit).all()
            
            print(f"📰 文章列表 ({len(articles)} 篇):")
            print("=" * 80)
            
            for i, article in enumerate(articles, 1):
                print(f"{i:2d}. {article.title}")
                print(f"    作者: {article.author}")
                print(f"    時間: {article.publish_time}")
                print(f"    推文: {article.push_count}")
                print(f"    股票: {article.stock_symbols}")
                print(f"    URL: {article.url}")
                print("-" * 80)
            
            return articles
    
    def analyze_article(self, article):
        """分析文章."""
        print(f"\n🔍 分析文章: {article.title}")
        print("=" * 80)
        
        # 使用分析器分析文章
        analysis = self.analyzer._analyze_content(article)
        
        print("📊 基本資訊:")
        print(f"  標題: {analysis['title']}")
        print(f"  作者: {analysis['author']}")
        print(f"  時間: {analysis['publish_time']}")
        print(f"  推文數: {analysis['push_count']}")
        print(f"  URL: {analysis['url']}")
        
        print("\n🎯 投資分析:")
        print(f"  股票代碼: {analysis['analysis']['stocks']['mentioned_stocks']}")
        print(f"  投資策略: {analysis['analysis']['strategy']['strategy_type']}")
        print(f"  情感傾向: {analysis['analysis']['sentiment']['sentiment']}")
        print(f"  產業類別: {analysis['analysis']['sectors']}")
        
        print("\n💡 投資建議:")
        recommendations = analysis['analysis']['recommendations']
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['context']}: {rec['value']}")
        else:
            print("  無明確投資建議")
        
        print("\n⚠️ 風險提示:")
        risks = analysis['analysis']['risks']
        if risks:
            print(f"  風險關鍵詞: {', '.join(risks)}")
        else:
            print("  無明顯風險提示")
        
        print(f"\n⏰ 時間框架: {analysis['analysis']['time_horizon']}")
        
        print("\n📝 投資論述:")
        thesis = analysis['analysis']['investment_thesis']
        if thesis and thesis != "未找到明確投資論述":
            print(f"  {thesis[:200]}...")
        else:
            print("  無明確投資論述")
        
        print("\n💰 價格目標:")
        price_targets = analysis['analysis']['price_targets']
        if price_targets:
            for target in price_targets:
                print(f"  {target['context']}: {target['price']}")
        else:
            print("  無明確價格目標")
    
    def show_authors(self):
        """顯示作者列表."""
        with db_manager.get_session() as session:
            author_stats = session.query(
                PTTArticle.author,
                func.count(PTTArticle.id).label('count')
            ).group_by(PTTArticle.author).order_by(desc('count')).all()
            
            print("👥 作者列表:")
            print("=" * 50)
            for i, (author, count) in enumerate(author_stats, 1):
                print(f"{i:2d}. {author} ({count} 篇文章)")
            print("-" * 50)
            
            return [author for author, _ in author_stats]
    
    def show_high_push_articles(self):
        """顯示高推文文章."""
        with db_manager.get_session() as session:
            articles = session.query(PTTArticle).filter(
                PTTArticle.push_count >= 50
            ).order_by(desc(PTTArticle.push_count)).limit(20).all()
            
            print("🔥 高推文文章 (推文數 >= 50):")
            print("=" * 80)
            
            for i, article in enumerate(articles, 1):
                print(f"{i:2d}. {article.title}")
                print(f"    作者: {article.author}")
                print(f"    推文: {article.push_count}")
                print(f"    時間: {article.publish_time}")
                print("-" * 80)
            
            return articles
    
    def show_recent_articles(self):
        """顯示最近文章."""
        with db_manager.get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=7)
            articles = session.query(PTTArticle).filter(
                PTTArticle.publish_time >= cutoff_date
            ).order_by(desc(PTTArticle.publish_time)).limit(20).all()
            
            print("📅 最近 7 天的文章:")
            print("=" * 80)
            
            for i, article in enumerate(articles, 1):
                print(f"{i:2d}. {article.title}")
                print(f"    作者: {article.author}")
                print(f"    推文: {article.push_count}")
                print(f"    時間: {article.publish_time}")
                print("-" * 80)
            
            return articles


def main():
    """主函數."""
    if len(sys.argv) < 2:
        print("🔍 文章選擇器使用方式:")
        print("=" * 50)
        print("python article_selector.py list [作者] [數量]")
        print("python article_selector.py analyze <文章編號>")
        print("python article_selector.py authors")
        print("python article_selector.py high")
        print("python article_selector.py recent")
        print()
        print("範例:")
        print("  python article_selector.py list mrp 10")
        print("  python article_selector.py analyze 1")
        print("  python article_selector.py authors")
        return
    
    selector = ArticleSelector()
    command = sys.argv[1]
    
    if command == "list":
        author = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        articles = selector.list_articles(author=author, limit=limit)
        
        if articles:
            print(f"\n💡 使用 'python article_selector.py analyze <編號>' 來分析特定文章")
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("❌ 請提供文章編號")
            return
        
        try:
            article_num = int(sys.argv[2])
            # 預設顯示 mrp 的文章
            articles = selector.list_articles(author="mrp", limit=30)
            
            if 1 <= article_num <= len(articles):
                selected_article = articles[article_num - 1]
                selector.analyze_article(selected_article)
            else:
                print(f"❌ 文章編號超出範圍 (1-{len(articles)})")
        except ValueError:
            print("❌ 請輸入有效的文章編號")
    
    elif command == "authors":
        selector.show_authors()
    
    elif command == "high":
        articles = selector.show_high_push_articles()
        if articles:
            print(f"\n💡 使用 'python article_selector.py analyze <編號>' 來分析特定文章")
    
    elif command == "recent":
        articles = selector.show_recent_articles()
        if articles:
            print(f"\n💡 使用 'python article_selector.py analyze <編號>' 來分析特定文章")
    
    else:
        print("❌ 未知命令")


if __name__ == "__main__":
    main()
