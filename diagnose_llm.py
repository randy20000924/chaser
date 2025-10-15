#!/usr/bin/env python3
"""
診斷 LLM 分析超時問題
"""

import asyncio
import aiohttp
import json
import time
from loguru import logger

async def test_ollama_connection():
    """測試 Ollama 連接"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Ollama 連接成功，可用模型: {[model['name'] for model in data.get('models', [])]}")
                    return True
                else:
                    logger.error(f"Ollama API 錯誤: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Ollama 連接失敗: {e}")
        return False

async def test_model_availability():
    """測試模型可用性"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    
                    target_model = "Qwen2.5:0.5b"
                    if target_model in models:
                        logger.info(f"✅ 模型 {target_model} 可用")
                        return True
                    else:
                        logger.error(f"❌ 模型 {target_model} 不可用")
                        logger.info(f"可用模型: {models}")
                        return False
    except Exception as e:
        logger.error(f"檢查模型可用性失敗: {e}")
        return False

async def test_simple_generation():
    """測試簡單的文本生成"""
    try:
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "Qwen2.5:0.5b",
                    "prompt": "Hello",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_tokens": 10,
                        "num_ctx": 100,
                        "num_predict": 10,
                        "num_thread": 1,
                        "num_gpu": 0
                    }
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ 簡單生成測試成功，耗時: {duration:.2f}秒")
                    logger.info(f"回應: {result.get('response', '')[:50]}...")
                    return True
                else:
                    logger.error(f"❌ 生成測試失敗: {response.status}")
                    return False
    except asyncio.TimeoutError:
        logger.error("❌ 生成測試超時")
        return False
    except Exception as e:
        logger.error(f"❌ 生成測試錯誤: {e}")
        return False

async def test_article_analysis():
    """測試文章分析"""
    try:
        start_time = time.time()
        
        prompt = """分析股票文章：台積電股價上漲

JSON: {"stocks":["代碼"],"sentiment":"pos/neg/neu","reason":"原因"}"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "Qwen2.5:0.5b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "max_tokens": 100,
                        "num_ctx": 512,
                        "num_predict": 100,
                        "num_thread": 1,
                        "num_gpu": 0
                    }
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ 文章分析測試成功，耗時: {duration:.2f}秒")
                    logger.info(f"回應: {result.get('response', '')}")
                    return True
                else:
                    logger.error(f"❌ 文章分析測試失敗: {response.status}")
                    return False
    except asyncio.TimeoutError:
        logger.error("❌ 文章分析測試超時")
        return False
    except Exception as e:
        logger.error(f"❌ 文章分析測試錯誤: {e}")
        return False

async def main():
    """主診斷函數"""
    logger.info("=== LLM 分析診斷開始 ===")
    
    # 1. 測試 Ollama 連接
    logger.info("1. 測試 Ollama 連接...")
    if not await test_ollama_connection():
        logger.error("Ollama 服務不可用，請檢查服務狀態")
        return
    
    # 2. 測試模型可用性
    logger.info("2. 測試模型可用性...")
    if not await test_model_availability():
        logger.error("目標模型不可用")
        return
    
    # 3. 測試簡單生成
    logger.info("3. 測試簡單生成...")
    if not await test_simple_generation():
        logger.error("簡單生成測試失敗")
        return
    
    # 4. 測試文章分析
    logger.info("4. 測試文章分析...")
    if not await test_article_analysis():
        logger.error("文章分析測試失敗")
        return
    
    logger.info("=== 所有測試通過 ===")

if __name__ == "__main__":
    asyncio.run(main())
