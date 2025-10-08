#!/usr/bin/env python3
"""文章分析模組 - 分析PTT文章中的投資標的和策略."""

import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
from database import db_manager
from models import PTTArticle
from sqlalchemy import desc


class ArticleAnalyzer:
    """文章分析器."""
    
    def __init__(self):
        self.stock_patterns = {
            # 美股代碼 (1-5個字母)
            'us_stocks': r'\b([A-Z]{1,5})\b',
            # 台股代碼 (4位數字)
            'tw_stocks': r'\b([0-9]{4})\b',
            # 港股代碼 (4-5位數字)
            'hk_stocks': r'\b([0-9]{4,5})\b'
        }
        
        # 投資策略關鍵詞
        self.strategy_keywords = {
            'buy_signals': ['買', '多', '看多', '推薦', '建議', '建倉', '加倉', '持有'],
            'sell_signals': ['賣', '空', '看空', '減倉', '出場', '獲利了結'],
            'risk_keywords': ['風險', '注意', '小心', '謹慎', '波動', '不確定'],
            'sector_keywords': ['半導體', 'AI', '電動車', '新能源', '生技', '金融', '地產']
        }
    
    def analyze_article(self, article_id: str) -> Dict:
        """分析單篇文章."""
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(
                PTTArticle.article_id == article_id
            ).first()
            
            if not article:
                return {"error": "文章不存在"}
            
            return self._analyze_content(article)
    
    def analyze_article_by_url(self, url: str) -> Dict:
        """根據URL分析文章."""
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(
                PTTArticle.url == url
            ).first()
            
            if not article:
                return {"error": "文章不存在"}
            
            return self._analyze_content(article)
    
    def _analyze_content(self, article: PTTArticle) -> Dict:
        """分析文章內容."""
        content = article.content
        title = article.title
        
        # 提取股票代碼
        stocks = self._extract_stocks(content)
        
        # 分析投資策略
        strategy = self._analyze_strategy(content)
        
        # 分析情感傾向
        sentiment = self._analyze_sentiment(content)
        
        # 分析產業類別
        sectors = self._analyze_sectors(content)
        
        # 分析投資建議
        recommendations = self._extract_recommendations(content)
        
        # 分析風險提示
        risks = self._extract_risks(content)
        
        return {
            "article_id": article.article_id,
            "title": article.title,
            "author": article.author,
            "publish_time": article.publish_time.isoformat(),
            "url": article.url,
            "push_count": article.push_count,
            "analysis": {
                "stocks": stocks,
                "strategy": strategy,
                "sentiment": sentiment,
                "sectors": sectors,
                "recommendations": recommendations,
                "risks": risks,
                "investment_thesis": self._extract_investment_thesis(content),
                "price_targets": self._extract_price_targets(content),
                "time_horizon": self._analyze_time_horizon(content)
            }
        }
    
    def _extract_stocks(self, content: str) -> Dict:
        """提取股票代碼."""
        stocks = {
            "us_stocks": [],
            "tw_stocks": [],
            "hk_stocks": [],
            "mentioned_stocks": []
        }
        
        # 提取美股代碼
        us_matches = re.findall(self.stock_patterns['us_stocks'], content)
        stocks["us_stocks"] = list(set([match for match in us_matches if len(match) <= 5]))
        
        # 提取台股代碼
        tw_matches = re.findall(self.stock_patterns['tw_stocks'], content)
        stocks["tw_stocks"] = list(set([match for match in tw_matches if not match.startswith(('20', '19', '0', '1'))]))
        
        # 提取港股代碼
        hk_matches = re.findall(self.stock_patterns['hk_stocks'], content)
        stocks["hk_stocks"] = list(set([match for match in hk_matches if len(match) >= 4]))
        
        # 合併所有股票
        all_stocks = stocks["us_stocks"] + stocks["tw_stocks"] + stocks["hk_stocks"]
        stocks["mentioned_stocks"] = list(set(all_stocks))
        
        return stocks
    
    def _analyze_strategy(self, content: str) -> Dict:
        """分析投資策略."""
        strategy = {
            "buy_signals": [],
            "sell_signals": [],
            "strategy_type": "unknown"
        }
        
        # 檢查買入信號
        for keyword in self.strategy_keywords['buy_signals']:
            if keyword in content:
                strategy["buy_signals"].append(keyword)
        
        # 檢查賣出信號
        for keyword in self.strategy_keywords['sell_signals']:
            if keyword in content:
                strategy["sell_signals"].append(keyword)
        
        # 判斷策略類型
        if strategy["buy_signals"] and not strategy["sell_signals"]:
            strategy["strategy_type"] = "bullish"
        elif strategy["sell_signals"] and not strategy["buy_signals"]:
            strategy["strategy_type"] = "bearish"
        elif strategy["buy_signals"] and strategy["sell_signals"]:
            strategy["strategy_type"] = "mixed"
        
        return strategy
    
    def _analyze_sentiment(self, content: str) -> Dict:
        """分析情感傾向."""
        positive_words = ['看好', '樂觀', '成長', '機會', '潛力', '利多', '上漲', '突破']
        negative_words = ['看壞', '悲觀', '衰退', '風險', '利空', '下跌', '破底']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "confidence": abs(positive_count - negative_count) / max(positive_count + negative_count, 1)
        }
    
    def _analyze_sectors(self, content: str) -> List[str]:
        """分析產業類別."""
        sectors = []
        for sector in self.strategy_keywords['sector_keywords']:
            if sector in content:
                sectors.append(sector)
        
        # 額外的產業識別
        if '半導體' in content or '晶片' in content or 'AMD' in content or 'NV' in content:
            sectors.append('半導體')
        if 'AI' in content or '人工智慧' in content:
            sectors.append('AI')
        if '電動車' in content or '特斯拉' in content or 'TSLA' in content:
            sectors.append('電動車')
        if '新能源' in content or '太陽能' in content or '風電' in content:
            sectors.append('新能源')
        if '生技' in content or '醫療' in content or '製藥' in content:
            sectors.append('生技')
        if '衛星' in content or '太空' in content or 'SpaceX' in content:
            sectors.append('太空科技')
        if '核能' in content or '核電' in content:
            sectors.append('核能')
        
        return list(set(sectors))
    
    def _extract_recommendations(self, content: str) -> List[Dict]:
        """提取投資建議."""
        recommendations = []
        
        # 尋找價格建議
        price_patterns = [
            r'(\d+(?:\.\d+)?)\s*元',
            r'(\d+(?:\.\d+)?)\s*美元',
            r'(\d+(?:\.\d+)?)\s*USD'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                recommendations.append({
                    "type": "price_target",
                    "value": float(match),
                    "context": "價格目標"
                })
        
        # 尋找時間建議
        time_patterns = [
            r'(\d+)\s*年',
            r'(\d+)\s*月',
            r'(\d+)\s*季'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                recommendations.append({
                    "type": "time_horizon",
                    "value": int(match),
                    "context": "投資期間"
                })
        
        return recommendations
    
    def _extract_risks(self, content: str) -> List[str]:
        """提取風險提示."""
        risks = []
        
        risk_indicators = [
            '風險', '注意', '小心', '謹慎', '波動', '不確定', '可能', '或許',
            '但是', '不過', '然而', '雖然', '儘管'
        ]
        
        for indicator in risk_indicators:
            if indicator in content:
                risks.append(indicator)
        
        return list(set(risks))
    
    def _extract_investment_thesis(self, content: str) -> str:
        """提取投資論述."""
        # 尋找關鍵論述段落
        thesis_indicators = ['因為', '所以', '因此', '由於', '基於', '根據']
        
        for indicator in thesis_indicators:
            if indicator in content:
                # 提取包含該指示詞的句子
                sentences = content.split('。')
                for sentence in sentences:
                    if indicator in sentence:
                        return sentence.strip()
        
        return "未找到明確投資論述"
    
    def _extract_price_targets(self, content: str) -> List[Dict]:
        """提取價格目標."""
        price_targets = []
        
        # 尋找價格目標模式
        patterns = [
            r'目標價\s*(\d+(?:\.\d+)?)',
            r'看到\s*(\d+(?:\.\d+)?)',
            r'上看\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*元'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                price_targets.append({
                    "price": float(match),
                    "context": "價格目標"
                })
        
        return price_targets
    
    def _analyze_time_horizon(self, content: str) -> str:
        """分析投資時間框架."""
        if any(word in content for word in ['短期', '近期', '這週', '這個月']):
            return "短期"
        elif any(word in content for word in ['中期', '幾個月', '半年']):
            return "中期"
        elif any(word in content for word in ['長期', '幾年', '長期持有']):
            return "長期"
        else:
            return "未明確"
    
    def batch_analyze_articles(self, author: str = None, limit: int = 10) -> List[Dict]:
        """批量分析文章."""
        with db_manager.get_session() as session:
            query = session.query(PTTArticle)
            
            if author:
                query = query.filter(PTTArticle.author == author)
            
            articles = query.order_by(desc(PTTArticle.publish_time)).limit(limit).all()
            
            results = []
            for article in articles:
                try:
                    analysis = self._analyze_content(article)
                    results.append(analysis)
                except Exception as e:
                    logger.error(f"分析文章 {article.article_id} 失敗: {e}")
                    continue
            
            return results
    
    def get_author_investment_profile(self, author: str) -> Dict:
        """分析作者投資偏好."""
        with db_manager.get_session() as session:
            articles = session.query(PTTArticle).filter(
                PTTArticle.author == author
            ).order_by(desc(PTTArticle.publish_time)).all()
            
            if not articles:
                return {"error": "找不到該作者的文章"}
            
            # 統計分析
            all_stocks = []
            all_sectors = []
            all_sentiments = []
            
            for article in articles:
                analysis = self._analyze_content(article)
                all_stocks.extend(analysis["analysis"]["stocks"]["mentioned_stocks"])
                all_sectors.extend(analysis["analysis"]["sectors"])
                all_sentiments.append(analysis["analysis"]["sentiment"]["sentiment"])
            
            # 計算統計
            stock_frequency = {}
            for stock in all_stocks:
                stock_frequency[stock] = stock_frequency.get(stock, 0) + 1
            
            sector_frequency = {}
            for sector in all_sectors:
                sector_frequency[sector] = sector_frequency.get(sector, 0) + 1
            
            sentiment_frequency = {}
            for sentiment in all_sentiments:
                sentiment_frequency[sentiment] = sentiment_frequency.get(sentiment, 0) + 1
            
            return {
                "author": author,
                "total_articles": len(articles),
                "favorite_stocks": sorted(stock_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
                "favorite_sectors": sorted(sector_frequency.items(), key=lambda x: x[1], reverse=True)[:5],
                "sentiment_distribution": sentiment_frequency,
                "investment_style": self._determine_investment_style(all_sectors, all_sentiments)
            }
    
    def _determine_investment_style(self, sectors: List[str], sentiments: List[str]) -> str:
        """判斷投資風格."""
        if '半導體' in sectors and 'AI' in sectors:
            return "科技成長型"
        elif '新能源' in sectors and '核能' in sectors:
            return "能源轉型型"
        elif '太空科技' in sectors:
            return "前沿科技型"
        elif sentiments.count('positive') > sentiments.count('negative'):
            return "樂觀進取型"
        else:
            return "穩健保守型"


def main():
    """測試分析功能."""
    analyzer = ArticleAnalyzer()
    
    # 分析特定文章
    print("🔍 分析 mrp 的最新文章...")
    analysis = analyzer.analyze_article_by_url("https://www.ptt.cc/bbs/Stock/M.1759822323.A.E44.html")
    
    if "error" not in analysis:
        print(f"📰 文章: {analysis['title']}")
        print(f"作者: {analysis['author']}")
        print(f"推文數: {analysis['push_count']}")
        print()
        
        print("📊 分析結果:")
        print(f"股票代碼: {analysis['analysis']['stocks']['mentioned_stocks']}")
        print(f"投資策略: {analysis['analysis']['strategy']['strategy_type']}")
        print(f"情感傾向: {analysis['analysis']['sentiment']['sentiment']}")
        print(f"產業類別: {analysis['analysis']['sectors']}")
        print(f"投資建議: {len(analysis['analysis']['recommendations'])} 項")
        print(f"風險提示: {analysis['analysis']['risks']}")
        print(f"投資論述: {analysis['analysis']['investment_thesis']}")
        print(f"時間框架: {analysis['analysis']['time_horizon']}")
    
    # 分析作者投資偏好
    print("\n👤 分析 mrp 的投資偏好...")
    profile = analyzer.get_author_investment_profile("mrp")
    
    if "error" not in profile:
        print(f"總文章數: {profile['total_articles']}")
        print(f"偏好股票: {profile['favorite_stocks'][:5]}")
        print(f"偏好產業: {profile['favorite_sectors']}")
        print(f"情感分布: {profile['sentiment_distribution']}")
        print(f"投資風格: {profile['investment_style']}")


if __name__ == "__main__":
    main()
