#!/bin/bash
# VPS 自動同步設定腳本

echo "🚀 設定 VPS 自動同步..."

# 在 VPS 上執行以下命令
cat << 'EOF'
# 1. 進入專案目錄
cd /var/www/chaser

# 2. 設定腳本權限
chmod +x vps_sync.sh

# 3. 設定 crontab 每 2 分鐘檢查一次
(crontab -l 2>/dev/null; echo "*/2 * * * * /var/www/chaser/vps_sync.sh >> /var/log/chaser_sync.log 2>&1") | crontab -

# 4. 建立日誌目錄
mkdir -p /var/log

# 5. 測試腳本
./vps_sync.sh

# 6. 檢查 crontab 設定
crontab -l

echo "✅ VPS 自動同步設定完成！"
echo "📝 日誌位置: /var/log/chaser_sync.log"
echo "⏰ 檢查頻率: 每 2 分鐘"
EOF

echo "📋 請在 VPS 上執行上述命令"
