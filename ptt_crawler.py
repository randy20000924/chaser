"""PTT股票版爬蟲模組."""

import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from loguru import logger
import random
from random import choice

from config import settings
from models import PTTArticle
from database import db_manager
from article_analyzer import ArticleAnalyzer
class PTTCrawler:
    """PTT爬蟲類別."""
    
    def __init__(self):
        self.base_url = settings.ptt_base_url
        self.stock_board = settings.ptt_stock_board
        self.user_agent = settings.ptt_user_agent
        self.user_agents_pool = settings.user_agents or [self.user_agent]
        self.target_authors = settings.target_authors
        self.session = None
        self.cookies = {"over18": "1"}
        self.proxy = settings.http_proxy_url
        self.analyzer = ArticleAnalyzer()  # 添加分析器
        
    async def __aenter__(self):
        """異步上下文管理器進入."""
        # pick a random UA on session start
        self.user_agent = choice(self.user_agents_pool)
        default_headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        self.session = aiohttp.ClientSession(
            headers=default_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出."""
        if self.session:
            await self.session.close()
    
    async def _get_page(self, url: str, retries: int = 3) -> Optional[str]:
        """取得網頁內容，包含重試機制."""
        for attempt in range(retries):
            try:
                # 隨機延遲避免被偵測
                await asyncio.sleep(random.uniform(1, 3))
                
                # 加上 Referer 指向看板，並隨機延遲與可選代理
                referer_headers = {'Referer': f"{self.base_url}/bbs/{self.stock_board}/index.html"}
                proxy = self.proxy
                # 隨機延遲（更可控）
                await asyncio.sleep(random.uniform(settings.request_min_delay_ms/1000.0, settings.request_max_delay_ms/1000.0))
                async with self.session.get(url, cookies=self.cookies, headers=referer_headers, proxy=proxy) as response:
                    if response.status == 200:
                        # 更新cookies
                        self.cookies.update(response.cookies)
                        return await response.text()
                    elif response.status in (400, 403, 429):
                        logger.warning(f"Access denied for {url}, attempt {attempt + 1}")
                        # 嘗試通過18+驗證
                        try:
                            await self._bypass_over18()
                        except Exception as _:
                            pass
                        # 指數退避等待
                        sleep_s = min(settings.backoff_max_sleep_seconds, 2 ** attempt + random.uniform(0, 2))
                        await asyncio.sleep(sleep_s)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}, attempt {attempt + 1}")
                        await asyncio.sleep(random.uniform(2, 5))
                        
            except Exception as e:
                logger.error(f"Error fetching {url}, attempt {attempt + 1}: {e}")
                await asyncio.sleep(random.uniform(3, 6))
        
        return None

    async def _setup_board_access(self) -> None:
        """設置看板訪問權限，包括 18+ 驗證."""
        try:
            # 先訪問看板首頁
            board_url = f"{self.base_url}/bbs/{self.stock_board}/index.html"
            logger.info(f"Setting up access for {self.stock_board} board")
            
            async with self.session.get(board_url, cookies=self.cookies, proxy=self.proxy) as response:
                if response.status == 200:
                    # 檢查是否需要 18+ 驗證
                    html = await response.text()
                    if "over18" in html or "18歲" in html:
                        logger.info("18+ verification required, submitting...")
                        await self._bypass_over18()
                    else:
                        logger.info("No 18+ verification needed")
                else:
                    logger.warning(f"Failed to access board: {response.status}")
        except Exception as e:
            logger.error(f"Error setting up board access: {e}")

    async def _bypass_over18(self) -> None:
        """提交18+驗證並設定cookie."""
        ask_url = urljoin(self.base_url, "/ask/over18")
        payload = {"from": f"/bbs/{self.stock_board}/index.html", "yes": "yes"}
        headers = {"User-Agent": self.user_agent, "Referer": f"{self.base_url}/bbs/{self.stock_board}/index.html"}
        async with self.session.post(ask_url, data=payload, headers=headers, cookies=self.cookies, proxy=self.proxy) as resp:
            if resp.status in (200, 302):
                self.cookies.update({"over18": "1"})
            else:
                # 隨機切換 UA 再試一次
                self.user_agent = choice(self.user_agents_pool)
                try:
                    async with self.session.post(ask_url, data=payload, headers={**headers, 'User-Agent': self.user_agent}, cookies=self.cookies, proxy=self.proxy) as _:
                        self.cookies.update({"over18": "1"})
                except Exception:
                    pass

    
    
    def _parse_author_search_results(self, html: str, target_author: str) -> List[Dict]:
        """解析作者搜尋結果頁面."""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # 尋找文章列表
        for row in soup.find_all('div', class_='r-ent'):
            try:
                # 取得文章標題和連結
                title_cell = row.find('div', class_='title')
                if not title_cell:
                    continue
                
                title_link = title_cell.find('a')
                if not title_link:
                    continue
                
                title = title_link.text.strip()
                article_url = title_link.get('href')
                
                # 跳過已刪除的文章
                if title.startswith('(本文已被刪除)') or title.startswith('(本文已被'):
                    continue
                
                # 取得作者 - 修正：作者在 meta 裡面
                meta_cell = row.find('div', class_='meta')
                author = ''
                if meta_cell:
                    author_cell = meta_cell.find('div', class_='author')
                    author = author_cell.text.strip() if author_cell else ''
                
                # 嚴格匹配作者名稱（大小寫敏感）
                if author != target_author:
                    continue
                
                # 取得推文數
                push_cell = row.find('div', class_='nrec')
                push_count = 0
                if push_cell and push_cell.text.strip():
                    push_text = push_cell.text.strip()
                    if push_text.isdigit():
                        push_count = int(push_text)
                    elif push_text == '爆':
                        push_count = 100
                
                # 取得日期
                date_cell = row.find('div', class_='date')
                date_str = date_cell.text.strip() if date_cell else ''
                
                # 嘗試解析日期，如果沒有年份，補上當前年份
                try:
                    # PTT列表頁日期格式通常是 MM/DD
                    parsed_date = datetime.strptime(date_str, '%m/%d').replace(year=datetime.now().year)
                except ValueError:
                    parsed_date = datetime.now()  # 解析失敗則用當前時間
                
                logger.info(f"Found article: {title[:50]}... by {author}")
                
                articles.append({
                    'title': title,
                    'author': author,
                    'url': urljoin(self.base_url, article_url),
                    'push_count': push_count,
                    'date_str': date_str,
                    'publish_time_from_list': parsed_date
                })
                
            except Exception as e:
                logger.error(f"Error parsing article row: {e}")
                continue
        
        logger.info(f"Parsed {len(articles)} articles for author {target_author}")
        return articles
    
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
            
            # 提取股票代碼
            stock_symbols = self._extract_stock_symbols(content)
            
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
                analysis_result = self.analyzer._analyze_content(temp_article)
                
                logger.info(f"LLM analysis completed for article: {article_id}")
                
                return {
                    'article_id': article_id,
                    'content': content,
                    'publish_time': publish_time,
                    'stock_symbols': stock_symbols,
                    'analysis_result': analysis_result  # 添加分析結果
                }
                
            except Exception as e:
                logger.error(f"LLM analysis failed for article {article_id}: {e}")
                # 即使分析失敗，也返回基本內容
                return {
                    'article_id': article_id,
                    'content': content,
                    'publish_time': publish_time,
                    'stock_symbols': stock_symbols,
                    'analysis_result': None
                }
            
        except Exception as e:
            logger.error(f"Error parsing article content from {article_url}: {e}")
            return None
    
    def _extract_article_id(self, url: str) -> str:
        """從URL提取文章ID."""
        # PTT URL格式: /bbs/Stock/M.1234567890.A.123.html
        match = re.search(r'/([A-Z]\.[0-9]+\.[A-Z]\.[0-9]+)\.html', url)
        return match.group(1) if match else url.split('/')[-1].replace('.html', '')
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> datetime:
        """提取發文時間."""
        try:
            # 尋找時間資訊
            time_elements = soup.find_all('span', class_='article-meta-value')
            for element in time_elements:
                time_text = element.text.strip()
                # 嘗試解析時間格式
                time_formats = [
                    '%a %b %d %H:%M:%S %Y',
                    '%m/%d %H:%M',
                    '%Y-%m-%d %H:%M:%S'
                ]
                
                for fmt in time_formats:
                    try:
                        return datetime.strptime(time_text, fmt)
                    except ValueError:
                        continue
        except Exception as e:
            logger.error(f"Error extracting publish time: {e}")
        
        # 如果無法解析，返回當前時間
        return datetime.now()
    
    def _extract_stock_symbols(self, content: str) -> List[str]:
        """從文章內容提取股票代碼."""
        # 台灣股票代碼模式 (4位數字)
        stock_pattern = r'\b([0-9]{4})\b'
        matches = re.findall(stock_pattern, content)
        
        # 過濾掉明顯不是股票代碼的數字
        stock_symbols = []
        for match in matches:
            # 簡單過濾：排除年份、電話號碼等
            if not (match.startswith('20') or match.startswith('19') or 
                   match.startswith('0') or match.startswith('1')):
                stock_symbols.append(match)
        
        return list(set(stock_symbols))  # 去重
    
    async def crawl_author_articles(self, author: str, max_articles: int = 50, since_days: int = 3) -> List[Dict]:
        """通過作者搜尋功能爬取特定作者的文章，僅限最近 since_days 天."""
        logger.info(f"Starting to crawl articles for author: {author}")
        
        # 先訪問看板首頁並通過 18+ 驗證
        await self._setup_board_access()
        
        articles = []
        cutoff_time = datetime.now() - timedelta(days=since_days)
        
        # 使用作者搜尋功能
        search_url = f"{self.base_url}/bbs/Stock/search?q=author:{author}"
        logger.info(f"Searching for author {author} at {search_url}")
        
        html = await self._get_page(search_url)
        if not html:
            logger.error(f"Failed to get search results for author {author}")
            return articles
        
        # 解析搜尋結果
        search_articles = self._parse_author_search_results(html, author)
        logger.info(f"Found {len(search_articles)} articles from search results")
        
        # 處理每篇文章
        for article_info in search_articles[:max_articles]:
            # 檢查文章發布時間是否在範圍內
            if article_info.get('publish_time_from_list') and article_info['publish_time_from_list'] < cutoff_time:
                logger.info(f"Article is older than {since_days} days, stopping processing")
                break
            
            logger.info(f"Processing article: {article_info['title'][:50]}...")
            
            # 取得文章詳細內容
            content_info = await self._get_article_content(article_info['url'])
            if content_info:
                # 再次確認詳細內容中的發布時間是否在範圍內
                if content_info.get('publish_time') and content_info['publish_time'] < cutoff_time:
                    logger.info(f"Article content publish time is older than {since_days} days, skipping")
                    continue
                article_info.update(content_info)
                articles.append(article_info)
            
            # 避免請求過於頻繁
            await asyncio.sleep(random.uniform(2, 4))
        
        logger.info(f"Found {len(articles)} articles for author {author}")
        return articles

    
    async def crawl_all_authors(self) -> List[Dict]:
        """爬取所有目標作者的文章（使用作者搜尋功能）."""
        all_articles = []
        
        for author in self.target_authors:
            logger.info(f"Crawling articles for author: {author}")
            author_articles = await self.crawl_author_articles(author, max_articles=100, since_days=3)
            all_articles.extend(author_articles)
            logger.info(f"Found {len(author_articles)} articles for {author}")
        
        logger.info(f"Total articles found: {len(all_articles)}")
        return all_articles
