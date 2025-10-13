"""簡化分析器 - 基於規則的輕量分析."""

import re
from typing import Dict, Any
from loguru import logger

class SimpleAnalyzer:
    """簡化分析器 - 不依賴 LLM."""
    
    def __init__(self):
        pass
    
    def _extract_sentiment_keywords(self, content: str) -> str:
        """基於關鍵詞分析情感."""
        positive_words = ['漲', '多', '看好', '推薦', '買入', '強勢', '突破', '利多', '好', '優', '佳']
        negative_words = ['跌', '空', '看壞', '賣出', '弱勢', '破底', '利空', '壞', '差', '劣', '糟']
        
        pos_count = sum(1 for word in positive_words if word in content)
        neg_count = sum(1 for word in negative_words if word in content)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_strategy_keywords(self, content: str) -> str:
        """基於關鍵詞分析策略."""
        if any(word in content for word in ['短線', '當沖', '日內']):
            return "短線交易"
        elif any(word in content for word in ['長線', '長期', '持有']):
            return "長期投資"
        elif any(word in content for word in ['波段', '中期']):
            return "波段操作"
        else:
            return "一般投資"
    
    def _extract_risk_keywords(self, content: str) -> str:
        """基於關鍵詞分析風險等級."""
        high_risk_words = ['高風險', '槓桿', '期貨', '選擇權', '當沖', '投機']
        low_risk_words = ['穩健', '保守', '定存', '債券', 'ETF']
        
        if any(word in content for word in high_risk_words):
            return "high"
        elif any(word in content for word in low_risk_words):
            return "low"
        else:
            return "medium"
    
    def _extract_sectors(self, content: str) -> list:
        """基於關鍵詞分析產業."""
        sectors = []
        sector_keywords = {
            '科技': ['科技', '半導體', 'IC', '晶片', 'AI', '人工智慧'],
            '金融': ['金融', '銀行', '保險', '證券'],
            '能源': ['能源', '石油', '天然氣', '太陽能', '風電'],
            '醫療': ['醫療', '生技', '製藥', '健康'],
            '消費': ['消費', '零售', '食品', '飲料'],
            '工業': ['工業', '製造', '機械', '鋼鐵'],
            '地產': ['地產', '房地產', '建設', '營建']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in content for keyword in keywords):
                sectors.append(sector)
        
        return sectors[:3]  # 最多返回3個產業
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """分析文章內容."""
        try:
            logger.info("Using simple rule-based analysis")
            
            return {
                "recommended_stocks": [],  # 由股票驗證器處理
                "reason": "基於關鍵詞分析",
                "sentiment": self._extract_sentiment_keywords(content),
                "sectors": self._extract_sectors(content),
                "strategy": self._extract_strategy_keywords(content),
                "risk_level": self._extract_risk_keywords(content)
            }
        except Exception as e:
            logger.error(f"Simple analysis error: {e}")
            return {
                "recommended_stocks": [],
                "reason": "分析失敗",
                "sentiment": "neutral",
                "sectors": [],
                "strategy": "未知",
                "risk_level": "medium"
            }

# 創建全局實例
simple_analyzer = SimpleAnalyzer()
