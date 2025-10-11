#!/bin/bash

# Chaser Backend Deployment Script
# 後端部署腳本

set -e

echo "🚀 Starting Chaser Backend Deployment..."

# 檢查是否在正確的目錄
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 創建後端目錄結構
echo "📁 Creating backend directory structure..."
mkdir -p backend/{logs,venv}

# 複製後端文件到backend目錄
echo "📋 Copying backend files..."
cp main.py backend/
cp config.py backend/
cp database.py backend/
cp models.py backend/
cp ptt_crawler.py backend/
cp data_processor.py backend/
cp article_analyzer.py backend/
cp http_mcp_server.py backend/
cp requirements.txt backend/
cp env.example backend/
cp install.sh backend/

# 創建後端專用的Dockerfile
echo "🐳 Creating backend Dockerfile..."
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements並安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . .

# 創建日誌目錄
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "http_mcp_server.py"]
EOF

# 創建後端docker-compose.yml
echo "🐳 Creating backend docker-compose.yml..."
cat > backend/docker-compose.yml << 'EOF'
version: '3.8'

services:
  chaser-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL:-postgresql+psycopg://ptt_user:ptt_password@db:5432/ptt_stock_crawler}
      - TARGET_AUTHORS=${TARGET_AUTHORS:-mrp}
      - CRAWL_INTERVAL=${CRAWL_INTERVAL:-300}
      - ENABLE_OLLAMA=${ENABLE_OLLAMA:-false}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5:0.5b}
      - MCP_SERVER_HOST=${MCP_SERVER_HOST:-0.0.0.0}
      - MCP_SERVER_PORT=${MCP_SERVER_PORT:-8000}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ptt_stock_crawler
      - POSTGRES_USER=ptt_user
      - POSTGRES_PASSWORD=ptt_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# 創建後端部署說明
echo "📝 Creating backend deployment guide..."
cat > backend/DEPLOYMENT.md << 'EOF'
# Chaser Backend Deployment Guide

## 快速部署

### 1. 環境準備
```bash
# 確保Docker和Docker Compose已安裝
docker --version
docker-compose --version
```

### 2. 配置環境變數
```bash
# 複製環境變數範例
cp env.example .env

# 編輯環境變數
nano .env
```

### 3. 啟動服務
```bash
# 構建並啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 4. 初始化資料庫
```bash
# 進入容器執行資料庫初始化
docker-compose exec chaser-backend python -c "from database import db_manager; db_manager.create_tables()"
```

## 服務端口
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432

## 健康檢查
```bash
# 檢查API狀態
curl http://localhost:8000/

# 檢查資料庫連線
docker-compose exec chaser-backend python -c "from database import db_manager; print('DB OK' if db_manager.health_check() else 'DB Error')"
```
EOF

echo "✅ Backend deployment files created successfully!"
echo "📁 Backend files are in: ./backend/"
echo "🚀 To deploy: cd backend && docker-compose up -d"
