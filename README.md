# Chaser: PTT股票版作者爬蟲分析

一個功能完整的PTT股票版爬蟲系統，支援多作者追蹤、MCP整合、LLM分析、前端展示。

## 功能特色

- 🕷️ **智能爬蟲**: 處理PTT防爬機制和年齡限制，支援內容過濾
- 👥 **多作者追蹤**: 支援追蹤多個指定作者的文章
- 🗄️ **資料庫儲存**: 使用PostgreSQL儲存結構化資料和分析結果
- 🔍 **MCP整合**: 提供HTTP MCP Server供LLM查詢和分析
- 🤖 **LLM分析**: 支援Ollama本地LLM和規則式分析，股票推薦和原因分析
- ⚡ **異步處理**: 高效能的異步爬蟲架構
- ⏰ **定時執行**: 支援每天台灣時區下午3點自動執行
- 🛡️ **防爬機制**: 隨機UA、指數退避、Selenium後備、代理支援
- 🌐 **前端展示**: Next.js前端，支援作者搜尋和文章分析結果展示

## 系統架構

```
PTT爬蟲 → 內容過濾 → 批量分析 → PostgreSQL → HTTP MCP Server → Next.js前端
    ↓
Ollama LLM / 規則式分析 → 股票推薦 → 原因分析 → 資料庫儲存
```

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `env.example` 為 `.env` 並修改設定：

```bash
cp env.example .env
```

主要設定項目：
- `DATABASE_URL`: PostgreSQL連線字串
- `TARGET_AUTHORS`: 追蹤的作者列表（逗號分隔）
- `CRAWL_INTERVAL`: 爬蟲間隔時間（秒）

### 3. 初始化資料庫

```bash
python -c "from database import db_manager; db_manager.create_tables()"
```

### 4. 執行模式

```bash
# 定時執行（每天台灣時區下午3點）
python main.py --mode scheduled

# 執行一次爬蟲（測試用）
python main.py --mode once

# 常駐爬蟲（每5分鐘檢查）
python main.py --mode crawler

# 執行HTTP MCP服務器
python main.py --mode mcp

# 同時執行爬蟲和MCP
python main.py --mode both
```

### 5. 前端啟動

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# 啟動開發服務器
npm run dev

# 訪問 http://localhost:3000
```

### 6. 定時執行設定

系統支援每天台灣時區下午3點自動執行爬蟲：

```bash
# 啟動定時執行
python main.py --mode scheduled

# 背景執行
nohup python main.py --mode scheduled &

# 查看日誌
tail -f logs/crawler.log
```

## 使用方式

### 基本爬蟲

```python
from ptt_crawler import PTTCrawler

async def crawl_articles():
    async with PTTCrawler() as crawler:
        articles = await crawler.crawl_all_authors()
        print(f"找到 {len(articles)} 篇文章")
```

### HTTP MCP查詢

HTTP MCP Server提供以下API端點：

- `POST /tools/analyze_article`: 分析單篇文章
- `POST /tools/get_author_articles`: 取得作者文章列表（含分析結果）
- `POST /tools/process_articles`: 批量處理未分析的文章
- `GET /tools/analysis_stats`: 取得分析統計資料
- `GET /health`: 健康檢查

### 前端使用

1. 在搜尋框輸入PTT作者名稱
2. 查看該作者的文章列表
3. 直接查看每篇文章的股票推薦和分析原因
4. 高推文數文章會顯示紅色"爆"字

### 資料庫查詢

```python
from database import db_manager
from models import PTTArticle

with db_manager.get_session() as session:
    # 查詢特定作者的文章
    articles = session.query(PTTArticle).filter(
        PTTArticle.author == "mrp"
    ).all()
```

## 配置說明

### 環境變數

| 變數名 | 說明 | 預設值 |
|--------|------|--------|
| `DATABASE_URL` | 資料庫連線字串 | `postgresql+psycopg://...` |
| `TARGET_AUTHORS` | 追蹤作者列表 | `["mrp"]` |
| `CRAWL_INTERVAL` | 爬蟲間隔（秒） | `300` |
| `MAX_ARTICLES_PER_CRAWL` | 每次爬取最大文章數 | `50` |
| `ENABLE_SELENIUM` | 啟用Selenium後備 | `false` |
| `HTTP_PROXY_URL` | HTTP代理URL | 無 |
| `RANDOM_USER_AGENT` | 隨機User-Agent | `true` |
| `LOG_LEVEL` | 日誌級別 | `INFO` |
| `ENABLE_OLLAMA` | 啟用Ollama LLM分析 | `false` |
| `OLLAMA_BASE_URL` | Ollama服務地址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama模型名稱 | `qwen2.5:0.5b` |
| `MCP_SERVER_URL` | MCP服務器地址 | `http://localhost:8000` |

### 資料庫結構

- `ptt_articles`: 文章資料表（含分析結果欄位）
- `author_profiles`: 作者檔案表
- `crawl_logs`: 爬蟲執行日誌表

## 開發指南

### 專案結構

```
chaser/
├── main.py                    # 主應用程式
├── config.py                  # 配置管理
├── models.py                  # 資料庫模型
├── database.py                # 資料庫連線
├── ptt_crawler.py             # PTT爬蟲模組
├── data_processor.py          # 資料處理器
├── article_analyzer.py        # 文章分析模組（含Ollama整合）
├── http_mcp_server.py         # HTTP MCP Server
├── frontend/                  # Next.js前端應用
│   ├── src/app/              # 前端頁面和API
│   ├── package.json          # 前端依賴
│   └── next.config.ts        # Next.js配置
├── QUICKSTART.md              # 快速開始指南
├── requirements.txt           # 依賴清單
├── docker-compose.yml         # Docker Compose配置
├── Dockerfile                 # Docker配置
└── README.md                  # 說明文檔
```

### 添加新功能

1. **新增作者追蹤**: 修改 `config.py` 中的 `target_authors`
2. **自定義分析**: 修改 `article_analyzer.py` 中的分析方法
3. **新增API端點**: 修改 `http_mcp_server.py` 中的路由
4. **前端功能**: 修改 `frontend/src/app/` 中的頁面和API
5. **Ollama模型**: 修改 `config.py` 中的 `OLLAMA_MODEL` 設定


## 故障排除

### 常見問題

1. **資料庫連線失敗**
   - 檢查PostgreSQL服務是否運行
   - 確認 `DATABASE_URL` 設定正確

2. **爬蟲被阻擋**
   - 增加請求間隔時間
   - 檢查User-Agent設定
   - 考慮使用代理伺服器

3. **MCP Server無法啟動**
   - 檢查端口是否被占用
   - 確認MCP依賴已正確安裝

### 日誌查看

日誌檔案位置：`logs/crawler.log`

```bash
# 查看即時日誌
tail -f logs/crawler.log

# 查看錯誤日誌
grep ERROR logs/crawler.log
```

## 授權

MIT License

## 貢獻

歡迎提交Issue和Pull Request！

## 更新日誌

### v2.0.0
- 新增Next.js前端展示介面
- 整合Ollama本地LLM分析
- 實現批量文章預分析流程
- 新增HTTP MCP Server替代stdio版本
- 優化文章內容過濾（排除回文）
- 調整定時執行時間為下午3點
- 新增分析結果資料庫儲存
- 清理專案結構，移除不必要檔案

### v1.2.0
- 新增文章分析模組（股票推薦、情感分析）
- 新增互動式文章選擇器
- 新增快速查詢工具
- 優化專案結構，移除不必要檔案

### v1.1.0
- 新增定時執行功能（每天台灣時區早上8點）
- 強化防爬機制（隨機UA、指數退避、Selenium後備）
- 支援HTTP代理
- 優化資料庫去重機制
- 更新依賴套件版本

### v1.0.0
- 初始版本發布
- 支援基本爬蟲功能
- 整合MCP Server
- 支援PostgreSQL資料庫
