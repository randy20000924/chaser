#!/bin/bash

# VPS 部署腳本
echo "🚀 開始在 VPS 上部署 Chaser 專案..."

# 設定變數
REPO_URL="https://github.com/randy20000924/Chaser.git"
DEPLOY_DIR="/var/www/chaser"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 更新系統
echo "📦 更新系統套件..."
sudo apt update && sudo apt upgrade -y

# 安裝必要套件
echo "🔧 安裝必要套件..."
sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib nginx git

# 創建部署目錄
echo "📁 創建部署目錄..."
sudo mkdir -p $DEPLOY_DIR
sudo chown $USER:$USER $DEPLOY_DIR

# 克隆專案
echo "📥 克隆專案..."
cd $DEPLOY_DIR
git clone $REPO_URL .

# 部署 Backend
echo "📦 部署 Backend..."
cd backend
chmod +x deploy.sh
./deploy.sh

# 創建 Backend 系統服務
echo "🔧 創建 Backend 系統服務..."
sudo tee /etc/systemd/system/chaser-backend.service > /dev/null << EOF
[Unit]
Description=Chaser Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_DIR/backend
Environment=PATH=$DEPLOY_DIR/backend/venv/bin
ExecStart=$DEPLOY_DIR/backend/venv/bin/python main.py --mode both
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 部署 Frontend
echo "🌐 部署 Frontend..."
cd ../frontend
chmod +x deploy.sh
./deploy.sh

# 創建 Frontend 系統服務
echo "🔧 創建 Frontend 系統服務..."
sudo tee /etc/systemd/system/chaser-frontend.service > /dev/null << EOF
[Unit]
Description=Chaser Frontend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_DIR/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 配置 Nginx
echo "🌐 配置 Nginx..."
sudo tee /etc/nginx/sites-available/chaser > /dev/null << EOF
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
sudo ln -sf /etc/nginx/sites-available/chaser /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 啟動服務
echo "🚀 啟動服務..."
sudo systemctl daemon-reload
sudo systemctl enable chaser-backend chaser-frontend
sudo systemctl start chaser-backend chaser-frontend

echo "✅ VPS 部署完成！"
echo ""
echo "📋 服務狀態:"
echo "  Backend:  sudo systemctl status chaser-backend"
echo "  Frontend: sudo systemctl status chaser-frontend"
echo "  Nginx:    sudo systemctl status nginx"
echo ""
echo "🌐 訪問地址:"
echo "  http://your-vps-ip"
echo ""
echo "📝 日誌查看:"
echo "  Backend:  sudo journalctl -u chaser-backend -f"
echo "  Frontend: sudo journalctl -u chaser-frontend -f"
