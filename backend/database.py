"""Database connection and session management."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
from functools import wraps

from config import settings
from models import Base


# 建立資料庫引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False  # 設為True可看到SQL語句
)

# 建立Session工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """建立所有資料表."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """取得資料庫session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[Session, None]:
    """異步取得資料庫session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_async(func):
    """將同步函數包裝為異步執行."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper


class DatabaseManager:
    """資料庫管理類別."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """建立資料表."""
        create_tables()
    
    def get_session(self) -> Session:
        """取得新的session."""
        return self.SessionLocal()
    
    async def health_check(self) -> bool:
        """檢查資料庫連線狀態."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False


# 全域資料庫管理實例
db_manager = DatabaseManager()
