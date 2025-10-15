#!/bin/bash

# VPS 性能測試腳本

echo "🚀 開始 VPS 性能測試..."
echo "=================================="

# 進入專案目錄
cd /var/www/chaser

# 激活虛擬環境
source venv/bin/activate

# 檢查 Ollama 模型
echo "📋 檢查當前 Ollama 模型:"
ollama list

echo ""
echo "🔍 檢查 Ollama 服務狀態:"
systemctl status ollama --no-pager -l

echo ""
echo "📊 檢查系統資源:"
echo "CPU 使用率:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1

echo "記憶體使用率:"
free -h

echo "磁碟使用率:"
df -h /var/www/chaser

echo ""
echo "🕷️ 開始爬蟲和分析性能測試..."
echo "=================================="

# 運行快速測試
python quick_test.py

echo ""
echo "📈 測試完成！"
echo "=================================="
