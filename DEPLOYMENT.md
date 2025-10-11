# Chaser 部署指南

## 📁 專案結構

```
chaser/
├── backend/                    # 後端 (Python)
│   ├── main.py                # 主應用程式
│   ├── config.py              # 配置管理
│   ├── database.py            # 資料庫連線
│   ├── models.py              # 資料庫模型
│   ├── ptt_crawler.py         # PTT爬蟲模組
│   ├── data_processor.py      # 資料處理器
│   ├── article_analyzer.py    # 文章分析模組
│   ├── http_mcp_server.py     # HTTP MCP Server
│   ├── requirements.txt       # Python依賴
│   ├── env.example           # 環境變數範例
│   ├── install.sh            # 安裝腳本
│   └── deploy.sh             # 後端部署腳本
├── frontend/                   # 前端 (Next.js)
│   ├── src/app/              # Next.js應用
│   ├── package.json          # Node.js依賴
│   ├── next.config.ts        # Next.js配置
│   └── deploy.sh             # 前端部署腳本
├── deploy.sh                  # 一鍵部署腳本
├── vps-deploy.sh             # VPS部署腳本
└── docker-compose.yml        # Docker配置
```

## 🚀 本地部署

### 一鍵部署
```bash
chmod +x deploy.sh
./deploy.sh
```

### 分別部署

#### 後端部署
```bash
cd backend
chmod +x deploy.sh
./deploy.sh
```

#### 前端部署
```bash
cd frontend
chmod +x deploy.sh
./deploy.sh
```

## 🌐 VPS部署

### 在VPS上執行
```bash
# 下載並執行VPS部署腳本
wget https://raw.githubusercontent.com/randy20000924/Chaser/main/vps-deploy.sh
chmod +x vps-deploy.sh
./vps-deploy.sh
```

### 手動部署步驟

1. **連接到VPS**
```bash
ssh your-username@your-vps-ip
```

2. **克隆專案**
```bash
cd /var/www
sudo git clone https://github.com/randy20000924/Chaser.git
sudo chown -R $USER:$USER chaser
cd chaser
```

3. **執行部署腳本**
```bash
chmod +x vps-deploy.sh
./vps-deploy.sh
```

## 🔧 配置說明

### 後端配置 (backend/.env)
```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/chaser
TARGET_AUTHORS=["mrp"]
CRAWL_INTERVAL=300
ENABLE_OLLAMA=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### 前端配置 (frontend/.env.local)
```env
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
```

## 🌐 端口配置

- **後端 (MCP Server)**: 8000
- **前端 (Next.js)**: 3000
- **Nginx (反向代理)**: 80

## 📋 服務管理

### 查看服務狀態
```bash
sudo systemctl status chaser-backend
sudo systemctl status chaser-frontend
sudo systemctl status nginx
```

### 重啟服務
```bash
sudo systemctl restart chaser-backend
sudo systemctl restart chaser-frontend
sudo systemctl restart nginx
```

### 查看日誌
```bash
sudo journalctl -u chaser-backend -f
sudo journalctl -u chaser-frontend -f
```

## 🔄 更新部署

### 更新代碼
```bash
cd /var/www/chaser
git pull origin main
```

### 重啟服務
```bash
sudo systemctl restart chaser-backend chaser-frontend
```

## 🐳 Docker部署

```bash
docker-compose up -d
```

## 📞 故障排除

1. **端口衝突**: 檢查8000和3000端口是否被占用
2. **權限問題**: 確保文件權限正確
3. **依賴問題**: 檢查Python和Node.js版本
4. **資料庫連線**: 檢查PostgreSQL服務狀態
