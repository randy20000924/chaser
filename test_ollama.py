#!/usr/bin/env python3
"""測試 Ollama 整合"""

import os
import json
from article_analyzer import ArticleAnalyzer
from database import db_manager
from models import PTTArticle

def test_ollama_integration():
    """測試 Ollama 整合"""
    print("🔍 測試 Ollama 整合...")
    
    # 檢查環境變數
    enable_ollama = os.getenv('ENABLE_OLLAMA', 'false').lower() == 'true'
    ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
    
    print(f"ENABLE_OLLAMA: {enable_ollama}")
    print(f"OLLAMA_MODEL: {ollama_model}")
    
    if not enable_ollama:
        print("❌ 請在 .env 中設定 ENABLE_OLLAMA=true")
        return
    
    # 測試文章
    test_article_id = "M.1759909853.A.234"  # 2429 銘旺科文章
    
    with db_manager.get_session() as session:
        article = session.query(PTTArticle).filter(
            PTTArticle.article_id == test_article_id
        ).first()
        
        if not article:
            print(f"❌ 找不到文章 {test_article_id}")
            return
        
        print(f"📄 測試文章: {article.title}")
        print(f"作者: {article.author}")
        print(f"內容前200字: {article.content[:200]}...")
        print()
        
        # 測試分析器
        analyzer = ArticleAnalyzer()
        
        print("🤖 開始分析...")
        try:
            result = analyzer.analyze_article(test_article_id)
            print("✅ 分析完成!")
            print("📊 結果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 檢查結果
            if result.get('recommended_stocks'):
                print(f"🎯 推薦標的: {result['recommended_stocks']}")
            else:
                print("⚠️  未找到推薦標的")
                
        except Exception as e:
            print(f"❌ 分析失敗: {e}")

if __name__ == "__main__":
    test_ollama_integration()
