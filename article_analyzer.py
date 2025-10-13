"""文章分析器 - 使用較輕量的 Qwen2:0.5b 模型."""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from loguru import logger
from models import PTTArticle

class ArticleAnalyzer:
    """文章分析器類別."""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model_name = "qwen2:0.5b"  # 使用較輕量的模型
    
    async def _analyze_with_llm(self, content: str) -> Dict[str, Any]:
        """使用 LLM 分析文章內容."""
        try:
            # 進一步簡化提示詞，減少處理負擔
            prompt = f"""分析PTT股票文章：

{content[:500]}...

返回JSON：
{{
    "recommended_stocks": ["代碼1", "代碼2"],
    "reason": "簡短原因",
    "sentiment": "positive/negative/neutral",
    "sectors": ["產業"],
    "strategy": "策略",
    "risk_level": "low/medium/high"
}}"""

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,
                            "max_tokens": 200,  # 進一步限制輸出長度
                            "num_ctx": 1024,    # 限制上下文長度
                            "num_predict": 200  # 限制預測長度
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=15)  # 減少超時時間
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # 嘗試解析JSON
                        try:
                            # 提取JSON部分
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            if json_start != -1 and json_end > json_start:
                                json_str = response_text[json_start:json_end]
                                analysis = json.loads(json_str)
                                
                                # 確保所有必要字段存在
                                return {
                                    "recommended_stocks": analysis.get("recommended_stocks", []),
                                    "reason": analysis.get("reason", "技術分析"),
                                    "sentiment": analysis.get("sentiment", "neutral"),
                                    "sectors": analysis.get("sectors", []),
                                    "strategy": analysis.get("strategy", "投資策略"),
                                    "risk_level": analysis.get("risk_level", "medium")
                                }
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse LLM response as JSON")
                        
                        # 如果JSON解析失敗，返回默認值
                        return {
                            "recommended_stocks": [],
                            "reason": "分析失敗",
                            "sentiment": "neutral",
                            "sectors": [],
                            "strategy": "未知",
                            "risk_level": "medium"
                        }
                    else:
                        logger.error(f"LLM API error: {response.status}")
                        return self._get_default_analysis()
                        
        except asyncio.TimeoutError:
            logger.error("LLM analysis timeout")
            return self._get_default_analysis()
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """返回默認分析結果."""
        return {
            "recommended_stocks": [],
            "reason": "分析失敗",
            "sentiment": "neutral",
            "sectors": [],
            "strategy": "未知",
            "risk_level": "medium"
        }
    
    async def _analyze_content(self, article: PTTArticle) -> Dict[str, Any]:
        """分析文章內容."""
        try:
            logger.info(f"Analyzing article: {article.article_id}")
            
            # 使用LLM分析
            analysis = await self._analyze_with_llm(article.content)
            
            logger.info(f"Analysis completed for article: {article.article_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing article {article.article_id}: {e}")
            return self._get_default_analysis()

# 創建全局實例
analyzer = ArticleAnalyzer()
