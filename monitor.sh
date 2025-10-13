#!/bin/bash
# PM2 監控腳本

echo "=== PM2 服務狀態 ==="
pm2 status

echo -e "\n=== 系統資源使用 ==="
free -h
df -h /

echo -e "\n=== 最近錯誤日誌 ==="
pm2 logs --lines 10 --err

echo -e "\n=== 重啟統計 ==="
pm2 show chaser-backend | grep -E "(restart|uptime)"
pm2 show chaser-frontend | grep -E "(restart|uptime)"
pm2 show chaser-scheduler | grep -E "(restart|uptime)"
