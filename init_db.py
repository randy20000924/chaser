"""初始化資料庫腳本."""

import asyncio
import sys
from loguru import logger

# 添加專案根目錄到Python路徑
sys.path.append('.')

from database import db_manager
from models import Base


async def init_database():
    """初始化資料庫."""
    logger.info("開始初始化資料庫...")
    
    try:
        # 檢查資料庫連線
        if not await db_manager.health_check():
            logger.error("無法連接到資料庫，請檢查設定")
            return False
        
        # 建立所有資料表
        db_manager.create_tables()
        logger.info("資料表建立完成")
        
        # 顯示資料表資訊
        logger.info("已建立的資料表:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")
        
        logger.info("資料庫初始化完成！")
        return True
        
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(init_database())
