#!/bin/bash

# Chaser Full Stack Deployment Script
# 全棧部署腳本

set -e

echo "🚀 Starting Chaser Full Stack Deployment..."

# 檢查是否在正確的目錄
if [ ! -f "main.py" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 創建部署目錄結構
echo "📁 Creating deployment structure..."
mkdir -p backend logs

# 執行後端部署
echo "🔧 Deploying backend..."
chmod +x backend/deploy.sh
./backend/deploy.sh

# 執行前端部署
echo "🔧 Deploying frontend..."
chmod +x frontend/deploy.sh
cd frontend
./deploy.sh
cd ..

# 創建根目錄的docker-compose.yml
echo "🐳 Creating root docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # 前端服務
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - MCP_SERVER_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  # 後端服務
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+psycopg://ptt_user:ptt_password@db:5432/ptt_stock_crawler
      - TARGET_AUTHORS=${TARGET_AUTHORS:-mrp}
      - CRAWL_INTERVAL=${CRAWL_INTERVAL:-300}
      - ENABLE_OLLAMA=${ENABLE_OLLAMA:-false}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5:0.5b}
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
    restart: unless-stopped

  # 資料庫服務
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

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# 創建Nginx配置
echo "🌐 Creating Nginx configuration..."
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }
    
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端路由
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 後端API路由
        location /api/ {
            proxy_pass http://backend/tools/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 直接後端API路由
        location /tools/ {
            proxy_pass http://backend/tools/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# 創建環境變數範例
echo "📝 Creating environment configuration..."
cat > .env.example << 'EOF'
# 資料庫配置
DATABASE_URL=postgresql+psycopg://ptt_user:ptt_password@localhost:5432/ptt_stock_crawler

# 目標作者
TARGET_AUTHORS=mrp

# 爬蟲配置
CRAWL_INTERVAL=300
ENABLE_SELENIUM=false
HTTP_PROXY_URL=
RANDOM_USER_AGENT=true

# 日誌配置
LOG_LEVEL=INFO

# Ollama配置
ENABLE_OLLAMA=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

# MCP服務器配置
MCP_SERVER_URL=http://localhost:8000

# 定時任務配置
SCHEDULED_TIME=15:00
TIMEZONE=Asia/Taipei
EOF

# 創建VPS部署指南
echo "📝 Creating VPS deployment guide..."
cat > VPS_DEPLOYMENT.md << 'EOF'
# VPS部署指南

## 1. VPS環境準備

### 創建chaser用戶
```bash
# 創建chaser用戶
sudo adduser chaser
sudo usermod -aG sudo chaser
sudo usermod -aG docker chaser

# 切換到chaser用戶
su - chaser
```

### 安裝必要軟體
```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安裝Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新載入用戶組
newgrp docker
```

## 2. 部署應用

### 克隆代碼
```bash
# 在/home/chaser目錄下
cd /home/chaser
git clone https://github.com/randy20000924/Chaser.git
cd Chaser
```

### 配置環境變數
```bash
# 複製環境變數範例
cp .env.example .env

# 編輯環境變數
nano .env
```

### 啟動服務
```bash
# 構建並啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 初始化資料庫
docker-compose exec backend python -c "from database import db_manager; db_manager.create_tables()"
```

## 3. 服務管理

### 常用命令
```bash
# 啟動服務
docker-compose up -d

# 停止服務
docker-compose down

# 重啟服務
docker-compose restart

# 查看狀態
docker-compose ps

# 查看日誌
docker-compose logs -f [service_name]

# 更新代碼
git pull
docker-compose down
docker-compose up -d --build
```

### 服務端口
- **前端**: http://your-vps-ip:3000
- **後端API**: http://your-vps-ip:8000
- **Nginx**: http://your-vps-ip:80
- **PostgreSQL**: your-vps-ip:5432

## 4. 自動更新（可選）

### 創建更新腳本
```bash
cat > update.sh << 'SCRIPTEOF'
#!/bin/bash
cd /home/chaser/Chaser
git pull
docker-compose down
docker-compose up -d --build
echo "Update completed at $(date)"
SCRIPTEOF

chmod +x update.sh
```

### 設置定時更新
```bash
# 編輯crontab
crontab -e

# 添加定時任務（每天凌晨2點更新）
0 2 * * * /home/chaser/Chaser/update.sh >> /home/chaser/update.log 2>&1
```
EOF

# 設置執行權限
chmod +x deploy.sh
chmod +x backend/deploy.sh
chmod +x frontend/deploy.sh

echo "✅ Full stack deployment setup completed!"
echo ""
echo "📁 Directory structure:"
echo "├── backend/          # 後端服務"
echo "├── frontend/         # 前端服務"
echo "├── logs/            # 日誌文件"
echo "├── docker-compose.yml # 全棧部署配置"
echo "├── nginx.conf       # Nginx配置"
echo "└── VPS_DEPLOYMENT.md # VPS部署指南"
echo ""
echo "🚀 To deploy locally:"
echo "   ./deploy.sh"
echo "   docker-compose up -d"
echo ""
echo "🌐 To deploy on VPS:"
echo "   1. Follow VPS_DEPLOYMENT.md"
echo "   2. Clone repo to /home/chaser/Chaser"
echo "   3. Run: docker-compose up -d"
