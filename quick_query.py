#!/usr/bin/env python3
"""快速資料庫查詢."""

from database import db_manager
from models import PTTArticle
from sqlalchemy import desc, func


def show_mrp_articles():
    """顯示 mrp 作者的文章."""
    with db_manager.get_session() as session:
        articles = session.query(PTTArticle).filter(
            PTTArticle.author == 'mrp'
        ).order_by(desc(PTTArticle.publish_time)).all()
        
        print(f"📰 mrp 作者的文章 ({len(articles)} 篇):")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            print(f"{i:2d}. {article.title}")
            print(f"    時間: {article.publish_time}")
            print(f"    推文: {article.push_count}")
            print(f"    股票: {article.stock_symbols}")
            print(f"    URL: {article.url}")
            print("-" * 80)


def show_recent_articles():
    """顯示最近的文章."""
    with db_manager.get_session() as session:
        articles = session.query(PTTArticle).order_by(
            desc(PTTArticle.publish_time)
        ).limit(10).all()
        
        print("📰 最近的文章:")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            print(f"{i:2d}. {article.title}")
            print(f"    作者: {article.author}")
            print(f"    時間: {article.publish_time}")
            print(f"    推文: {article.push_count}")
            print(f"    URL: {article.url}")
            print("-" * 80)


def show_stats():
    """顯示統計資訊."""
    with db_manager.get_session() as session:
        # 總文章數
        total_articles = session.query(PTTArticle).count()
        
        # 作者統計
        author_stats = session.query(
            PTTArticle.author,
            func.count(PTTArticle.id).label('count')
        ).group_by(PTTArticle.author).all()
        
        # 總推文數
        total_push = session.query(func.sum(PTTArticle.push_count)).scalar() or 0
        
        print("📊 資料庫統計:")
        print("=" * 80)
        print(f"總文章數: {total_articles}")
        print(f"總推文數: {total_push}")
        print("\n作者統計:")
        for author, count in author_stats:
            print(f"  {author}: {count} 篇")
        print("-" * 80)


if __name__ == "__main__":
    print("🔍 快速資料庫查詢")
    print("1. 顯示 mrp 文章")
    print("2. 顯示最近文章")
    print("3. 顯示統計資訊")
    
    import sys
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("請選擇 (1-3): ").strip()
    
    if choice == "1":
        show_mrp_articles()
    elif choice == "2":
        show_recent_articles()
    elif choice == "3":
        show_stats()
    else:
        print("❌ 無效選擇")
