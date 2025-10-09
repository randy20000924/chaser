# 🚀 Chaser VPS部署檢查清單

## 部署前準備

### ✅ 域名設置
- [ ] 在Namecheap DNS中設置A記錄：`www.chaser.cloud` → `159.198.37.93`
- [ ] 等待DNS傳播（通常5-30分鐘）
- [ ] 測試域名解析：`nslookup www.chaser.cloud`

### ✅ VPS準備
- [ ] 確認VPS可以SSH連接：`ssh root@159.198.37.93`
- [ ] 確認VPS有足夠資源（最少2GB RAM，20GB儲存）
- [ ] 確認VPS是Ubuntu 20.04+或Debian 11+

## 快速部署（推薦）

### ✅ 一鍵部署
```bash
# 1. SSH連接到VPS
ssh root@159.198.37.93

# 2. 下載並執行部署腳本
wget https://raw.githubusercontent.com/randy20000924/chaser/main/deploy_vps.sh
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### ✅ 等待部署完成
- [ ] 等待10-15分鐘讓腳本完成所有設置
- [ ] 檢查腳本輸出是否有錯誤

## 部署後驗證

### ✅ 服務檢查
```bash
# 檢查所有服務狀態
systemctl status chaser-backend
systemctl status chaser-frontend
systemctl status nginx
systemctl status postgresql

# 應該看到所有服務都是 "active (running)"
```

### ✅ 端口檢查
```bash
# 檢查端口是否監聽
netstat -tlnp | grep -E ':(3000|8000|80|443)'

# 應該看到：
# :80 (Nginx)
# :443 (Nginx SSL)
# :3000 (前端)
# :8000 (後端)
```

### ✅ 網站訪問測試
- [ ] 訪問 https://www.chaser.cloud
- [ ] 確認網站正常載入
- [ ] 測試搜尋功能
- [ ] 檢查API健康狀態：https://www.chaser.cloud/api/health

### ✅ SSL證書檢查
```bash
# 檢查SSL證書
certbot certificates

# 應該看到有效的證書
```

## 功能測試

### ✅ 前端功能
- [ ] 在搜尋框輸入作者名稱（如"mrp"）
- [ ] 確認文章列表正常顯示
- [ ] 檢查文章分析結果是否顯示
- [ ] 確認高推文數文章顯示紅色"爆"字

### ✅ 後端功能
```bash
# 測試API端點
curl https://www.chaser.cloud/api/health
curl -X POST https://www.chaser.cloud/api/authors/articles \
  -H "Content-Type: application/json" \
  -d '{"author": "mrp"}'
```

### ✅ 爬蟲功能
- [ ] 檢查爬蟲是否在運行：`journalctl -u chaser-backend -f`
- [ ] 確認定時任務設置：`crontab -l`
- [ ] 檢查資料庫是否有數據：`psql -h localhost -U chaser_user -d chaser_db -c "SELECT COUNT(*) FROM ptt_articles;"`

## 監控設置

### ✅ 日誌監控
```bash
# 設置日誌監控
journalctl -u chaser-backend -f &
journalctl -u chaser-frontend -f &
```

### ✅ 自動同步檢查
```bash
# 檢查自動同步腳本
ls -la /opt/chaser/auto_sync.sh
crontab -l | grep auto_sync
```

## 故障排除

### ❌ 如果網站無法訪問
1. 檢查Nginx狀態：`systemctl status nginx`
2. 檢查Nginx配置：`nginx -t`
3. 檢查防火牆：`ufw status`
4. 檢查域名DNS：`nslookup www.chaser.cloud`

### ❌ 如果後端API無法訪問
1. 檢查後端服務：`systemctl status chaser-backend`
2. 檢查後端日誌：`journalctl -u chaser-backend -n 50`
3. 檢查資料庫連接：`psql -h localhost -U chaser_user -d chaser_db`

### ❌ 如果前端無法訪問
1. 檢查前端服務：`systemctl status chaser-frontend`
2. 檢查前端日誌：`journalctl -u chaser-frontend -n 50`
3. 檢查Node.js進程：`ps aux | grep node`

## 維護命令

### 🔧 常用維護命令
```bash
# 重啟所有服務
systemctl restart chaser-backend chaser-frontend nginx

# 查看服務日誌
journalctl -u chaser-backend -f
journalctl -u chaser-frontend -f

# 手動同步代碼
cd /opt/chaser && git pull origin main

# 檢查系統資源
htop
df -h
free -h
```

### 🔄 更新部署
```bash
# 本地更新後，推送到GitHub
git add .
git commit -m "更新功能"
git push origin main

# VPS會自動在5分鐘內同步更新
```

## ✅ 部署完成確認

當所有檢查項目都完成後，你的Chaser系統應該：

- [ ] 網站正常運行在 https://www.chaser.cloud
- [ ] 前端搜尋功能正常
- [ ] 後端API正常響應
- [ ] 爬蟲定時執行
- [ ] 自動同步設置完成
- [ ] SSL證書有效
- [ ] 所有服務穩定運行

🎉 **恭喜！你的Chaser系統已經成功部署並運行！**
