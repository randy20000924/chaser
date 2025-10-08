# 快速開始指南

## 1. 環境準備

### 安裝PostgreSQL
```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows
# 下載並安裝PostgreSQL: https://www.postgresql.org/download/windows/
```

### 建立資料庫
```sql
-- 連接到PostgreSQL
psql -U postgres

-- 建立資料庫和使用者
CREATE DATABASE ptt_stock_crawler;
CREATE USER ptt_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ptt_stock_crawler TO ptt_user;
\q
```

## 2. 安裝和設定

### 方法一：使用安裝腳本（推薦）
```bash
# 執行安裝腳本
./install.sh

# 編輯環境變數
nano .env
```

### 方法二：手動安裝
```bash
# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 複製環境變數檔案
cp env.example .env

# 編輯環境變數
nano .env
```

### 設定環境變數
編輯 `.env` 檔案：
```env
DATABASE_URL=postgresql+psycopg://ptt_user:ptt_password@localhost:5432/ptt_stock_crawler
TARGET_AUTHORS=["mrp"]
CRAWL_INTERVAL=300
ENABLE_SELENIUM=false
HTTP_PROXY_URL=
RANDOM_USER_AGENT=true
```

## 3. 初始化資料庫

```bash
python init_db.py
```

## 4. 測試系統

```bash
# 執行測試
python test_crawler.py
```

## 5. 啟動服務

### 選項1：只執行爬蟲
```bash
python main.py --mode crawler
```

### 選項2：只執行MCP服務器
```bash
python main.py --mode mcp
```

### 選項3：同時執行兩者
```bash
python main.py --mode both
```

### 選項4：執行一次爬蟲（測試用）
```bash
python main.py --mode once
```

### 選項5：定時執行（每天台灣時區早上8點）
```bash
python main.py --mode scheduled
```

## 6. 使用Docker（可選）

```bash
# 使用Docker Compose
docker-compose up -d

# 查看日誌
docker-compose logs -f crawler

# 停止服務
docker-compose down
```

## 7. 測試MCP連接

```bash
# 測試MCP客戶端
python test_mcp_client.py
```

## 8. 監控和日誌

### 查看日誌
```bash
# 即時日誌
tail -f logs/crawler.log

# 錯誤日誌
grep ERROR logs/crawler.log
```

### 資料庫查詢
```sql
-- 連接到資料庫
psql -U ptt_user -d ptt_stock_crawler

-- 查看文章數量
SELECT COUNT(*) FROM ptt_articles;

-- 查看作者統計
SELECT author, COUNT(*) as article_count 
FROM ptt_articles 
GROUP BY author 
ORDER BY article_count DESC;

-- 查看最近文章
SELECT title, author, publish_time 
FROM ptt_articles 
ORDER BY publish_time DESC 
LIMIT 10;
```

## 9. 常見問題

### Q: 爬蟲被PTT阻擋怎麼辦？
A: 
- 增加 `CRAWL_INTERVAL` 設定值
- 啟用 `RANDOM_USER_AGENT=true`
- 啟用 `ENABLE_SELENIUM=true` 使用Selenium後備
- 設定 `HTTP_PROXY_URL` 使用代理伺服器

### Q: 資料庫連線失敗？
A: 
- 確認PostgreSQL服務正在運行
- 檢查 `DATABASE_URL` 設定
- 確認資料庫使用者權限

### Q: MCP服務器無法啟動？
A: 
- 檢查端口8000是否被占用
- 確認MCP依賴已正確安裝
- 查看日誌檔案中的錯誤訊息

## 10. 下一步

- 閱讀完整的 [README.md](README.md) 了解詳細功能
- 修改 `config.py` 自定義設定
- 在 `data_processor.py` 中整合實際的LLM API
- 添加更多作者到追蹤列表

## 支援

如有問題，請查看：
1. 日誌檔案：`logs/crawler.log`
2. 完整文檔：`README.md`
3. 測試腳本：`test_crawler.py`
