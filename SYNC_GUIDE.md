# 🔄 自動同步使用指南

## 📋 同步架構

```
本地端 → GitHub → VPS
  ↓        ↓      ↓
手動推送  自動檢查  自動拉取
```

## 🚀 本地端使用

### **方法 1: 智能同步 (推薦)**
```bash
./sync.sh
```
- ✅ 檢查是否有變更
- ✅ 自動提交到 Git
- ✅ 推送到 GitHub
- ✅ VPS 自動更新

### **方法 2: 快速同步**
```bash
./quick_sync.sh
```
- ⚡ 不檢查變更，直接推送
- ⚡ 適合緊急更新

## 🖥️ VPS 端設定

### **第一次設定**
```bash
# 在 VPS 上執行
cd /var/www/chaser
chmod +x vps_sync.sh

# 設定定時任務 (每 2 分鐘檢查)
(crontab -l 2>/dev/null; echo "*/2 * * * * /var/www/chaser/vps_sync.sh >> /var/log/chaser_sync.log 2>&1") | crontab -

# 測試腳本
./vps_sync.sh
```

### **檢查同步狀態**
```bash
# 查看同步日誌
tail -f /var/log/chaser_sync.log

# 檢查 crontab 設定
crontab -l

# 手動執行同步
./vps_sync.sh
```

## ⏰ 同步時間

- **本地推送**: 立即
- **VPS 檢查**: 每 2 分鐘
- **VPS 更新**: 發現更新後立即執行

## 🔧 故障排除

### **本地推送失敗**
```bash
# 檢查 Git 狀態
git status

# 強制推送
git push -f origin main
```

### **VPS 不同步**
```bash
# 檢查網路連線
ping github.com

# 手動拉取
cd /var/www/chaser
git pull origin main
```

### **查看詳細日誌**
```bash
# 查看 crontab 日誌
grep CRON /var/log/syslog

# 查看同步腳本日誌
cat /var/log/chaser_sync.log
```

## 📝 注意事項

1. **本地端**: 修改程式碼後執行 `./sync.sh`
2. **VPS端**: 自動檢查，無需手動操作
3. **日誌**: 所有同步記錄保存在 `/var/log/chaser_sync.log`
4. **頻率**: VPS 每 2 分鐘檢查一次 GitHub 更新

## 🎯 最佳實踐

1. **開發流程**:
   ```bash
   # 1. 修改程式碼
   # 2. 測試本地功能
   # 3. 執行同步
   ./sync.sh
   # 4. 等待 2 分鐘檢查 VPS
   ```

2. **緊急更新**:
   ```bash
   # 使用快速同步
   ./quick_sync.sh
   ```

3. **檢查狀態**:
   ```bash
   # 查看 VPS 日誌
   ssh root@159.198.37.93 "tail -f /var/log/chaser_sync.log"
   ```
