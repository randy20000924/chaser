#!/usr/bin/env python3
"""文章分析模組 - 分析PTT文章中的投資標的和策略，並將結果存儲到資料庫."""

import re
import json
from typing import List, Dict, Optional, Tuple
import httpx
from datetime import datetime
from loguru import logger
from database import db_manager
from models import PTTArticle
from sqlalchemy import desc


class ArticleAnalyzer:
    """文章分析器 - 用於爬蟲後處理和即時分析."""
    
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
    
    def process_crawled_articles(self, limit: int = None) -> Dict:
        """處理已爬取但未分析的文章."""
        logger.info("開始處理已爬取的文章...")
        
        with db_manager.get_session() as session:
            # 查詢未分析的文章（analysis_result 為 NULL 或空）
            query = session.query(PTTArticle).filter(
                (PTTArticle.analysis_result.is_(None)) | 
                (PTTArticle.analysis_result == "")
            )
            
            if limit:
                query = query.limit(limit)
            
            articles = query.all()
            total_articles = len(articles)
            
            if total_articles == 0:
                logger.info("沒有需要處理的文章")
                return {"processed": 0, "errors": 0}
            
            logger.info(f"找到 {total_articles} 篇需要處理的文章")
            
            processed = 0
            errors = 0
            
            for article in articles:
                try:
                    # 分析文章
                    analysis_result = self._analyze_content(article)
                    
                    # 將分析結果存儲到資料庫
                    article.analysis_result = json.dumps(analysis_result, ensure_ascii=False)
                    article.analysis_time = datetime.now()
                    
                    processed += 1
                    
                    if processed % 10 == 0:
                        logger.info(f"已處理 {processed}/{total_articles} 篇文章")
                        
                except Exception as e:
                    logger.error(f"處理文章 {article.article_id} 失敗: {e}")
                    errors += 1
                    continue
            
            # 提交所有更改
            session.commit()
            
            logger.info(f"文章處理完成: 成功 {processed} 篇, 錯誤 {errors} 篇")
            return {"processed": processed, "errors": errors}
    
    def get_article_analysis(self, article_id: str) -> Dict:
        """從資料庫獲取文章分析結果."""
        with db_manager.get_session() as session:
            article = session.query(PTTArticle).filter(
                PTTArticle.article_id == article_id
            ).first()
            
            if not article:
                return {"error": "文章不存在"}
            
            # 如果已有分析結果，直接返回
            if article.analysis_result:
                try:
                    return json.loads(article.analysis_result)
                except json.JSONDecodeError:
                    logger.warning(f"文章 {article_id} 的分析結果格式錯誤，重新分析")
            
            # 如果沒有分析結果，進行即時分析
            logger.info(f"文章 {article_id} 沒有分析結果，進行即時分析")
            analysis_result = self._analyze_content(article)
            
            # 保存分析結果到資料庫
            try:
                article.analysis_result = json.dumps(analysis_result, ensure_ascii=False)
                article.analysis_time = datetime.now()
                session.commit()
            except Exception as e:
                logger.error(f"保存分析結果失敗: {e}")
            
            return analysis_result
    
    def get_author_articles_with_analysis(self, author: str, limit: int = 20) -> Dict:
        """獲取作者的文章及其分析結果."""
        with db_manager.get_session() as session:
            articles = session.query(PTTArticle).filter(
                PTTArticle.author == author
            ).order_by(desc(PTTArticle.publish_time)).limit(limit).all()
            
            if not articles:
                return {"error": "找不到該作者的文章"}
            
            result = []
            for article in articles:
                article_data = {
                    "article_id": article.article_id,
                    "title": article.title,
                    "author": article.author,
                    "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                    "url": article.url,
                    "push_count": article.push_count,
                    "analysis": None
                }
                
                # 如果有分析結果，解析並添加
                if article.analysis_result:
                    try:
                        article_data["analysis"] = json.loads(article.analysis_result)
                    except json.JSONDecodeError:
                        logger.warning(f"文章 {article.article_id} 的分析結果格式錯誤")
                
                result.append(article_data)
            
            return {
                "author": author,
                "articles": result,
                "total": len(result)
            }
    
    def _analyze_content(self, article: PTTArticle) -> Dict:
        """分析文章內容 - 簡化輸出格式."""
        content = article.content
        title = article.title
        
        # 若啟用 Ollama，優先走 LLM 分析路徑
        try:
            from config import settings
            if getattr(settings, "enable_ollama", False):
                llm = self._analyze_with_ollama(
                    content=content, 
                    author=article.author, 
                    url=article.url, 
                    date=article.publish_time
                )
                if isinstance(llm, dict) and llm.get("recommended_stocks"):
                    return llm
        except Exception as e:
            logger.warning(f"Ollama analysis failed or disabled, fallback to rules. Reason: {e}")
        
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
        
        # 簡化輸出格式
        return {
            "author": article.author,
            "date": article.publish_time.strftime('%Y-%m-%d') if article.publish_time else 'N/A',
            "url": article.url,
            "recommended_stocks": list(stocks.get('mentioned_stocks', []))[:5],  # 最多5個推薦標的
            "reason": self._generate_simple_reason(stocks, strategy, sentiment, sectors, risks)
        }

    def _analyze_with_ollama(self, content: str, author: str, url: str, date: Optional[datetime]) -> Dict:
        """使用本地 Ollama 進行分析，返回既定 JSON 結構。"""
        from config import settings
        base = settings.ollama_base_url.rstrip("/")
        model = settings.ollama_model
        prompt = (
            "你是一個專業的股票分析師。請分析以下PTT股票版文章，提取投資標的和推薦原因。\n\n"
            "分析重點：\n"
            "1. 找出文章推薦的股票代碼（台股為數字代碼並附帶公司名稱，如台積電2330，美股直接使用代碼，如AAPL）\n"
            "2. 分析推薦原因（技術面、基本面、消息面等）\n"
            "3. 判斷投資方向（看多/看空）\n\n"
            f"文章資訊：\n"
            f"作者: {author}\n"
            f"URL: {url}\n"
            f"日期: {(date.strftime('%Y-%m-%d') if isinstance(date, datetime) else 'N/A')}\n\n"
            f"文章內容：\n{content}\n\n"
            "請輸出JSON格式，包含以下欄位：\n"
            "- author: 作者名稱\n"
            "- date: 發文日期 (YYYY-MM-DD)\n"
            "- url: 文章連結\n"
            "- recommended_stocks: 推薦的股票代碼陣列（最多5個）\n"
            "- reason: 推薦原因（簡潔說明，如：技術面突破、基本面改善、消息面利多等）\n\n"
            "只輸出JSON，不要其他文字。"
        )
        payload = {"model": model, "prompt": prompt, "stream": False}
        try:
            # 提高超時，並重試一次
            with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
                resp = client.post(f"{base}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Ollama 回傳形如 {"response": "...文本..."}
                raw = data.get("response", "").strip()
                # 嘗試解析JSON
                result = json.loads(raw)
                # 後處理：確保 recommended_stocks 只包含有效的股票代碼
                stocks = result.get("recommended_stocks", [])
                valid_stocks = []
                for stock in stocks:
                    if isinstance(stock, str):
                        # 台股4位數代碼
                        if re.match(r'^\d{4}$', stock):
                            valid_stocks.append(stock)
                        # 美股英文字母代碼 (1-5個字母)
                        elif re.match(r'^[A-Z]{1,5}$', stock):
                            valid_stocks.append(stock)
                
                # 正規化欄位
                return {
                    "author": result.get("author", author),
                    "date": result.get("date", (date.strftime('%Y-%m-%d') if isinstance(date, datetime) else 'N/A')),
                    "url": result.get("url", url),
                    "recommended_stocks": valid_stocks[:5],
                    "reason": result.get("reason", "")
                }
        except Exception as e:
            logger.warning(f"Ollama call/parse error: {e}")
            return {}
    
    def _generate_simple_reason(self, stocks: Dict, strategy: Dict, sentiment: Dict, sectors: List, risks: List) -> str:
        """生成簡化的推薦原因."""
        reasons = []
        
        # 基於股票代碼數量
        stock_count = len(stocks.get('mentioned_stocks', []))
        if stock_count > 0:
            if stock_count == 1:
                reasons.append(f"推薦標的: {stocks['mentioned_stocks'][0]}")
            else:
                reasons.append(f"推薦{stock_count}個標的")
        
        # 基於策略
        buy_signals = len(strategy.get('buy_signals', []))
        sell_signals = len(strategy.get('sell_signals', []))
        
        if buy_signals > sell_signals:
            reasons.append("看多訊號")
        elif sell_signals > buy_signals:
            reasons.append("看空訊號")
        
        # 基於情感
        positive = sentiment.get('positive', 0)
        negative = sentiment.get('negative', 0)
        
        if positive > negative:
            reasons.append("正面情緒")
        elif negative > positive:
            reasons.append("負面情緒")
        
        # 基於產業
        if sectors:
            reasons.append(f"關注{sectors[0]}產業")
        
        # 基於風險
        if risks:
            reasons.append("注意風險")
        
        # 如果沒有具體原因，嘗試從內容中提取關鍵信息
        if not reasons:
            reasons.append("技術分析")
        
        return "、".join(reasons) if reasons else "技術分析"
    
    def _extract_stocks(self, content: str) -> Dict:
        """提取股票代碼."""
        stocks = {
            "us_stocks": [],
            "tw_stocks": [],
            "hk_stocks": [],
            "mentioned_stocks": []
        }
        
        # 改進的台股代碼提取 - 4位數字，排除年份和常見數字
        tw_pattern = r'\b([0-9]{4})\b'
        tw_matches = re.findall(tw_pattern, content)
        
        # 過濾掉年份和常見數字
        filtered_tw = []
        for match in tw_matches:
            # 排除年份 (2020-2030)
            if not (2020 <= int(match) <= 2030):
                # 排除常見的數字序列和技術規格
                if not match in ['0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999', '3120', '2500', '1230', '1070', '1090', '1330', '1575', '8000', '5800', '3000', '1000', '2000', '10000', '8550', '1400', '2800', '5600']:
                    filtered_tw.append(match)
        
        stocks["tw_stocks"] = list(set(filtered_tw))
        
        # 提取美股代碼 (1-5個字母)
        us_pattern = r'\b([A-Z]{1,5})\b'
        us_matches = re.findall(us_pattern, content)
        # 過濾掉常見的英文單詞和技術術語
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY', 'WORD', 'BUT', 'WHAT', 'SOME', 'WE', 'IT', 'IS', 'OR', 'HAD', 'THE', 'OF', 'TO', 'AND', 'A', 'IN', 'IS', 'IT', 'YOU', 'THAT', 'HE', 'WAS', 'FOR', 'ON', 'ARE', 'AS', 'WITH', 'HIS', 'THEY', 'I', 'AT', 'BE', 'THIS', 'HAVE', 'FROM', 'OR', 'ONE', 'HAD', 'BY', 'WORD', 'BUT', 'NOT', 'WHAT', 'ALL', 'WERE', 'WE', 'WHEN', 'YOUR', 'CAN', 'SAID', 'THERE', 'EACH', 'WHICH', 'SHE', 'DO', 'HOW', 'THEIR', 'IF', 'WILL', 'UP', 'OTHER', 'ABOUT', 'OUT', 'MANY', 'THEN', 'THEM', 'THESE', 'SO', 'SOME', 'HER', 'WOULD', 'MAKE', 'LIKE', 'INTO', 'HIM', 'TIME', 'HAS', 'TWO', 'MORE', 'GO', 'NO', 'WAY', 'COULD', 'MY', 'THAN', 'FIRST', 'BEEN', 'CALL', 'WHO', 'ITS', 'NOW', 'FIND', 'LONG', 'DOWN', 'DAY', 'DID', 'GET', 'COME', 'MADE', 'MAY', 'PART', 'ATH', 'Q4', 'Q1', 'Q2', 'EPS', 'PE', 'DJI', 'AI', 'COBRA', 'RKLB', 'ONDS', 'AVAV', 'RCAT', 'PDYN', 'TOP', 'M', 'W', 'X', 'Y', 'Z'}
        stocks["us_stocks"] = list(set([match for match in us_matches if match not in common_words and len(match) <= 5]))
        
        # 提取港股代碼 (4-5位數字)
        hk_pattern = r'\b([0-9]{4,5})\b'
        hk_matches = re.findall(hk_pattern, content)
        # 過濾掉技術規格數字
        filtered_hk = []
        for match in hk_matches:
            if len(match) >= 4 and not (2020 <= int(match) <= 2030):
                if not match in ['3120', '2500', '1230', '1070', '1090', '1330', '1575', '8000', '5800', '3000', '1000', '2000', '10000', '8550', '1400', '2800', '5600']:
                    filtered_hk.append(match)
        stocks["hk_stocks"] = list(set(filtered_hk))
        
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
    
    def get_analysis_statistics(self) -> Dict:
        """獲取分析統計信息."""
        with db_manager.get_session() as session:
            total_articles = session.query(PTTArticle).count()
            analyzed_articles = session.query(PTTArticle).filter(
                PTTArticle.analysis_result.isnot(None),
                PTTArticle.analysis_result != ""
            ).count()
            
            return {
                "total_articles": total_articles,
                "analyzed_articles": analyzed_articles,
                "pending_articles": total_articles - analyzed_articles,
                "analysis_rate": f"{(analyzed_articles / total_articles * 100):.1f}%" if total_articles > 0 else "0%"
            }


def main():
    """測試分析功能."""
    analyzer = ArticleAnalyzer()
    
    # 測試處理已爬取的文章
    print("🔍 開始處理已爬取的文章...")
    result = analyzer.process_crawled_articles(limit=5)
    print(f"處理結果: {result}")
    
    # 測試獲取分析統計
    print("\n📊 分析統計:")
    stats = analyzer.get_analysis_statistics()
    print(f"總文章數: {stats['total_articles']}")
    print(f"已分析: {stats['analyzed_articles']}")
    print(f"待分析: {stats['pending_articles']}")
    print(f"分析率: {stats['analysis_rate']}")


if __name__ == "__main__":
    main()