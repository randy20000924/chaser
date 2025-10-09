"""Configuration management for PTT Stock Crawler."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql+psycopg://ptt_user:ptt_password@localhost:5432/ptt_stock_crawler"
    
    # PTT Configuration
    ptt_base_url: str = "https://www.ptt.cc"
    ptt_stock_board: str = "Stock"
    ptt_user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # Target Authors
    target_authors: List[str] = ["mrp"]
    
    # Crawler Settings
    crawl_interval: int = 300  # seconds
    max_articles_per_crawl: int = 100  # 增加文章數量以記錄更多作者
    enable_selenium: bool = False
    http_proxy_url: str | None = None  # e.g. http://127.0.0.1:8888
    # 搜尋範圍設定（天數）
    search_days: int = 3  # 搜尋最近3天
    request_min_delay_ms: int = 800
    request_max_delay_ms: int = 2500
    backoff_max_sleep_seconds: int = 20
    user_agents: list[str] = [
        # A small rotating pool of realistic desktop UAs
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    ]
    
    # MCP Server
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/crawler.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @field_validator("target_authors", mode="before")
    @classmethod
    def _parse_target_authors(cls, value):
        """Allow comma-separated string in env, e.g. "mrp,foo,bar"."""
        if isinstance(value, str):
            return [author.strip() for author in value.split(",") if author.strip()]
        return value


# Global settings instance
settings = Settings()
