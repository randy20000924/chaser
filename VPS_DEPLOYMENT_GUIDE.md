# VPS部署指南 - PTT股票爬蟲系統

## 🎯 部署目標
- **GitHub倉庫**: https://github.com/randy20000924/Chaser.git
- **VPS用戶**: chaser
- **部署目錄**: /home/chaser/chaser
- **服務端口**: 前端3000, 後端8000, 資料庫5432

## 📋 VPS部署步驟

### 1. 創建chaser用戶

```bash
# 以root身份登入VPS後執行
sudo adduser chaser
# 設置密碼（請記住這個密碼）

# 將chaser用戶添加到sudo組
sudo usermod -aG sudo chaser

# 將chaser用戶添加到docker組
sudo usermod -aG docker chaser

# 切換到chaser用戶
su - chaser
```

### 2. 初始化VPS環境

```bash
# 以chaser用戶身份執行
cd /home/chaser

# 下載並執行VPS初始化腳本
wget https://raw.githubusercontent.com/randy20000924/Chaser/main/vps-setup.sh
chmod +x vps-setup.sh
./vps-setup.sh
```

### 3. 克隆代碼並部署

```bash
# 克隆GitHub倉庫
git clone https://github.com/randy20000924/Chaser.git
cd chaser

# 給所有腳本執行權限
chmod +x deploy.sh
chmod +x backend/deploy.sh
chmod +x frontend/deploy.sh

# 編輯環境變數（重要！）
nano .env
# 修改以下設定：
# - TARGET_AUTHORS=你的目標作者
# - 其他必要的環境變數

# 執行全棧部署
./deploy.sh all
```

### 4. 配置Nginx（如果需要）

```bash
# 編輯Nginx配置
sudo nano /etc/nginx/sites-available/chaser

# 確保配置正確：
# - 前端代理到 localhost:3000
# - 後端API代理到 localhost:8000

# 重啟Nginx
sudo systemctl restart nginx
```

## 🔧 重要配置

### 環境變數設定 (.env)
```env
# 資料庫配置
DATABASE_URL=postgresql+psycopg://ptt_user:ptt_password@localhost:5432/ptt_stock_crawler

# PTT配置 - 請修改為你要追蹤的作者
TARGET_AUTHORS=mrp,author2,author3

# 爬蟲配置
CRAWL_INTERVAL=300
MAX_ARTICLES_PER_CRAWL=100

# LLM配置
ENABLE_OLLAMA=true
OLLAMA_MODEL=qwen2.5:0.5b

# MCP服務器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### 端口配置
- **前端**: http://你的VPS_IP:3000
- **後端API**: http://你的VPS_IP:8000
- **PostgreSQL**: localhost:5432

## 🚀 一鍵部署命令

```bash
# 在VPS上執行（以chaser用戶身份）
cd /home/chaser/chaser
./deploy.sh all
```

## 🔍 檢查部署狀態

```bash
# 檢查服務狀態
docker-compose ps

# 檢查端口監聽
netstat -tulpn | grep -E ":(3000|8000|5432)"

# 查看日誌
docker-compose logs -f

# 測試API
curl http://localhost:8000/
curl http://localhost:3000/
```

## 📊 服務管理

### 啟動服務
```bash
cd /home/chaser/chaser
docker-compose up -d
```

### 停止服務
```bash
cd /home/chaser/chaser
docker-compose down
```

### 重啟服務
```bash
cd /home/chaser/chaser
docker-compose restart
```

### 查看日誌
```bash
cd /home/chaser/chaser
docker-compose logs -f crawler
docker-compose logs -f postgres
```

## 🔄 自動更新

### 手動更新
```bash
cd /home/chaser/chaser
git pull origin main
./deploy.sh all
```

### 設置自動更新（可選）
```bash
# 創建自動更新腳本
cat > /home/chaser/auto-update.sh << 'EOF'
#!/bin/bash
cd /home/chaser/chaser
git pull origin main
./deploy.sh all
EOF

chmod +x /home/chaser/auto-update.sh

# 設置定時任務（每小時檢查一次）
crontab -e
# 添加以下行：
# 0 * * * * /home/chaser/auto-update.sh >> /home/chaser/update.log 2>&1
```

## 🛠️ 故障排除

### 常見問題

1. **端口被占用**
   ```bash
   sudo netstat -tulpn | grep :3000
   sudo kill -9 <PID>
   ```

2. **Docker權限問題**
   ```bash
   sudo usermod -aG docker chaser
   newgrp docker
   ```

3. **服務啟動失敗**
   ```bash
   docker-compose logs
   docker-compose down
   docker-compose up -d
   ```

4. **資料庫連線失敗**
   ```bash
   docker-compose restart postgres
   sleep 10
   docker-compose up -d crawler
   ```

## 📞 支援

如有問題，請檢查：
1. 日誌文件：`/home/chaser/chaser/logs/crawler.log`
2. Docker日誌：`docker-compose logs`
3. 系統日誌：`journalctl -u docker`

## 🎉 部署完成

部署完成後，你可以通過以下URL訪問：
- **前端應用**: http://你的VPS_IP:3000
- **後端API**: http://你的VPS_IP:8000
- **API文檔**: http://你的VPS_IP:8000/docs
