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
  const [searchQuery, setSearchQuery] = useState('');

  // 載入所有作者列表
  useEffect(() => {
    fetchAuthors();
  }, []);

  const fetchAuthors = async () => {
    try {
      const url = `${API_BASE}/authors`;
      console.log('Fetching authors from:', url);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      console.log('Authors response:', data);
      
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

  const searchAuthor = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      // 後端正確路由：/api/authors/{author_name}/articles
      const response = await fetch(`${API_BASE}/authors/${encodeURIComponent(searchQuery)}/articles`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setArticles(data.articles || []);
      setSelectedAuthor(searchQuery);
    } catch (error) {
      console.error('Error searching author:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeArticle = async (articleId: string) => {
    setLoading(true);
    try {
      console.log(`Analyzing article: ${articleId}`);
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ articleId }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Analysis result:', data);
      setAnalysis(data);
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
              />
            </div>
            <button
              onClick={searchAuthor}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Search className="h-4 w-4" />
              {loading ? '搜尋中...' : '搜尋'}
            </button>
          </div>
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
                    setSearchQuery(author.author);
                    searchAuthor();
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