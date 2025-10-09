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

# 2. 安裝必要套件
echo -e "${BLUE}🔧 安裝必要套件...${NC}"

# 先更新套件列表
apt update

# 安裝基礎套件
apt install -y curl wget git nginx certbot python3-certbot-nginx postgresql postgresql-contrib python3 python3-pip python3-venv docker.io docker-compose ufw

# 安裝 Node.js 和 npm (使用 NodeSource 官方源)
echo -e "${BLUE}📦 安裝 Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 驗證安裝
node --version
npm --version

# 3. 啟動服務
echo -e "${BLUE}🔄 啟動服務...${NC}"
systemctl start postgresql
systemctl enable postgresql
systemctl start docker
systemctl enable docker
systemctl start nginx
systemctl enable nginx

# 4. 配置PostgreSQL
echo -e "${BLUE}🗄️ 配置PostgreSQL...${NC}"
sudo -u postgres psql -c "CREATE DATABASE chaser_db;"
sudo -u postgres psql -c "CREATE USER chaser_user WITH PASSWORD 'chaser_password_2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chaser_db TO chaser_user;"

# 5. 創建專案目錄
echo -e "${BLUE}📁 創建專案目錄...${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 6. 克隆專案
echo -e "${BLUE}📥 克隆專案...${NC}"
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/randy20000924/chaser.git .
fi

# 7. 設置Python環境
echo -e "${BLUE}🐍 設置Python環境...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 8. 設置環境變數
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

# 9. 初始化資料庫
echo -e "${BLUE}🗄️ 初始化資料庫...${NC}"
source venv/bin/activate
python -c "from database import db_manager; db_manager.create_tables()"

# 10. 設置前端
echo -e "${BLUE}🌐 設置前端...${NC}"
cd frontend
npm install
npm run build
cd ..

# 11. 配置Nginx
echo -e "${BLUE}🌐 配置Nginx...${NC}"
cat > /etc/nginx/sites-available/chaser << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # 前端
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

    # 後端API
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

# 啟用站點
ln -sf /etc/nginx/sites-available/chaser /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# 12. 設置SSL證書
echo -e "${BLUE}🔒 設置SSL證書...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# 13. 配置防火牆
echo -e "${BLUE}🔥 配置防火牆...${NC}"
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# 14. 創建系統服務
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

# 15. 啟動服務
echo -e "${BLUE}🚀 啟動服務...${NC}"
systemctl daemon-reload
systemctl enable chaser-backend
systemctl enable chaser-frontend
systemctl start chaser-backend
systemctl start chaser-frontend

# 16. 設置定時同步
echo -e "${BLUE}🔄 設置定時同步...${NC}"
cat > /opt/chaser/auto_sync.sh << EOF
#!/bin/bash
cd $PROJECT_DIR
git pull origin main
systemctl restart chaser-backend
systemctl restart chaser-frontend
EOF

chmod +x /opt/chaser/auto_sync.sh

# 添加到crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/chaser/auto_sync.sh") | crontab -

echo -e "${GREEN}🎉 部署完成！${NC}"
echo ""
echo -e "${BLUE}📋 服務狀態:${NC}"
echo "後端: systemctl status chaser-backend"
echo "前端: systemctl status chaser-frontend"
echo "Nginx: systemctl status nginx"
echo ""
echo -e "${BLUE}🌐 訪問地址:${NC}"
echo "https://$DOMAIN"
echo ""
echo -e "${BLUE}📝 日誌查看:${NC}"
echo "後端日誌: journalctl -u chaser-backend -f"
echo "前端日誌: journalctl -u chaser-frontend -f"
echo "Nginx日誌: tail -f /var/log/nginx/access.log"
echo ""
echo -e "${GREEN}✅ 部署完成！你的Chaser系統現在運行在 https://$DOMAIN${NC}"
