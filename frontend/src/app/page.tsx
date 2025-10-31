'use client';

import { useState, useEffect } from 'react';
import { Search, TrendingUp, User, Calendar, ExternalLink } from 'lucide-react';

interface Author {
  author: string;
  article_count: number;
  last_activity: string;
}

interface Article {
  article_id: string;
  title: string;
  author: string;
  publish_time: string;
  url: string;
  push_count: number;
}

interface Analysis {
  author: string;
  date: string;
  url: string;
  recommended_stocks: string[];
  reason: string;
}

export default function Home() {
  // 使用環境變數或默認的後端 URL
  const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://www.chaser.cloud/api';
  const [authors, setAuthors] = useState<Author[]>([]);
  const [selectedAuthor, setSelectedAuthor] = useState('');
  const [articles, setArticles] = useState<Article[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [crawlStatus, setCrawlStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  // 載入所有作者列表
  useEffect(() => {
    fetchAuthors();
  }, []);

  const fetchAuthors = async () => {
    try {
      const url = `${API_BASE}/authors`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      
      // 為每個作者獲取文章數量
      const authorsWithCounts = await Promise.all(
        data.authors.map(async (author: string) => {
          try {
            const authorResponse = await fetch(`${API_BASE}/authors/${encodeURIComponent(author)}/articles`);
            if (authorResponse.ok) {
              const authorData = await authorResponse.json();
              return {
                author,
                article_count: authorData.total || 0,
                last_activity: authorData.articles?.[0]?.publish_time || ''
              };
            }
            return { author, article_count: 0, last_activity: '' };
          } catch (error) {
            console.error(`Error fetching articles for ${author}:`, error);
            return { author, article_count: 0, last_activity: '' };
          }
        })
      );
      
      setAuthors(authorsWithCounts);
    } catch (error) {
      console.error('Error fetching authors:', error);
    }
  };

  const checkCrawlStatus = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/crawl/status`);
      if (response.ok) {
        const status = await response.json();
        return status.is_running || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking crawl status:', error);
      return false;
    }
  };

  const triggerCrawl = async (author: string): Promise<boolean> => {
    setCrawling(true);
    setCrawlStatus('正在啟動爬蟲...');
    
    try {
      // 觸發爬蟲
      const response = await fetch(`${API_BASE}/crawl/author/${encodeURIComponent(author)}`, {
        method: 'POST',
      });

      if (response.status === 409) {
        // 爬蟲正在運行中，輪詢狀態
        setCrawlStatus('爬蟲正在運行中，等待完成...');
        
        // 輪詢直到爬蟲完成
        const pollInterval = setInterval(async () => {
          const isRunning = await checkCrawlStatus();
          if (!isRunning) {
            clearInterval(pollInterval);
            setCrawling(false);
            setCrawlStatus('');
            // 重新查詢文章
            await searchAuthorInternal(author);
          }
        }, 2000); // 每2秒檢查一次

        // 設置超時（最多等待5分鐘）
        setTimeout(() => {
          clearInterval(pollInterval);
          setCrawling(false);
          setCrawlStatus('');
        }, 300000);
        
        return false;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      setCrawlStatus('爬蟲完成！');
      
      // 等待一下讓資料寫入資料庫
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return true;
    } catch (error) {
      console.error('Error triggering crawl:', error);
      setCrawlStatus(`爬蟲失敗: ${error instanceof Error ? error.message : '未知錯誤'}`);
      return false;
    } finally {
      setCrawling(false);
      setTimeout(() => setCrawlStatus(''), 3000); // 3秒後清除狀態訊息
    }
  };

  const searchAuthorInternal = async (author: string) => {
    try {
      // 後端正確路由：/api/authors/{author_name}/articles
      const response = await fetch(`${API_BASE}/authors/${encodeURIComponent(author)}/articles`);
      
      if (!response.ok) {
        if (response.status === 404) {
          // 找不到作者，返回空結果
          return { articles: [], found: false };
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      return { articles: data.articles || [], found: data.articles && data.articles.length > 0 };
    } catch (error) {
      console.error('Error searching author:', error);
      return { articles: [], found: false };
    }
  };

  const searchAuthor = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setSelectedAuthor(searchQuery);
    
    try {
      // 先嘗試查詢作者
      const result = await searchAuthorInternal(searchQuery);
      
      if (result.found && result.articles.length > 0) {
        // 找到作者且有文章，直接顯示
        setArticles(result.articles);
      } else {
        // 沒找到作者或沒有文章，觸發爬蟲
        setCrawlStatus('未找到該作者，正在啟動爬蟲...');
        const crawlSuccess = await triggerCrawl(searchQuery);
        
        if (crawlSuccess) {
          // 爬蟲完成後重新查詢
          const newResult = await searchAuthorInternal(searchQuery);
          setArticles(newResult.articles);
        } else {
          // 如果爬蟲失敗或正在運行中，嘗試再次查詢
          setTimeout(async () => {
            const retryResult = await searchAuthorInternal(searchQuery);
            setArticles(retryResult.articles);
          }, 2000);
        }
      }
    } catch (error) {
      console.error('Error in searchAuthor:', error);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeArticle = async (articleId: string) => {
    setLoading(true);
    try {
      console.log(`Analyzing article: ${articleId}`);
      const response = await fetch(`${API_BASE}/articles/${articleId}/analysis`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Analysis result:', data);
      
      // 格式化數據以符合前端期望
      const formattedData = {
        author: data.author || 'Unknown',
        date: data.date || new Date().toISOString().split('T')[0],
        url: data.url || '',
        recommended_stocks: data.recommended_stocks || [],
        reason: data.reason || 'No analysis available'
      };
      
      setAnalysis(formattedData);
    } catch (error) {
      console.error('Error analyzing article:', error);
      // 顯示錯誤信息給用戶
      setAnalysis({
        author: 'Error',
        date: new Date().toISOString().split('T')[0],
        url: '',
        recommended_stocks: [],
        reason: `分析失敗: ${error instanceof Error ? error.message : '未知錯誤'}`
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <img 
                src="/chaser-logo-nav.png" 
                alt="Chaser Logo" 
                className="h-8 w-auto"
        />
              <h1 className="ml-2 text-xl font-semibold text-black"></h1>
            </div>
            <div className="text-sm text-gray-500">
              每天下午3點自動更新
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-lg font-medium text-black mb-4">搜尋作者</h2>
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="輸入作者名稱..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                onKeyPress={(e) => e.key === 'Enter' && searchAuthor()}
                disabled={crawling || loading}
              />
            </div>
            <button
              onClick={searchAuthor}
              disabled={loading || crawling}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
              <Search className="h-4 w-4" />
              {crawling ? '爬蟲中...' : loading ? '搜尋中...' : '搜尋'}
            </button>
          </div>
          {/* 爬蟲狀態顯示 */}
          {crawlStatus && (
            <div className={`mt-4 p-3 rounded-md ${
              crawlStatus.includes('失敗') 
                ? 'bg-red-50 border border-red-200 text-red-800'
                : crawlStatus.includes('完成')
                ? 'bg-green-50 border border-green-200 text-green-800'
                : 'bg-blue-50 border border-blue-200 text-blue-800'
            }`}>
              <div className="flex items-center gap-2">
                {crawling && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                )}
                <span className="text-sm">{crawlStatus}</span>
              </div>
            </div>
          )}
        </div>

        {/* Authors List */}
        {authors.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h2 className="text-lg font-medium text-black mb-4">活躍作者</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {authors.slice(0, 12).map((author) => (
                <div
                  key={author.author}
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => {
                    // 僅填入搜尋欄，不自動調出文章
                    setSearchQuery(author.author);
                  }}
                >
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-500" />
                    <span className="font-medium text-black">{author.author}</span>
                  </div>
                  <div className="text-sm text-black mt-1">
                    {author.article_count} 篇文章
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Articles List */}
        {articles.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h2 className="text-lg font-medium text-black mb-4">
              {selectedAuthor} 的文章 ({articles.length} 篇)
            </h2>
            <div className="space-y-4">
              {articles.map((article) => (
                <div
                  key={article.article_id}
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-black mb-2">{article.title}</h3>
                      <div className="flex items-center gap-4 text-sm text-black">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {new Date(article.publish_time).toLocaleDateString()}
                        </span>
                        <span>
                          推文: {article.push_count >= 100 ? (
                            <span className="text-red-600 font-bold">爆</span>
                          ) : article.push_count === -1 ? (
                            <span className="text-gray-600 font-bold">X</span>
                          ) : (
                            article.push_count
                          )}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <a
                        href={article.url}
          target="_blank"
          rel="noopener noreferrer"
                        className="p-2 text-gray-400 hover:text-gray-600"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                      <button
                        onClick={() => analyzeArticle(article.article_id)}
                        disabled={loading}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        分析
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analysis Result */}
        {analysis && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-medium text-black mb-4">分析結果</h2>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-black mb-1">作者</div>
                  <div className="font-medium text-black">{analysis.author}</div>
                </div>
                <div>
                  <div className="text-sm text-black mb-1">日期</div>
                  <div className="font-medium text-black">{analysis.date}</div>
                </div>
                <div className="md:col-span-2">
                  <div className="text-sm text-black mb-1">推薦標的</div>
                  <div className="flex flex-wrap gap-2">
                    {analysis.recommended_stocks.map((stock, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded"
                      >
                        {stock}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="md:col-span-2">
                  <div className="text-sm text-black mb-1">推薦原因</div>
                  <div className="text-black">{analysis.reason}</div>
                </div>
                <div className="md:col-span-2">
                  <a
                    href={analysis.url}
          target="_blank"
          rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm"
                  >
                    <ExternalLink className="h-4 w-4" />
                    查看原文
        </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}