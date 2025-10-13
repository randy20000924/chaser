"""PTT股票版爬蟲模組."""

import asyncio
import aiohttp
import random
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from loguru import logger

from config import settings
from models import PTTArticle
from article_analyzer import analyzer
from stock_validator import stock_validator

class PTTCrawler:
    """PTT股票版爬蟲類別."""
    
    def __init__(self):
        self.base_url = settings.PTT_BASE_URL
        self.stock_board = settings.PTT_STOCK_BOARD
        self.target_authors = settings.TARGET_AUTHORS
        self.user_agents = settings.USER_AGENTS
        self.session = None
        self.analyzer = analyzer
        self.stock_validator = stock_validator
    
    async def __aenter__(self):
        """異步上下文管理器入口."""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': random.choice(self.user_agents)},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口."""
        if self.session:
            await self.session.close()
    
    async def _get_page(self, url: str) -> Optional[str]:
        """取得網頁內容."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to get page {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting page {url}: {e}")
            return None
    
    async def _setup_board_access(self) -> bool:
        """設置看板訪問權限."""
        try:
            board_url = f"{self.base_url}/bbs/{self.stock_board}/index.html"
            html = await self._get_page(board_url)
            
            if not html:
                return False
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 檢查是否需要18+驗證
            if "您要查看的看板需要特殊權限" in html:
                logger.info("Board requires special permission")
                return False
            
            logger.info("No 18+ verification needed")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up board access: {e}")
            return False
    
    def _extract_article_id(self, url: str) -> str:
        """從URL提取文章ID."""
        try:
            # 從URL中提取文章ID，例如：M.1760105224.A.507
            match = re.search(r'M\.\d+\.A\.\d+', url)
            return match.group(0) if match else url.split('/')[-1].replace('.html', '')
        except:
            return url.split('/')[-1].replace('.html', '')
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> datetime:
        """提取發文時間."""
        try:
            # 查找時間信息
            time_elements = soup.find_all('span', class_='article-meta-value')
            for element in time_elements:
                text = element.get_text().strip()
                if '年' in text and '月' in text and '日' in text:
                    # 解析中文日期格式
                    time_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
                    if time_match:
                        year, month, day = time_match.groups()
                        return datetime(int(year), int(month), int(day))
            
            # 如果找不到，返回當前時間
            return datetime.now()
        except:
            return datetime.now()
    
    async def _extract_and_validate_stocks(self, content: str) -> List[Dict]:
        """提取並驗證股票代碼."""
        try:
            # 使用股票驗證器來獲取有效的股票代碼
            validated_stocks = await self.stock_validator.validate_stocks(content)
            
            # 提取股票代碼列表
            stock_codes = [stock['code'] for stock in validated_stocks]
            
            logger.info(f"Found {len(validated_stocks)} valid stocks: {stock_codes}")
            return validated_stocks
            
        except Exception as e:
            logger.error(f"Error extracting and validating stocks: {e}")
            return []
    
    async def _get_article_content(self, article_url: str) -> Optional[Dict]:
        """取得文章詳細內容並進行 LLM 分析."""
        html = await self._get_page(article_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        try:
            # 取得文章內容
            main_content = soup.find('div', id='main-content')
            if not main_content:
                return None

            # 移除推文部分
            for push in main_content.find_all('div', class_='push'):
                push.decompose()

            # 移除回文部分（以冒號開頭的span元素）
            for span in main_content.find_all('span', class_='f6'):
                if span.text.strip().startswith(':'):
                    span.decompose()

            # 取得純文字內容
            content = main_content.get_text().strip()
            
            # 取得文章ID
            article_id = self._extract_article_id(article_url)
            
            # 取得發文時間
            publish_time = self._extract_publish_time(soup)
            
            # 提取並驗證股票代碼
            validated_stocks = await self._extract_and_validate_stocks(content)
            stock_symbols = [stock['code'] for stock in validated_stocks]
            
            # 進行 LLM 分析
            logger.info(f"Starting LLM analysis for article: {article_id}")
            try:
                # 創建臨時的 PTTArticle 對象進行分析
                temp_article = PTTArticle(
                    article_id=article_id,
                    title="",  # 標題會在後續處理中設置
                    author="",  # 作者會在後續處理中設置
                    board=self.stock_board,
                    url=article_url,
                    content=content,
                    publish_time=publish_time,
                    stock_symbols=stock_symbols
                )
                
                # 進行 LLM 分析
                analysis_result = await self.analyzer._analyze_content(temp_article)
                
                logger.info(f"LLM analysis completed for article: {article_id}")
                
                return {
                    'article_id': article_id,
                    'content': content,
                    'publish_time': publish_time,
                    'stock_symbols': stock_symbols,
                    'validated_stocks': validated_stocks,  # 添加驗證後的股票信息
                    'analysis_result': analysis_result
                }
                
            except Exception as e:
                logger.error(f"LLM analysis failed for article {article_id}: {e}")
                # 即使分析失敗，也返回基本內容
                return {
                    'article_id': article_id,
                    'content': content,
                    'publish_time': publish_time,
                    'stock_symbols': stock_symbols,
                    'validated_stocks': validated_stocks,
                    'analysis_result': None
                }
            
        except Exception as e:
            logger.error(f"Error parsing article content from {article_url}: {e}")
            return None
    
    async def _parse_author_search_results(self, html: str, author: str) -> List[Dict]:
        """解析作者搜尋結果."""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        try:
            # 查找文章列表
            article_elements = soup.find_all('div', class_='r-ent')
            
            for element in article_elements:
                try:
                    # 提取文章標題和連結
                    title_element = element.find('div', class_='title')
                    if not title_element:
                        continue
                    
                    link_element = title_element.find('a')
                    if not link_element:
                        continue
                    
                    title = link_element.get_text().strip()
                    article_url = urljoin(self.base_url, link_element.get('href'))
                    
                    # 提取推文數
                    push_element = element.find('div', class_='nrec')
                    push_count = 0
                    if push_element:
                        push_text = push_element.get_text().strip()
                        if push_text.isdigit():
                            push_count = int(push_text)
                    
                    # 提取日期
                    date_element = element.find('div', class_='date')
                    date_str = date_element.get_text().strip() if date_element else ""
                    
                    articles.append({
                        'title': title,
                        'url': article_url,
                        'push_count': push_count,
                        'date': date_str,
                        'author': author
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing article element: {e}")
                    continue
            
            logger.info(f"Parsed {len(articles)} articles for author {author}")
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return []
    
    async def crawl_author_articles(self, author: str) -> List[Dict]:
        """爬取特定作者的文章."""
        logger.info(f"Starting to crawl articles for author: {author}")
        
        # 設置看板訪問
        if not await self._setup_board_access():
            logger.error("Failed to setup board access")
            return []
        
        try:
            # 搜尋作者文章
            search_url = f"{self.base_url}/bbs/{self.stock_board}/search?q=author:{author}"
            logger.info(f"Searching for author {author} at {search_url}")
            
            html = await self._get_page(search_url)
            if not html:
                logger.error(f"Failed to get search results for {author}")
                return []
            
            # 解析搜尋結果
            articles = await self._parse_author_search_results(html, author)
            logger.info(f"Found {len(articles)} articles from search results")
            
            # 處理每篇文章
            processed_articles = []
            for article in articles:
                try:
                    logger.info(f"Processing article: {article['title']}")
                    
                    # 取得文章詳細內容
                    article_data = await self._get_article_content(article['url'])
                    if not article_data:
                        continue
                    
                    # 合併數據
                    article_data.update({
                        'title': article['title'],
                        'author': author,
                        'push_count': article['push_count']
                    })
                    
                    # 檢查文章是否在時間範圍內
                    days_ago = (datetime.now() - article_data['publish_time']).days
                    if days_ago > settings.SEARCH_DAYS:
                        logger.info(f"Article is older than {settings.SEARCH_DAYS} days, stopping processing")
                        break
                    
                    processed_articles.append(article_data)
                    
                    # 添加延遲避免被阻擋
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.error(f"Error processing article {article.get('title', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(processed_articles)} articles for author {author}")
            return processed_articles
            
        except Exception as e:
            logger.error(f"Error crawling articles for author {author}: {e}")
            return []
    
    async def crawl_all_authors(self) -> List[Dict]:
        """爬取所有目標作者的文章."""
        all_articles = []
        
        for author in self.target_authors:
            logger.info(f"Crawling articles for author: {author}")
            articles = await self.crawl_author_articles(author)
            all_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles for {author}")
        
        logger.info(f"Total articles found: {len(all_articles)}")
        return all_articles
