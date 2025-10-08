"""Database models for PTT Stock Crawler."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

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
    
    # 處理狀態
    is_processed = Column(Boolean, default=False)
    is_relevant = Column(Boolean, default=True)
    
    # 建立索引
    __table_args__ = (
        Index('idx_author_time', 'author', 'publish_time'),
        Index('idx_board_time', 'board', 'publish_time'),
        Index('idx_stock_symbols', 'stock_symbols', postgresql_using='gin'),
        Index('idx_publish_time', 'publish_time'),
    )
    
    def __repr__(self):
        return f"<PTTArticle(id={self.article_id}, author={self.author}, title={self.title[:50]}...)>"


class CrawlLog(Base):
    """爬蟲執行日誌."""
    
    __tablename__ = "crawl_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crawl_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    target_authors = Column(JSON, nullable=False)
    articles_found = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    errors = Column(JSON)
    duration_seconds = Column(Integer)
    status = Column(String(20), default="success")  # success, error, partial
    
    def __repr__(self):
        return f"<CrawlLog(time={self.crawl_time}, found={self.articles_found}, saved={self.articles_saved})>"


class AuthorProfile(Base):
    """作者檔案."""
    
    __tablename__ = "author_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)
    total_articles = Column(Integer, default=0)
    
    # 作者偏好設定
    preferred_stocks = Column(JSON)  # 常關注的股票
    writing_style = Column(JSON)  # 寫作風格分析
    
    def __repr__(self):
        return f"<AuthorProfile(username={self.username}, active={self.is_active})>"
