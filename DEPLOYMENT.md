# PTT股票爬蟲系統 - 部署指南

## 📁 專案結構

```
chaser/
├── backend/                    # 後端服務
│   └── deploy.sh              # 後端部署腳本
├── frontend/                   # 前端服務
│   └── deploy.sh              # 前端部署腳本
├── .github/workflows/         # GitHub Actions
│   └── deploy.yml             # 自動部署工作流程
├── deploy.sh                  # 全棧部署腳本
├── vps-setup.sh              # VPS初始化腳本
├── docker-compose.yml         # Docker配置
├── Dockerfile                 # 後端Docker配置
└── env.example               # 環境變數範例
```

## 🚀 部署方式

### 方式一：本地部署（開發環境）

#### 1. 後端部署
```bash
# 進入後端目錄
cd backend

# 給腳本執行權限
chmod +x deploy.sh

# 部署後端（開發模式）
./deploy.sh dev

# 部署後端（生產模式）
./deploy.sh prod
```

#### 2. 前端部署
```bash
# 進入前端目錄
cd frontend

# 給腳本執行權限
chmod +x deploy.sh

# 部署前端（開發模式）
./deploy.sh dev

# 部署前端（生產模式）
./deploy.sh prod
```

#### 3. 全棧部署
```bash
# 在根目錄執行
chmod +x deploy.sh

# 部署所有服務
./deploy.sh all

# 清理部署（清理Docker鏡像）
./deploy.sh all --clean
```

### 方式二：VPS部署（生產環境）

#### 1. VPS初始化
```bash
# 在VPS上執行初始化腳本
chmod +x vps-setup.sh
./vps-setup.sh
```

#### 2. 手動部署
```bash
# 克隆代碼
git clone https://github.com/你的用戶名/chaser.git /var/www/chaser

# 進入專案目錄
cd /var/www/chaser

# 給腳本執行權限
chmod +x deploy.sh
chmod +x backend/deploy.sh
chmod +x frontend/deploy.sh

# 部署所有服務
./deploy.sh all
```

#### 3. 自動部署（GitHub Actions）

1. **設置GitHub Secrets**：
   - `VPS_HOST`: 你的VPS IP地址
   - `VPS_USERNAME`: 你的VPS用戶名
   - `VPS_SSH_KEY`: 你的SSH私鑰

2. **推送代碼觸發部署**：
   ```bash
   git add .
   git commit -m "部署更新"
   git push origin main
   ```

## 🔧 端口配置

### 默認端口
- **前端**: 3000 (Next.js)
- **後端API**: 8000 (FastAPI)
- **PostgreSQL**: 5432
- **Nginx**: 80 (HTTP), 443 (HTTPS)

### 端口衝突解決
如果端口被占用，可以修改以下文件：

1. **修改後端端口** (`docker-compose.yml`):
   ```yaml
   ports:
     - "8001:8000"  # 改為8001
   ```

2. **修改前端端口** (`frontend/package.json`):
   ```json
   {
     "scripts": {
       "dev": "next dev -p 3001",
       "start": "next start -p 3001"
     }
   }
   ```

3. **修改Nginx配置** (`/etc/nginx/sites-available/chaser`):
   ```nginx
   server {
       listen 80;
       location / {
           proxy_pass http://localhost:3001;  # 對應前端端口
       }
       location /api/ {
           proxy_pass http://localhost:8001/;  # 對應後端端口
       }
   }
   ```

## 📋 環境變數配置

### 後端環境變數 (`.env`)
```env
# 資料庫配置
DATABASE_URL=postgresql+psycopg://ptt_user:ptt_password@localhost:5432/ptt_stock_crawler

# PTT配置
TARGET_AUTHORS=mrp,author2,author3

# 爬蟲配置
CRAWL_INTERVAL=300
ENABLE_SELENIUM=false

# LLM配置
ENABLE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:0.5b

# MCP服務器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### 前端環境變數 (`.env.local`)
```env
# 前端配置
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=PTT股票爬蟲分析
```

## 🔍 故障排除

### 常見問題

1. **端口被占用**
   ```bash
   # 查看端口使用情況
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000
   
   # 殺死占用端口的進程
   sudo kill -9 <PID>
   ```

2. **Docker服務啟動失敗**
   ```bash
   # 查看Docker日誌
   docker-compose logs crawler
   
   # 重啟Docker服務
   docker-compose down
   docker-compose up -d
   ```

3. **資料庫連線失敗**
   ```bash
   # 檢查PostgreSQL狀態
   docker-compose ps postgres
   
   # 重啟資料庫
   docker-compose restart postgres
   ```

4. **前端構建失敗**
   ```bash
   # 清理node_modules
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### 日誌查看

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f crawler
docker-compose logs -f postgres

# 查看應用日誌
tail -f logs/crawler.log
```

## 📊 監控和維護

### 服務狀態檢查
```bash
# 檢查所有服務狀態
docker-compose ps

# 檢查端口監聽
netstat -tulpn | grep -E ":(3000|8000|5432)"

# 檢查系統資源
htop
df -h
```

### 定期維護
```bash
# 清理Docker系統
docker system prune -f

# 更新系統包
apt update && apt upgrade -y

# 重啟服務
docker-compose restart
```

## 🔐 安全建議

1. **更改默認密碼**：修改PostgreSQL和系統密碼
2. **配置防火牆**：只開放必要端口
3. **使用HTTPS**：配置SSL證書
4. **定期備份**：備份資料庫和重要文件
5. **監控日誌**：定期檢查系統和應用日誌

## 📞 支援

如有問題，請查看：
1. 日誌文件：`logs/crawler.log`
2. Docker日誌：`docker-compose logs`
3. 系統日誌：`journalctl -u docker`
4. 專案文檔：`README.md`
