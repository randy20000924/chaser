#!/bin/bash

# Chaser VPS部署腳本
# 用於在Namecheap VPS上部署完整的Chaser系統

set -e

echo "🚀 開始部署Chaser到VPS..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
DOMAIN="www.chaser.cloud"
VPS_IP="159.198.37.93"
VPS_USER="root"
PROJECT_DIR="/opt/chaser"
BACKEND_PORT="8000"
FRONTEND_PORT="3000"

echo -e "${BLUE}📋 部署配置:${NC}"
echo "域名: $DOMAIN"
echo "VPS IP: $VPS_IP"
echo "專案目錄: $PROJECT_DIR"
echo "後端端口: $BACKEND_PORT"
echo "前端端口: $FRONTEND_PORT"
echo ""

# 檢查是否在VPS上執行
if [ "$(hostname -I | awk '{print $1}')" != "$VPS_IP" ]; then
    echo -e "${YELLOW}⚠️  請在VPS上執行此腳本${NC}"
    echo "SSH連線: ssh $VPS_USER@$VPS_IP"
    exit 1
fi

echo -e "${GREEN}✅ 在VPS上執行，開始部署...${NC}"

# 1. 更新系統
echo -e "${BLUE}📦 更新系統套件...${NC}"
apt update && apt upgrade -y

# 2. 安裝必要套件（移除 npm，因為 nodejs 會包含）
echo -e "${BLUE}🔧 安裝必要套件...${NC}"
apt install -y curl wget git nginx certbot python3-certbot-nginx \
    postgresql postgresql-contrib python3 python3-pip python3-venv \
    docker.io docker-compose ufw

# 3. 安裝/驗證 Node.js 和 npm
echo -e "${BLUE}📦 檢查並安裝 Node.js...${NC}"

if ! command -v node &> /dev/null; then
    echo "Node.js 未安裝，開始安裝..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
else
    NODE_VERSION=$(node --version)
    echo "Node.js 已安裝: $NODE_VERSION"
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安裝，這不正常！${NC}"
    exit 1
else
    NPM_VERSION=$(npm --version)
    echo "npm 已安裝: $NPM_VERSION"
fi

# 4. 啟動服務
echo -e "${BLUE}🔄 啟動服務...${NC}"
systemctl start postgresql
systemctl enable postgresql
systemctl start docker
systemctl enable docker
systemctl start nginx
systemctl enable nginx

# 5. 配置PostgreSQL
echo -e "${BLUE}🗄️ 配置PostgreSQL...${NC}"

# 檢查資料庫是否已存在
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='chaser_db'")
if [ "$DB_EXISTS" != "1" ]; then
    sudo -u postgres psql -c "CREATE DATABASE chaser_db;"
    echo "資料庫 chaser_db 已創建"
else
    echo "資料庫 chaser_db 已存在"
fi

# 檢查用戶是否已存在
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='chaser_user'")
if [ "$USER_EXISTS" != "1" ]; then
    sudo -u postgres psql -c "CREATE USER chaser_user WITH PASSWORD 'chaser_password_2024';"
    echo "用戶 chaser_user 已創建"
else
    echo "用戶 chaser_user 已存在"
fi

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chaser_db TO chaser_user;"

# 6. 創建專案目錄
echo -e "${BLUE}📁 創建專案目錄...${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 7. 克隆專案
echo -e "${BLUE}📥 克隆/更新專案...${NC}"
if [ -d ".git" ]; then
    echo "更新現有專案..."
    git pull origin main
else
    echo "克隆新專案..."
    git clone https://github.com/randy20000924/chaser.git .
fi

# 8. 設置Python環境
echo -e "${BLUE}🐍 設置Python環境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Python 虛擬環境已創建"
else
    echo "Python 虛擬環境已存在"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 9. 設置環境變數
echo -e "${BLUE}⚙️ 設置環境變數...${NC}"
cat > .env << EOF
DATABASE_URL=postgresql+psycopg://chaser_user:chaser_password_2024@localhost:5432/chaser_db
TARGET_AUTHORS=["mrp","testuser"]
CRAWL_INTERVAL=300
MAX_ARTICLES_PER_CRAWL=50
ENABLE_SELENIUM=false
RANDOM_USER_AGENT=true
LOG_LEVEL=INFO
ENABLE_OLLAMA=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
MCP_SERVER_URL=http://localhost:$BACKEND_PORT
SCHEDULED_TIME=15:00
TIMEZONE=Asia/Taipei
EOF

# 10. 初始化資料庫
echo -e "${BLUE}🗄️ 初始化資料庫...${NC}"
source venv/bin/activate
python -c "from database import db_manager; db_manager.create_tables()" || echo "資料表可能已存在"

# 11. 設置前端
echo -e "${BLUE}🌐 設置前端...${NC}"
cd frontend

# 清除舊的 node_modules（如果需要）
if [ -d "node_modules" ]; then
    echo "清除舊的 node_modules..."
    rm -rf node_modules package-lock.json
fi

npm install
npm run build
cd ..

# 12. 配置Nginx
echo -e "${BLUE}🌐 配置Nginx...${NC}"
cat > /etc/nginx/sites-available/chaser << 'EOF'
server {
    listen 80;
    server_name www.chaser.cloud;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 後端API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 啟用站點
ln -sf /etc/nginx/sites-available/chaser /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 測試 Nginx 配置
if nginx -t; then
    echo "Nginx 配置測試通過"
    systemctl reload nginx
else
    echo -e "${RED}❌ Nginx 配置測試失敗${NC}"
    exit 1
fi

# 13. 設置SSL證書
echo -e "${BLUE}🔒 設置SSL證書...${NC}"
echo "注意：請確保域名 $DOMAIN 已正確指向 $VPS_IP"
read -p "是否繼續設置SSL證書？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || echo "SSL設置失敗，可稍後手動執行"
else
    echo "跳過SSL設置"
fi

# 14. 配置防火牆
echo -e "${BLUE}🔥 配置防火牆...${NC}"
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# 15. 創建系統服務
echo -e "${BLUE}⚙️ 創建系統服務...${NC}"

# 後端服務
cat > /etc/systemd/system/chaser-backend.service << EOF
[Unit]
Description=Chaser Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py --mode both
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 前端服務
cat > /etc/systemd/system/chaser-frontend.service << EOF
[Unit]
Description=Chaser Frontend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/frontend
Environment=NODE_ENV=production
Environment=PORT=$FRONTEND_PORT
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 16. 啟動服務
echo -e "${BLUE}🚀 啟動服務...${NC}"
systemctl daemon-reload
systemctl enable chaser-backend
systemctl enable chaser-frontend
systemctl start chaser-backend
systemctl start chaser-frontend

# 等待服務啟動
sleep 5

# 檢查服務狀態
echo -e "${BLUE}🔍 檢查服務狀態...${NC}"
systemctl is-active --quiet chaser-backend && echo "✅ 後端服務運行中" || echo "❌ 後端服務啟動失敗"
systemctl is-active --quiet chaser-frontend && echo "✅ 前端服務運行中" || echo "❌ 前端服務啟動失敗"

# 17. 設置定時同步
echo -e "${BLUE}🔄 設置定時同步...${NC}"
cat > /opt/chaser/auto_sync.sh << EOF
#!/bin/bash
cd $PROJECT_DIR
git pull origin main
systemctl restart chaser-backend
systemctl restart chaser-frontend
EOF

chmod +x /opt/chaser/auto_sync.sh

# 添加到crontab（每5分鐘檢查更新）
(crontab -l 2>/dev/null | grep -v auto_sync.sh; echo "*/5 * * * * /opt/chaser/auto_sync.sh >> /var/log/chaser-sync.log 2>&1") | crontab -

echo ""
echo -e "${GREEN}🎉 部署完成！${NC}"
echo ""
echo -e "${BLUE}📋 服務狀態:${NC}"
echo "後端: systemctl status chaser-backend"
echo "前端: systemctl status chaser-frontend"
echo "Nginx: systemctl status nginx"
echo ""
echo -e "${BLUE}🌐 訪問地址:${NC}"
echo "http://$DOMAIN (HTTP)"
echo "https://$DOMAIN (HTTPS - 如果SSL已設置)"
echo ""
echo -e "${BLUE}📝 日誌查看:${NC}"
echo "後端日誌: journalctl -u chaser-backend -f"
echo "前端日誌: journalctl -u chaser-frontend -f"
echo "Nginx日誌: tail -f /var/log/nginx/access.log"
echo "同步日誌: tail -f /var/log/chaser-sync.log"
echo ""
echo -e "${BLUE}🔧 常用命令:${NC}"
echo "重啟後端: systemctl restart chaser-backend"
echo "重啟前端: systemctl restart chaser-frontend"
echo "重啟全部: systemctl restart chaser-backend chaser-frontend nginx"
echo ""
echo -e "${GREEN}✅ 部署完成！你的Chaser系統現在運行在 http://$DOMAIN${NC}"