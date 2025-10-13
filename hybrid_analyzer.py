"""混合分析器 - 結合 LLM 和規則分析."""

import asyncio
from typing import Dict, Any
from loguru import logger
from article_analyzer import analyzer
from simple_analyzer import simple_analyzer

class HybridAnalyzer:
    """混合分析器 - 優先使用 LLM，失敗時回退到規則分析."""
    
    def __init__(self):
        self.llm_analyzer = analyzer
        self.rule_analyzer = simple_analyzer
        self.llm_timeout = 5  # LLM 超時時間（秒）
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """分析文章內容 - 混合模式."""
        try:
            # 嘗試使用 LLM 分析（短超時）
            logger.info("Attempting LLM analysis...")
            llm_result = await asyncio.wait_for(
                self.llm_analyzer._analyze_content_simple(content),
                timeout=self.llm_timeout
            )
            logger.info("LLM analysis successful")
            return llm_result
            
        except asyncio.TimeoutError:
            logger.warning("LLM analysis timeout, falling back to rule-based analysis")
            return await self.rule_analyzer.analyze_content(content)
            
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, falling back to rule-based analysis")
            return await self.rule_analyzer.analyze_content(content)

# 創建全局實例
hybrid_analyzer = HybridAnalyzer()
