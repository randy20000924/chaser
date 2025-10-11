# 🚀 VPS 部署指南

## 快速部署步驟

### 1. 準備 VPS
確保你的 VPS 滿足以下要求：
- **系統**: Ubuntu 20.04+ 或 Debian 10+
- **記憶體**: 至少 4GB RAM (推薦 8GB+)
- **儲存空間**: 至少 20GB 可用空間
- **網路**: 穩定的網路連接

### 2. 連接到 VPS
```bash
ssh root@your-vps-ip
```

### 3. 下載並執行部署腳本
```bash
# 下載部署腳本
wget https://raw.githubusercontent.com/randy20000924/chaser/main/vps_deploy.sh
chmod +x vps_deploy.sh

# 執行部署
sudo ./vps_deploy.sh
```

### 4. 安裝 Ollama (LLM 模型)
```bash
# 下載 Ollama 安裝腳本
wget https://raw.githubusercontent.com/randy20000924/chaser/main/install_ollama.sh
chmod +x install_ollama.sh

# 安裝 Ollama 和模型
sudo ./install_ollama.sh
```

### 5. 設置 SSL 證書 (可選)
```bash
# 安裝 SSL 證書
certbot --nginx -d your-domain.com

# 或使用 IP 地址 (不推薦用於生產環境)
# 跳過此步驟
```

## 部署後配置

### 檢查服務狀態
```bash
# 查看 PM2 服務狀態
pm2 status

# 查看服務日誌
pm2 logs

# 查看特定服務日誌
pm2 logs chaser-backend
pm2 logs chaser-frontend
```

### 手動同步代碼
```bash
# 手動同步最新代碼
/var/www/chaser/auto_sync.sh

# 或進入目錄手動同步
cd /var/www/chaser
git pull origin main
pm2 restart all
```

### 重啟服務
```bash
# 重啟所有服務
pm2 restart all

# 重啟特定服務
pm2 restart chaser-backend
pm2 restart chaser-frontend
```

## 服務管理

### PM2 命令
```bash
# 查看狀態
pm2 status

# 查看日誌
pm2 logs

# 重啟服務
pm2 restart all

# 停止服務
pm2 stop all

# 刪除服務
pm2 delete all

# 保存配置
pm2 save

# 設置開機自啟
pm2 startup
```

### 系統服務
```bash
# Ollama 服務
systemctl status ollama
systemctl restart ollama

# Nginx 服務
systemctl status nginx
systemctl restart nginx

# PostgreSQL 服務
systemctl status postgresql
systemctl restart postgresql
```

## 故障排除

### 檢查日誌
```bash
# 應用日誌
pm2 logs

# 系統日誌
journalctl -u ollama
journalctl -u nginx
journalctl -u postgresql

# Nginx 錯誤日誌
tail -f /var/log/nginx/error.log

# 應用錯誤日誌
tail -f /var/log/chaser/backend-error.log
tail -f /var/log/chaser/frontend-error.log
```

### 常見問題

#### 1. 端口被佔用
```bash
# 查看端口使用情況
netstat -tlnp | grep :8000
netstat -tlnp | grep :3000

# 殺死佔用端口的進程
sudo kill -9 <PID>
```

#### 2. 記憶體不足
```bash
# 查看記憶體使用情況
free -h
htop

# 重啟服務釋放記憶體
pm2 restart all
```

#### 3. 資料庫連接失敗
```bash
# 檢查 PostgreSQL 狀態
systemctl status postgresql

# 檢查資料庫連接
sudo -u postgres psql -c "SELECT 1;"

# 重啟資料庫
systemctl restart postgresql
```

#### 4. Ollama 模型下載失敗
```bash
# 檢查 Ollama 狀態
systemctl status ollama

# 手動下載模型
sudo -u www-data ollama pull qwen2.5:0.5b

# 檢查模型列表
ollama list
```

## 性能優化

### 1. 調整 PM2 配置
編輯 `/var/www/chaser/ecosystem.config.js`：
```javascript
{
  instances: 'max',  // 使用所有 CPU 核心
  max_memory_restart: '2G',  // 增加記憶體限制
}
```

### 2. 優化 Nginx 配置
編輯 `/etc/nginx/sites-available/chaser`：
```nginx
# 添加緩存配置
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 資料庫優化
```sql
-- 連接 PostgreSQL
sudo -u postgres psql chaser_db

-- 創建索引
CREATE INDEX CONCURRENTLY idx_articles_author_time ON ptt_articles(author, publish_time);
CREATE INDEX CONCURRENTLY idx_articles_analyzed ON ptt_articles(is_analyzed);
```

## 監控和維護

### 設置監控
```bash
# 安裝 htop 用於系統監控
apt install htop

# 設置日誌輪轉
cat > /etc/logrotate.d/chaser << EOF
/var/log/chaser/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 www-data www-data
}
EOF
```

### 定期維護
```bash
# 創建維護腳本
cat > /var/www/chaser/maintenance.sh << 'EOF'
#!/bin/bash
# 清理舊日誌
find /var/log/chaser -name "*.log" -mtime +7 -delete

# 重啟服務
pm2 restart all

# 檢查磁盤空間
df -h
EOF

chmod +x /var/www/chaser/maintenance.sh

# 設置定期維護 (每週執行)
echo "0 2 * * 0 /var/www/chaser/maintenance.sh" | crontab -u root -
```

## 安全建議

1. **更改默認密碼**: 修改資料庫密碼
2. **設置防火牆**: 只開放必要端口
3. **定期更新**: 保持系統和套件最新
4. **備份資料**: 定期備份資料庫和代碼
5. **監控日誌**: 定期檢查錯誤日誌

## 支援

如果遇到問題，請檢查：
1. 系統日誌: `journalctl -f`
2. 應用日誌: `pm2 logs`
3. 網路連接: `curl -I http://localhost:8000`
4. 服務狀態: `systemctl status ollama nginx postgresql`

---

🎉 **部署完成！** 你的 PTT Stock Crawler 現在應該在 VPS 上運行了！
