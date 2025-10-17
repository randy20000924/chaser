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
        self.model_name = "Qwen2.5:0.5b"  # 使用 Qwen2.5 0.5b 模型
    
    async def _analyze_with_llm(self, content: str) -> Dict[str, Any]:
        """使用 LLM 分析文章內容."""
        try:
            # 專業化提示詞，增加分析深度
            prompt = f"""你是一位資深的證券研究分析師，熟悉台灣與國際股市的新聞解讀與市場心理。忽略政治立場或網路俚語，只分析對股票市場的潛在影響，只用繁體中文回覆並以 JSON 格式輸出：

請從技術面、基本面、消息面三個角度分析以下股票文章，並只返回JSON格式，不要其他文字：

{content[:300]}

必須返回以下JSON格式：
{{"recommended_stocks":["股票代碼"],"sentiment":"pos/neg/neu","reason":"分析原因","sectors":["產業類別"],"strategy":"投資策略","risk_level":"low/medium/high"}}

分析要求：
- 情緒分析請考慮：市場恐慌程度、投資人信心、資金流向、外資動向
- 風險等級請考慮：市場風險、流動性風險、政策風險、個股風險
- 投資策略請包含：進場時機、停損點位、目標價位、持有期間
- 產業類別請包含：主要產業、次產業、相關概念股、上下游供應鏈"""

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.4,      # 稍微增加創造性
                            "max_tokens": 200,       # 增加輸出長度以容納更詳細分析
                            "num_ctx": 1024,         # 增加上下文長度
                            "num_predict": 200,      # 增加預測長度
                            "num_thread": 2,         # 增加線程數以提高處理速度
                            "num_gpu": 0,            # 禁用 GPU
                            "repeat_penalty": 1.1,   # 避免重複內容
                            "top_p": 0.9,            # 增加多樣性
                            "top_k": 40              # 限制詞彙選擇範圍
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=180)  # 增加超時時間到 180 秒 (3分鐘)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # 嘗試解析JSON，增加容錯機制
                        try:
                            # 清理回應文字，移除可能的額外文字
                            cleaned_response = response_text.strip()
                            
                            # 嘗試多種方式提取JSON
                            json_candidates = []
                            
                            # 方法1: 尋找完整的JSON對象
                            json_start = cleaned_response.find('{')
                            json_end = cleaned_response.rfind('}') + 1
                            if json_start != -1 and json_end > json_start:
                                json_candidates.append(cleaned_response[json_start:json_end])
                            
                            # 方法2: 尋找多行JSON
                            lines = cleaned_response.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line.startswith('{') and line.endswith('}'):
                                    json_candidates.append(line)
                            
                            # 方法3: 尋找包含特定關鍵字的JSON
                            for line in lines:
                                if any(keyword in line for keyword in ['recommended_stocks', 'sentiment', 'reason']):
                                    if '{' in line and '}' in line:
                                        json_candidates.append(line)
                            
                            # 嘗試解析每個候選JSON
                            for json_str in json_candidates:
                                try:
                                    analysis = json.loads(json_str)
                                    
                                    # 驗證必要字段
                                    if isinstance(analysis, dict):
                                        logger.info(f"Successfully parsed JSON: {json_str[:100]}...")
                                        
                                        # 確保所有必要字段存在並有合理值
                                        return {
                                            "recommended_stocks": analysis.get("recommended_stocks", []) if isinstance(analysis.get("recommended_stocks"), list) else [],
                                            "reason": analysis.get("reason", "技術分析") if analysis.get("reason") else "技術分析",
                                            "sentiment": analysis.get("sentiment", "neutral") if analysis.get("sentiment") in ["pos", "neg", "neu"] else "neutral",
                                            "sectors": analysis.get("sectors", []) if isinstance(analysis.get("sectors"), list) else [],
                                            "strategy": analysis.get("strategy", "投資策略") if analysis.get("strategy") else "投資策略",
                                            "risk_level": analysis.get("risk_level", "medium") if analysis.get("risk_level") in ["low", "medium", "high"] else "medium"
                                        }
                                except json.JSONDecodeError:
                                    continue
                            
                            logger.warning(f"Failed to parse any JSON from response: {response_text[:200]}...")
                            
                        except Exception as e:
                            logger.error(f"Error processing LLM response: {e}")
                        
                        # 如果所有JSON解析都失敗，返回默認值
                        return {
                            "recommended_stocks": [],
                            "reason": "分析失敗 - JSON解析錯誤",
                            "sentiment": "neutral",
                            "sectors": [],
                            "strategy": "未知",
                            "risk_level": "medium"
                        }
                    else:
                        logger.error(f"LLM API error: {response.status}")
                        return self._get_default_analysis()
                        
        except asyncio.TimeoutError:
            logger.error("LLM analysis timeout after 3 minutes")
            return {
                "recommended_stocks": [],
                "reason": "分析超時 - 請稍後重試",
                "sentiment": "neutral",
                "sectors": [],
                "strategy": "未知",
                "risk_level": "medium"
            }
        except aiohttp.ClientError as e:
            logger.error(f"Network error during LLM analysis: {e}")
            return {
                "recommended_stocks": [],
                "reason": "網路錯誤 - 無法連接分析服務",
                "sentiment": "neutral",
                "sectors": [],
                "strategy": "未知",
                "risk_level": "medium"
            }
        except Exception as e:
            logger.error(f"Unexpected error during LLM analysis: {e}")
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
    
    async def _analyze_content_simple(self, content: str) -> Dict[str, Any]:
        """簡化的文章內容分析（用於混合模式）."""
        try:
            logger.info("Starting simple LLM analysis")
            
            # 使用LLM分析
            analysis = await self._analyze_with_llm(content)
            
            logger.info("Simple LLM analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in simple LLM analysis: {e}")
            return self._get_default_analysis()

# 創建全局實例
analyzer = ArticleAnalyzer()