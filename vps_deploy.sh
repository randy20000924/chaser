#!/bin/bash

# PTT Stock Crawler VPS 部署腳本
# 適用於 Ubuntu/Debian 系統

set -e  # 遇到錯誤立即退出

echo "🚀 開始部署 PTT Stock Crawler 到 VPS..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
REPO_URL="https://github.com/randy20000924/chaser.git"
DEPLOY_DIR="/var/www/chaser"
SERVICE_USER="www-data"
BACKEND_PORT=8000
FRONTEND_PORT=3000
NGINX_SITE="chaser"

# 檢查是否為 root 用戶
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}請使用 sudo 執行此腳本${NC}"
    exit 1
fi

echo -e "${BLUE}📋 部署配置:${NC}"
echo "  倉庫: $REPO_URL"
echo "  部署目錄: $DEPLOY_DIR"
echo "  後端端口: $BACKEND_PORT"
echo "  前端端口: $FRONTEND_PORT"
echo ""

# 更新系統套件
echo -e "${YELLOW}📦 更新系統套件...${NC}"
apt update && apt upgrade -y

# 安裝必要套件
echo -e "${YELLOW}🔧 安裝必要套件...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    unzip \
    supervisor \
    certbot \
    python3-certbot-nginx

# 安裝 PM2
echo -e "${YELLOW}📦 安裝 PM2...${NC}"
npm install -g pm2

# 創建部署目錄
echo -e "${YELLOW}📁 創建部署目錄...${NC}"
mkdir -p $DEPLOY_DIR
chown $SERVICE_USER:$SERVICE_USER $DEPLOY_DIR

# 克隆專案
echo -e "${YELLOW}📥 克隆專案...${NC}"
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "專案已存在，更新中..."
    cd $DEPLOY_DIR
    sudo -u $SERVICE_USER git pull origin main
else
    cd $DEPLOY_DIR
    sudo -u $SERVICE_USER git clone $REPO_URL .
fi

# 設置 Python 虛擬環境
echo -e "${YELLOW}🐍 設置 Python 環境...${NC}"
cd $DEPLOY_DIR
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt

# 設置 Node.js 環境
echo -e "${YELLOW}📦 設置 Node.js 環境...${NC}"
cd $DEPLOY_DIR/frontend
sudo -u $SERVICE_USER npm install

# 配置 PostgreSQL
echo -e "${YELLOW}🗄️ 配置 PostgreSQL...${NC}"
systemctl start postgresql
systemctl enable postgresql

# 創建資料庫和用戶
sudo -u postgres psql -c "CREATE DATABASE chaser_db;" || echo "資料庫可能已存在"
sudo -u postgres psql -c "CREATE USER chaser_user WITH PASSWORD 'chaser_password';" || echo "用戶可能已存在"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chaser_db TO chaser_user;"
sudo -u postgres psql -c "ALTER USER chaser_user CREATEDB;"

# 創建環境變數檔案
echo -e "${YELLOW}⚙️ 創建環境變數檔案...${NC}"
cat > $DEPLOY_DIR/.env << EOF
# 資料庫配置
DATABASE_URL=postgresql://chaser_user:chaser_password@localhost:5432/chaser_db

# PTT 配置
PTT_BASE_URL=https://www.ptt.cc
PTT_STOCK_BOARD=Stock
PTT_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# 目標作者
TARGET_AUTHORS=["mrp", "testuser"]

# 爬蟲配置
CRAWL_INTERVAL=3600
MAX_ARTICLES_PER_CRAWL=50
SEARCH_DAYS=3

# MCP 服務器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/chaser/crawler.log

# 請求配置
REQUEST_MIN_DELAY_MS=1000
REQUEST_MAX_DELAY_MS=3000
BACKOFF_MAX_SLEEP_SECONDS=60
ENABLE_SELENIUM=false
HTTP_PROXY_URL=

# 用戶代理池
USER_AGENTS=["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"]
EOF

# 創建日誌目錄
mkdir -p /var/log/chaser
chown $SERVICE_USER:$SERVICE_USER /var/log/chaser

# 初始化資料庫
echo -e "${YELLOW}🗄️ 初始化資料庫...${NC}"
cd $DEPLOY_DIR
sudo -u $SERVICE_USER ./venv/bin/python -c "
from database import db_manager
db_manager.create_tables()
print('資料庫表創建完成')
"

# 配置 Nginx
echo -e "${YELLOW}🌐 配置 Nginx...${NC}"
cat > /etc/nginx/sites-available/$NGINX_SITE << EOF
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://localhost:$FRONTEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 啟用 Nginx 配置
ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# 創建 PM2 配置文件
echo -e "${YELLOW}⚙️ 創建 PM2 配置...${NC}"
cat > $DEPLOY_DIR/ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'chaser-backend',
      script: './venv/bin/python',
      args: 'main.py --mode both',
      cwd: '$DEPLOY_DIR',
      user: '$SERVICE_USER',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/chaser/backend-error.log',
      out_file: '/var/log/chaser/backend-out.log',
      log_file: '/var/log/chaser/backend-combined.log',
      time: true
    },
    {
      name: 'chaser-frontend',
      script: 'npm',
      args: 'start',
      cwd: '$DEPLOY_DIR/frontend',
      user: '$SERVICE_USER',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        NEXT_PUBLIC_MCP_SERVER_URL: 'http://localhost:$BACKEND_PORT'
      },
      error_file: '/var/log/chaser/frontend-error.log',
      out_file: '/var/log/chaser/frontend-out.log',
      log_file: '/var/log/chaser/frontend-combined.log',
      time: true
    }
  ]
};
EOF

# 設置自動同步腳本
echo -e "${YELLOW}🔄 設置自動同步...${NC}"
cat > $DEPLOY_DIR/auto_sync.sh << 'EOF'
#!/bin/bash
cd /var/www/chaser
git pull origin main
pm2 restart all
EOF

chmod +x $DEPLOY_DIR/auto_sync.sh

# 設置 crontab 自動同步
echo "*/5 * * * * /var/www/chaser/auto_sync.sh" | crontab -u $SERVICE_USER -

# 啟動服務
echo -e "${YELLOW}🚀 啟動服務...${NC}"
cd $DEPLOY_DIR
sudo -u $SERVICE_USER pm2 start ecosystem.config.js
sudo -u $SERVICE_USER pm2 save
sudo -u $SERVICE_USER pm2 startup

# 設置防火牆
echo -e "${YELLOW}🔥 配置防火牆...${NC}"
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${BLUE}📋 服務狀態:${NC}"
echo "  後端: pm2 status chaser-backend"
echo "  前端: pm2 status chaser-frontend"
echo "  日誌: pm2 logs"
echo ""
echo -e "${BLUE}🌐 訪問地址:${NC}"
echo "  http://your-vps-ip"
echo ""
echo -e "${BLUE}🔧 管理命令:${NC}"
echo "  重啟服務: pm2 restart all"
echo "  查看日誌: pm2 logs"
echo "  停止服務: pm2 stop all"
echo "  手動同步: /var/www/chaser/auto_sync.sh"
echo ""
echo -e "${YELLOW}⚠️ 注意事項:${NC}"
echo "  1. 請確保 VPS 有足夠的記憶體運行 Ollama"
echo "  2. 首次運行需要下載 Qwen2.5:0.5b 模型"
echo "  3. 建議設置 SSL 證書: certbot --nginx"
echo "  4. 檢查防火牆設置確保端口開放"
