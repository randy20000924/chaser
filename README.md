# PTT股票版爬蟲系統

一個功能完整的PTT股票版爬蟲系統，支援多作者追蹤、MCP整合、LLM分析和自動同步部署。

## 功能特色

- 🕷️ **智能爬蟲**: 處理PTT防爬機制和年齡限制
- 👥 **多作者追蹤**: 支援追蹤多個指定作者的文章
- 🗄️ **資料庫儲存**: 使用PostgreSQL儲存結構化資料
- 🔍 **MCP整合**: 提供MCP Server供LLM查詢和分析
- 🤖 **LLM分析**: 支援文章分類、情感分析、股票推薦等AI功能
- ⚡ **異步處理**: 高效能的異步爬蟲架構
- ⏰ **定時執行**: 支援每天台灣時區早上8點自動執行
- 🛡️ **防爬機制**: 隨機UA、指數退避、Selenium後備、代理支援
- 🔄 **自動同步**: 本地修改自動同步到VPS部署
- 🌐 **VPS部署**: 支援Docker容器化部署

## 系統架構

```
本地開發 → GitHub → VPS自動同步 → Docker部署
    ↓
PTT爬蟲 → 資料處理 → PostgreSQL → MCP Server → LLM Agent
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
# 定時執行（每天台灣時區早上8點）
python main.py --mode scheduled

# 執行一次爬蟲（測試用）
python main.py --mode once

# 常駐爬蟲（每5分鐘檢查）
python main.py --mode crawler

# 執行MCP服務器
python main.py --mode mcp

# 同時執行爬蟲和MCP
python main.py --mode both
```

### 5. 定時執行設定

系統支援每天台灣時區早上8點自動執行爬蟲：

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

### MCP查詢

MCP Server提供以下工具：

- `search_articles`: 搜尋文章（按作者、股票代碼、時間）
- `get_article_content`: 取得文章完整內容
- `analyze_author_activity`: 分析作者活動模式
- `get_stock_mentions`: 取得股票提及統計
- `classify_article`: 分類文章內容

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

### 資料庫結構

- `ptt_articles`: 文章資料表
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
├── data_processor.py          # 資料處理和LLM整合
├── simple_mcp_server.py       # MCP Server
├── article_analyzer.py        # 文章分析模組
├── article_selector.py        # 文章選擇器
├── quick_query.py             # 快速查詢工具
├── view_output.py             # 輸出查看工具
├── sync.sh                    # 本地同步腳本
├── quick_sync.sh              # 快速同步腳本
├── vps_sync.sh                # VPS同步腳本
├── setup_vps_auto_sync.sh     # VPS自動同步設定
├── SYNC_GUIDE.md              # 同步使用指南
├── QUICKSTART.md              # 快速開始指南
├── requirements.txt           # 依賴清單
├── docker-compose.yml         # Docker Compose配置
├── Dockerfile                 # Docker配置
└── README.md                  # 說明文檔
```

### 添加新功能

1. **新增作者追蹤**: 修改 `config.py` 中的 `target_authors`
2. **自定義分類**: 修改 `data_processor.py` 中的 `LLMClassifier`
3. **新增查詢工具**: 修改 `simple_mcp_server.py` 中的工具列表
4. **新增分析功能**: 修改 `article_analyzer.py` 中的分析方法

### 自動同步部署

系統支援本地開發自動同步到VPS：

```bash
# 本地修改後同步
./sync.sh

# 快速同步（緊急更新）
./quick_sync.sh
```

VPS會每2分鐘自動檢查GitHub更新並同步。

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

### v1.2.0
- 新增自動同步部署功能
- 新增文章分析模組（股票推薦、情感分析）
- 新增互動式文章選擇器
- 新增快速查詢工具
- 優化專案結構，移除不必要檔案
- 新增VPS部署支援

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
