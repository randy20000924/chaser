"""Database models for PTT Stock Crawler."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PTTArticle(Base):
    """PTT文章資料模型."""
    
    __tablename__ = "ptt_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(String(50), unique=True, nullable=False, index=True)  # PTT文章ID
    title = Column(String(500), nullable=False)
    author = Column(String(50), nullable=False, index=True)
    board = Column(String(50), nullable=False, index=True)
    url = Column(String(500), nullable=False, unique=True)
    content = Column(Text)
    publish_time = Column(DateTime, nullable=False, index=True)
    crawl_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 文章統計
    push_count = Column(Integer, default=0)
    boo_count = Column(Integer, default=0)
    arrow_count = Column(Integer, default=0)
    
    # 股票相關資訊
    stock_symbols = Column(JSON)  # 提取的股票代碼列表
    stock_mentions = Column(JSON)  # 股票提及次數統計
    
    # 分類和標籤
    category = Column(String(100))  # 文章分類
    tags = Column(JSON)  # 標籤列表
    sentiment = Column(String(20))  # 情感分析結果
    
    # LLM 分析結果
    analysis_result = Column(JSON)  # 完整的 LLM 分析結果
    analysis_time = Column(DateTime)  # 分析時間
    recommended_stocks = Column(JSON)  # 推薦的股票代碼
    analysis_reason = Column(Text)  # 分析原因
    llm_sentiment = Column(String(20))  # LLM 情感分析
    llm_sectors = Column(JSON)  # LLM 產業分析
    llm_strategy = Column(String(50))  # LLM 策略分析
    llm_risk_level = Column(String(20))  # LLM 風險等級
    
    # 處理狀態
    is_processed = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)  # 是否已進行 LLM 分析
    is_relevant = Column(Boolean, default=True)
    
    # 建立索引
    __table_args__ = (
        Index('idx_author_time', 'author', 'publish_time'),
        Index('idx_board_time', 'board', 'publish_time'),
        Index('idx_publish_time', 'publish_time'),
    )
    
    def __repr__(self):
        return f"<PTTArticle(id={self.article_id}, author={self.author}, title={self.title[:50]}...)>"

class CrawlLog(Base):
    """爬蟲執行日誌模型."""
    
    __tablename__ = "crawl_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crawl_time = Column(DateTime, nullable=False, index=True)
    target_authors = Column(JSON)  # 目標作者列表
    articles_found = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    articles_analyzed = Column(Integer, default=0)  # 新增：分析的文章數量
    errors = Column(JSON)  # 錯誤列表
    duration_seconds = Column(Integer)
    status = Column(String(20), default="success")  # success, error, partial
    
    def __repr__(self):
        return f"<CrawlLog(id={self.id}, time={self.crawl_time}, status={self.status})>"

class AuthorProfile(Base):
    """作者檔案模型."""
    
    __tablename__ = "author_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author = Column(String(50), unique=True, nullable=False, index=True)
    total_articles = Column(Integer, default=0)
    last_article_time = Column(DateTime)
    avg_push_count = Column(Integer, default=0)
    avg_boo_count = Column(Integer, default=0)
    favorite_stocks = Column(JSON)  # 最常提及的股票
    activity_pattern = Column(JSON)  # 活動模式分析
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuthorProfile(author={self.author}, articles={self.total_articles})>"
