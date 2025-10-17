"""股票代碼驗證模組 - 使用 FinMind 和 Alpha Vantage API."""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Tuple
from loguru import logger

class StockValidator:
    """股票代碼驗證器."""
    
    def __init__(self):
        import os
        self.finmind_api_key = os.getenv("FINMIND_API_KEY", "")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.finmind_base_url = "https://api.finmindtrade.com/api/v4"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # 台股代碼模式 (4位數字)
        self.taiwan_pattern = re.compile(r'\b(\d{4})\b')
        # 美股代碼模式 (1-5位字母)
        self.us_pattern = re.compile(r'\b([A-Z]{1,5})\b')
    
    def extract_potential_codes(self, content: str) -> Tuple[List[str], List[str]]:
        """從內容中提取潛在的股票代碼."""
        taiwan_codes = self.taiwan_pattern.findall(content)
        us_codes = self.us_pattern.findall(content)
        
        # 過濾掉明顯不是股票代碼的數字
        taiwan_codes = [code for code in taiwan_codes if self._is_valid_taiwan_code(code)]
        us_codes = [code for code in us_codes if self._is_valid_us_code(code)]
        
        return taiwan_codes, us_codes
    
    def _is_valid_taiwan_code(self, code: str) -> bool:
        """檢查是否為有效的台股代碼."""
        # 台股代碼範圍檢查
        if len(code) != 4:
            return False
        
        # 排除明顯不是股票代碼的數字
        if code.startswith('0') or code.startswith('9'):
            return False
        
        # 檢查是否在合理範圍內
        try:
            num = int(code)
            return 1000 <= num <= 9999
        except:
            return False
    
    def _is_valid_us_code(self, code: str) -> bool:
        """檢查是否為有效的美股代碼."""
    
        # 排除單字母代碼
        if len(code) == 1:
            return False
        
        # 排除常見的非股票代碼英文詞彙
        excluded = {
            # 冠詞、介係詞、連接詞
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'WITH', 'FROM', 'INTO', 'OVER',
            'ABOUT', 'AFTER', 'UNDER', 'UNTIL', 'UPON', 'THROUGH', 'BETWEEN', 'DURING',
            'AT', 'BY', 'IN', 'ON', 'TO', 'OF', 'AS', 'OR', 'AN', 'IS', 'IT', 'BE', 'DO',
            
            # 代名詞
            'YOU', 'HER', 'HIM', 'HIS', 'OUR', 'THEIR', 'THEM', 'THESE', 'THOSE', 'THIS',
            'THAT', 'HE', 'SHE', 'WE', 'THEY', 'US', 'MY', 'YOUR', 'ITS', 'WHO', 'WHICH',
            'WHAT', 'WHOSE', 'WHOM',
            
            # 常見動詞
            'WAS', 'WERE', 'HAD', 'HAS', 'BEEN', 'BEING', 'HAVE', 'CAN', 'COULD', 'WILL',
            'WOULD', 'SHALL', 'SHOULD', 'MAY', 'MIGHT', 'MUST', 'SAID', 'DID', 'MADE', 
            'COME', 'CAME', 'MAKE', 'TAKE', 'GIVE', 'FIND', 'CALL', 'GET', 'GO', 'KNOW',
            'SEE', 'SAY', 'USE', 'TELL', 'WORK', 'SHOW', 'LEAVE', 'FEEL', 'PUT', 'KEEP',
            'LET', 'BEGIN', 'SEEM', 'HELP', 'TURN', 'START', 'WRITE', 'MOVE', 'TRY',
            'LIVE', 'STAND', 'MEAN', 'LEAD', 'HEAR', 'MEET', 'RUN', 'LOOK', 'THINK',
            'WANT', 'NEED', 'ASK', 'BECOME', 'BRING', 'FOLLOW', 'HOLD', 'LOSE', 'PAY',
            
            # 常見形容詞
            'ONE', 'TWO', 'FIRST', 'LAST', 'LONG', 'GOOD', 'NEW', 'OLD', 'HIGH', 'GREAT',
            'BIG', 'SMALL', 'LARGE', 'BEST', 'NEXT', 'EARLY', 'YOUNG', 'SAME', 'FEW',
            'OWN', 'OTHER', 'RIGHT', 'SURE', 'REAL', 'TRUE', 'FULL', 'LESS', 'MOST',
            'MUCH', 'MANY', 'MORE', 'SUCH', 'BOTH', 'EACH', 'EVERY', 'LITTLE', 'WHOLE',
            
            # 常見名詞
            'TIME', 'YEAR', 'WAY', 'DAY', 'MAN', 'THING', 'WOMAN', 'LIFE', 'CHILD', 'WORLD',
            'SCHOOL', 'STATE', 'FAMILY', 'STUDENT', 'GROUP', 'COUNTRY', 'PROBLEM', 'HAND',
            'PART', 'PLACE', 'CASE', 'WEEK', 'COMPANY', 'SYSTEM', 'PROGRAM', 'QUESTION',
            'WORK', 'GOVERNMENT', 'NUMBER', 'NIGHT', 'POINT', 'HOME', 'WATER', 'ROOM',
            'MOTHER', 'AREA', 'MONEY', 'STORY', 'FACT', 'MONTH', 'BOOK', 'EYE', 'JOB',
            'WORD', 'BUSINESS', 'ISSUE', 'SIDE', 'KIND', 'HEAD', 'HOUSE', 'SERVICE',
            'FRIEND', 'FATHER', 'POWER', 'HOUR', 'GAME', 'LINE', 'END', 'MEMBER', 'LAW',
            'DOOR', 'BACK', 'FACE', 'BODY', 'NAME', 'IDEA', 'LEVEL',
            
            # 副詞和其他高頻詞
            'ALL', 'WHEN', 'THERE', 'IF', 'UP', 'OUT', 'THEN', 'SO', 'SOME', 'LIKE',
            'NOW', 'DOWN', 'ONLY', 'ALSO', 'WELL', 'VERY', 'EVEN', 'BACK', 'JUST',
            'WHERE', 'HOW', 'WHY', 'TOO', 'HERE', 'THAN', 'ONCE', 'AGAIN', 'NEVER',
            'ALWAYS', 'OFTEN', 'SOMETIMES', 'AWAY', 'STILL', 'WHILE', 'SINCE', 'YET',
            'EVER', 'ALREADY', 'QUITE', 'ALMOST', 'ENOUGH', 'RATHER', 'PERHAPS',
            
            # 數字相關
            'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN',
            'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY',
            'HUNDRED', 'THOUSAND', 'MILLION', 'BILLION',
            
            # 其他常見詞
            'YES', 'NO', 'MAYBE', 'SURE', 'OKAY', 'PLEASE', 'THANK', 'THANKS', 'SORRY',
            'HELLO', 'GOODBYE', 'BEFORE', 'BECAUSE', 'THOUGH', 'ALTHOUGH', 'UNLESS',
            'WHETHER', 'EITHER', 'NEITHER', 'BOTH', 'AMONG', 'AROUND', 'ACROSS', 'ALONG',
            'BEHIND', 'BELOW', 'BESIDE', 'BEYOND', 'WITHIN', 'WITHOUT', 'AGAINST',
            'TOWARD', 'TOWARDS',
        }
        
        if code in excluded:
            return False
        
        # 美股代碼通常是2-5位字母
        if not (2 <= len(code) <= 5 and code.isalpha()):
            return False
        
        return True
    
    async def validate_taiwan_stock(self, code: str) -> Optional[Dict]:
        """驗證台股代碼並獲取基本信息."""
        try:
            async with aiohttp.ClientSession() as session:
                # 使用 FinMind API 查詢台股基本信息
                url = f"{self.finmind_base_url}/taiwan_stock_info"
                params = {
                    'token': self.finmind_api_key,
                    'stock_id': code
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 200 and data.get('data'):
                            stock_info = data['data'][0]
                            return {
                                'code': code,
                                'name': stock_info.get('stock_name', ''),
                                'market': 'TW',
                                'type': 'taiwan_stock',
                                'valid': True
                            }
        except Exception as e:
            logger.warning(f"Error validating Taiwan stock {code}: {e}")
        
        return None
    
    async def validate_us_stock(self, code: str) -> Optional[Dict]:
        """驗證美股代碼並獲取基本信息."""
        try:
            async with aiohttp.ClientSession() as session:
                # 使用 Alpha Vantage API 查詢美股基本信息
                url = self.alpha_vantage_base_url
                params = {
                    'function': 'SYMBOL_SEARCH',
                    'keywords': code,
                    'apikey': self.alpha_vantage_api_key
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'bestMatches' in data and data['bestMatches']:
                            match = data['bestMatches'][0]
                            if match.get('1. symbol', '').upper() == code.upper():
                                return {
                                    'code': code,
                                    'name': match.get('2. name', ''),
                                    'market': 'US',
                                    'type': 'us_stock',
                                    'valid': True
                                }
        except Exception as e:
            logger.warning(f"Error validating US stock {code}: {e}")
        
        return None
    
    async def validate_stocks(self, content: str) -> List[Dict]:
        """驗證內容中的所有股票代碼."""
        taiwan_codes, us_codes = self.extract_potential_codes(content)
        
        validated_stocks = []
        
        # 驗證台股代碼
        for code in taiwan_codes:
            stock_info = await self.validate_taiwan_stock(code)
            if stock_info:
                validated_stocks.append(stock_info)
        
        # 驗證美股代碼
        for code in us_codes:
            stock_info = await self.validate_us_stock(code)
            if stock_info:
                validated_stocks.append(stock_info)
        
        # 去重
        seen_codes = set()
        unique_stocks = []
        for stock in validated_stocks:
            if stock['code'] not in seen_codes:
                seen_codes.add(stock['code'])
                unique_stocks.append(stock)
        
        logger.info(f"Validated {len(unique_stocks)} stocks from content")
        return unique_stocks

# 創建全局實例
stock_validator = StockValidator()
