#!/usr/bin/env python3
"""文章分析模組 - 分析PTT文章中的投資標的和策略."""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from database import db_manager
from models import PTTArticle
import ollama
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
        
        # LLM 配置
        self.llm_model = "qwen2.5:0.5b"
        self.ollama_client = ollama.Client()
    
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
        """分析文章內容 - 使用 LLM 進行深度分析."""
        content = article.content
        title = article.title
        
        # 使用 LLM 進行深度分析
        llm_analysis = self._analyze_with_llm(content, title)
        
        # 提取股票代碼（保留規則式提取作為備用）
        stocks = self._extract_stocks(content)
        
        # 合併 LLM 分析和規則式提取的結果
        recommended_stocks = llm_analysis.get('recommended_stocks', [])
        if not recommended_stocks:
            recommended_stocks = list(stocks.get('mentioned_stocks', []))[:5]
        
        return {
            "author": article.author,
            "date": article.publish_time.strftime('%Y-%m-%d') if article.publish_time else 'N/A',
            "url": article.url,
            "recommended_stocks": recommended_stocks,
            "reason": llm_analysis.get('reason', '技術分析'),
            "llm_analysis": llm_analysis  # 包含完整的 LLM 分析結果
        }
    
    def _analyze_with_llm(self, content: str, title: str) -> Dict:
        """使用 Qwen2.5 進行深度分析."""
        try:
            # 構建分析提示詞
            prompt = f"""
請分析以下 PTT 股票板文章，提取投資相關信息：

標題：{title}

內容：
{content[:2000]}...

請以 JSON 格式回傳分析結果，包含以下欄位：
1. recommended_stocks: 推薦的股票代碼列表（台股4位數字、美股1-5字母、港股4-5位數字）
2. reason: 推薦原因（簡潔說明）
3. sentiment: 情感傾向（positive/negative/neutral）
4. sectors: 相關產業類別
5. strategy: 投資策略類型
6. risk_level: 風險等級（low/medium/high）

請確保回傳的是有效的 JSON 格式。
"""

            # 調用 Qwen2.5 模型
            response = self.ollama_client.chat(
                model=self.llm_model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,  # 降低隨機性，提高一致性
                    'top_p': 0.9
                }
            )
            
            # 解析 LLM 回應
            llm_response = response['message']['content']
            logger.info(f"LLM Response: {llm_response}")
            
            # 嘗試解析 JSON
            try:
                # 提取 JSON 部分（如果回應包含其他文字）
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    analysis_result = json.loads(json_str)
                else:
                    # 如果找不到 JSON，使用預設值
                    analysis_result = self._create_default_analysis()
                
                return analysis_result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                return self._create_default_analysis()
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._create_default_analysis()
    
    def _create_default_analysis(self) -> Dict:
        """創建預設分析結果."""
        return {
            "recommended_stocks": [],
            "reason": "技術分析",
            "sentiment": "neutral",
            "sectors": [],
            "strategy": "unknown",
            "risk_level": "medium"
        }
    
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
