#!/bin/bash

# VPS初始化腳本 - Ubuntu 24.04
# 使用方法: ./vps-setup.sh

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "開始初始化VPS環境..."

# 更新系統
log_info "更新系統包..."
apt update && apt upgrade -y

# 安裝基本工具
log_info "安裝基本工具..."
apt install -y curl wget git vim htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# 安裝Docker
log_info "安裝Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 啟動Docker服務
systemctl start docker
systemctl enable docker

# 將當前用戶添加到docker組
usermod -aG docker $USER

# 安裝Docker Compose
log_info "安裝Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# 安裝Node.js 18
log_info "安裝Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 安裝Python 3.11
log_info "安裝Python 3.11..."
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 安裝PostgreSQL客戶端
log_info "安裝PostgreSQL客戶端..."
apt install -y postgresql-client

# 安裝Nginx
log_info "安裝Nginx..."
apt install -y nginx

# 創建應用目錄
log_info "創建應用目錄..."
mkdir -p /var/www/chaser
mkdir -p /var/log/chaser

# 設置權限
chown -R $USER:$USER /var/www/chaser
chown -R $USER:$USER /var/log/chaser

# 配置Nginx
log_info "配置Nginx..."
cat > /etc/nginx/sites-available/chaser << 'EOF'
server {
    listen 80;
    server_name _;
    
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
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# 啟用站點
ln -sf /etc/nginx/sites-available/chaser /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 測試Nginx配置
nginx -t

# 重啟Nginx
systemctl restart nginx
systemctl enable nginx

# 配置防火牆
log_info "配置防火牆..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# 安裝Ollama（可選）
read -p "是否安裝Ollama LLM服務？(y/n): " install_ollama
if [[ $install_ollama =~ ^[Yy]$ ]]; then
    log_info "安裝Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # 下載qwen2.5:0.5b模型
    log_info "下載qwen2.5:0.5b模型..."
    ollama pull qwen2.5:0.5b
fi

# 創建環境變數文件
log_info "創建環境變數文件..."
cat > /var/www/chaser/.env << 'EOF'
# 資料庫配置
DATABASE_URL=postgresql+psycopg://ptt_user:ptt_password@localhost:5432/ptt_stock_crawler

# PTT配置
PTT_BASE_URL=https://www.ptt.cc
PTT_STOCK_BOARD=Stock
TARGET_AUTHORS=mrp

# 爬蟲配置
CRAWL_INTERVAL=300
MAX_ARTICLES_PER_CRAWL=100
ENABLE_SELENIUM=false
HTTP_PROXY_URL=
RANDOM_USER_AGENT=true

# LLM配置
ENABLE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

# MCP服務器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_URL=http://localhost:8000

# 定時任務配置
SCHEDULED_TIME=15:00
TIMEZONE=Asia/Taipei

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=logs/crawler.log
EOF

# 設置權限
chown $USER:$USER /var/www/chaser/.env
chmod 600 /var/www/chaser/.env

log_success "VPS初始化完成！"
log_info "請執行以下步驟完成部署："
log_info "1. 將SSH公鑰添加到GitHub Secrets:"
log_info "   - VPS_HOST: 你的VPS IP地址"
log_info "   - VPS_USERNAME: 你的用戶名"
log_info "   - VPS_SSH_KEY: 你的SSH私鑰"
log_info "2. 克隆代碼到VPS:"
log_info "   git clone https://github.com/你的用戶名/chaser.git /var/www/chaser"
log_info "3. 運行部署腳本:"
log_info "   cd /var/www/chaser && chmod +x deploy.sh && ./deploy.sh all"
