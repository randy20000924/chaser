# Chaser: PTT股票版爬蟲與分析系統

一個功能完整的PTT股票版爬蟲與分析系統，支援多作者追蹤、LLM分析、股票推薦、Web前端展示和完整的MCP (Model Context Protocol) 協議支援。

> 🚀 **本專案使用 [Cursor](https://cursor.sh/) AI 程式碼編輯器協助製作** - 透過 AI 助手加速開發流程，實現智能程式碼生成和自動化開發。

## 功能特色

- 🕷️ **智能爬蟲**: 處理PTT防爬機制和年齡限制，支援多作者追蹤
- 🗄️ **資料庫儲存**: 使用PostgreSQL儲存結構化資料
- 🤖 **LLM分析**: 整合Ollama進行文章分析、情感分析、股票推薦
- ⚡ **異步處理**: 高效能的異步爬蟲架構
- ⏰ **定時執行**: 支援每天自動執行爬蟲和分析
- 🛡️ **防爬機制**: 隨機UA、指數退避、請求間隔控制
- 🌐 **Web前端**: Next.js前端展示分析結果
- 🔄 **VPS部署**: 支援PM2進程管理和Nginx反向代理
- 📊 **股票驗證**: 整合FinMind和Alpha Vantage API驗證股票代碼
- 🧠 **MCP協議**: 完整的Model Context Protocol支援，可與AI助手整合
- 🔧 **系統檢測**: 自動檢測硬體配置並推薦適合的Qwen模型
- 🎯 **動態爬蟲**: 支援指定單一作者進行爬蟲分析
- 🔒 **並發控制**: 使用鎖機制防止多個爬蟲任務同時執行，避免系統卡住
- 🌐 **前端自動爬蟲**: 前端搜索時如找不到作者，自動觸發爬蟲和分析

## 系統架構

```
本地開發 → GitHub → VPS部署 → PM2管理
    ↓
PTT爬蟲 → LLM分析 → PostgreSQL → Web前端展示
    ↓
Ollama LLM → 股票驗證 → 分析結果 → Next.js前端
    ↓
MCP協議 → AI助手整合 → 動態分析 → 智能推薦
```

### MCP (Model Context Protocol) 整合

```
Cursor AI助手 → MCP服務器 → 爬蟲分析 → 智能推薦
    ↓
系統硬體檢測 → Qwen模型選擇 → 動態作者爬蟲 → 投資分析
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
# 執行一次爬蟲和分析
python main.py --mode once

# 執行手動爬蟲
python manual_crawler.py

# 執行HTTP API服務器
python main.py --mode mcp

# 執行定時爬蟲
python auto_crawler.py

# 動態指定作者爬蟲
python main.py --mode once --author "homoho"

# 啟動MCP服務器（與AI助手整合）
python mcp_server.py
```

### 5. VPS部署

使用PM2管理進程：

```bash
# 啟動所有服務
pm2 start ecosystem.config.js

# 查看狀態
pm2 status

# 查看日誌
pm2 logs

# 重啟服務
pm2 restart all
```

## 使用方式

### MCP 協議整合（推薦）

在 Cursor 中直接與 AI 助手對話：

```
用戶：「幫我搜尋 homoho 作者的文章並分析他近3個月推薦的標的和推薦買的行業類別，並說明他分析的市場動向」

AI 助手會自動：
1. 調用 MCP 服務器檢查作者資料
2. 如果沒有資料，觸發爬蟲功能
3. 分析作者的推薦標的
4. 統計推薦的行業類別
5. 提供市場動向分析
```

### 基本爬蟲

```python
from ptt_crawler import PTTCrawler

async def crawl_articles():
    async with PTTCrawler() as crawler:
        articles = await crawler.crawl_all_authors()
        print(f"找到 {len(articles)} 篇文章")
```

### 系統硬體檢測

```python
from system_detector import system_detector

# 檢測系統硬體並推薦模型
system_info = system_detector.detect_system()
print(f"推薦模型: {system_info['recommended_model']}")
```

### HTTP API

後端提供以下API端點：

- `GET /health` - 健康檢查
- `GET /articles` - 取得所有文章
- `GET /articles/{article_id}` - 取得特定文章
- `GET /articles/{article_id}/analysis` - 取得文章分析結果
- `GET /authors` - 取得所有作者
- `GET /authors/{author_name}/articles` - 取得特定作者的文章
- `GET /stats` - 取得統計資料
- `POST /api/crawl/author/{author_name}` - 動態爬取指定作者的文章（帶並發控制）
- `GET /api/crawl/status` - 查詢爬蟲運行狀態

#### 動態爬蟲API使用範例

```bash
# 爬取指定作者
curl -X POST http://localhost:8000/api/crawl/author/mrp

# 查詢爬蟲狀態
curl http://localhost:8000/api/crawl/status

# 如果爬蟲正在運行，會返回 409 狀態碼和當前任務信息
```

#### 前端自動爬蟲

前端搜索功能會自動檢查作者是否存在：
- 如果找到作者且有文章 → 直接顯示
- 如果沒找到 → 自動觸發爬蟲API，顯示進度，完成後自動刷新結果

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
├── 核心功能/
│   ├── main.py                    # 主應用程式
│   ├── ptt_crawler.py             # PTT爬蟲模組
│   ├── article_analyzer.py        # LLM文章分析器
│   ├── stock_validator.py         # 股票代碼驗證器
│   ├── crawl_orchestrator.py      # 爬蟲協調器
│   └── system_detector.py         # 系統硬體檢測器
├── 服務/
│   ├── http_mcp_server.py         # HTTP API服務器
│   ├── mcp_server.py              # MCP協議服務器
│   ├── auto_crawler.py            # 自動定時爬蟲
│   └── manual_crawler.py          # 手動爬蟲
├── 配置/
│   ├── config.py                  # 配置管理
│   ├── models.py                  # 資料庫模型
│   ├── database.py                # 資料庫連線
│   └── ecosystem.config.js        # PM2配置
├── 前端/
│   └── frontend/                  # Next.js前端應用
├── 工具/
│   ├── clear_database.py          # 資料庫清理工具
│   └── monitor.sh                 # 系統監控腳本
├── requirements.txt               # Python依賴清單
└── README.md                      # 說明文檔
```

### 添加新功能

1. **新增作者追蹤**: 修改 `config.py` 中的 `TARGET_AUTHORS`
2. **自定義分析**: 修改 `article_analyzer.py` 中的LLM提示詞
3. **新增API端點**: 修改 `http_mcp_server.py` 中的路由
4. **新增前端頁面**: 修改 `frontend/src/app/` 中的頁面組件

### 部署流程

1. **本地開發**: 在本地進行代碼修改和測試
2. **推送到GitHub**: `git add . && git commit -m "message" && git push`
3. **VPS同步**: 在VPS上執行 `git pull` 更新代碼
4. **重啟服務**: `pm2 restart all` 重啟所有服務

## 故障排除

### 常見問題

1. **資料庫連線失敗**
   - 檢查PostgreSQL服務是否運行
   - 確認 `DATABASE_URL` 設定正確

2. **爬蟲被阻擋**
   - 增加請求間隔時間
   - 檢查User-Agent設定
   - 調整 `REQUEST_MIN_DELAY_MS` 和 `REQUEST_MAX_DELAY_MS`

3. **LLM分析失敗**
   - 檢查Ollama服務是否運行
   - 確認模型已下載：`ollama list`
   - 檢查分析超時設定

4. **前端無法顯示資料**
   - 檢查 `NEXT_PUBLIC_BACKEND_URL` 環境變數
   - 確認後端API服務正常運行
   - 檢查CORS設定

### 日誌查看

```bash
# 查看PM2日誌
pm2 logs

# 查看特定服務日誌
pm2 logs chaser-backend
pm2 logs chaser-frontend
pm2 logs chaser-scheduler

# 查看系統監控
./monitor.sh
```

## 授權

MIT License

## 貢獻

歡迎提交Issue和Pull Request！

## 更新日誌

### v3.1.0 (最新)
- 新增動態爬蟲API (`POST /api/crawl/author/{author_name}`)
- 實現並發控制機制，防止多個爬蟲任務同時執行
- 新增爬蟲狀態查詢API (`GET /api/crawl/status`)
- 前端搜索功能增強：找不到作者時自動觸發爬蟲
- 前端添加爬蟲進度顯示和狀態提示
- 優化用戶體驗，支持實時查詢和自動刷新

### v3.0.0
- 實現Model Context Protocol，可與AI助手整合
- 自動檢測CPU、GPU、記憶體、硬碟並推薦適合的Qwen模型
- 支援指定單一作者進行爬蟲，避免一次爬太多人
- 在Cursor中可直接與AI助手對話完成分析
- 自動分析推薦標的、行業類別、市場動向
- 使用Cursor AI程式碼編輯器協助製作

### v2.0.0
- 從MCP架構轉換為HTTP API + Web前端架構
- 整合Ollama進行文章分析、情感分析、股票推薦
- 新增Next.js前端展示分析結果
- 整合FinMind和Alpha Vantage API驗證股票代碼
- 爬蟲時進行LLM分析，避免前端等待
- 支援PM2進程管理和Nginx反向代理
- 移除未使用的檔案和功能

### v1.2.0
- 新增自動同步部署功能
- 新增文章分析模組（股票推薦、情感分析）
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
