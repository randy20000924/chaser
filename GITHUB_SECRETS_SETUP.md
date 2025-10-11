# GitHub Secrets 設置指南

## 🔐 設置GitHub Secrets（可選）

如果你想要啟用自動VPS部署，需要在GitHub倉庫中設置以下Secrets：

### 1. 進入GitHub倉庫設置
1. 前往 https://github.com/randy20000924/Chaser
2. 點擊 **Settings** 標籤
3. 在左側選單中點擊 **Secrets and variables** → **Actions**

### 2. 添加以下Secrets

#### VPS_HOST
- **名稱**: `VPS_HOST`
- **值**: 你的VPS IP地址（例如：`123.456.789.0`）

#### VPS_USERNAME
- **名稱**: `VPS_USERNAME`
- **值**: `chaser`

#### VPS_SSH_KEY
- **名稱**: `VPS_SSH_KEY`
- **值**: 你的SSH私鑰內容

### 3. 生成SSH密鑰（如果沒有）

在本地電腦上執行：
```bash
# 生成SSH密鑰對
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 查看公鑰（需要添加到VPS）
cat ~/.ssh/id_rsa.pub

# 查看私鑰（需要添加到GitHub Secrets）
cat ~/.ssh/id_rsa
```

### 4. 將SSH公鑰添加到VPS

在VPS上執行：
```bash
# 以chaser用戶身份
mkdir -p ~/.ssh
echo "你的SSH公鑰內容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

## 🚫 不設置Secrets的影響

如果你不設置這些Secrets：
- ✅ 代碼檢查和構建測試仍然會運行
- ✅ Docker鏡像會正常構建
- ❌ 自動VPS部署會被跳過
- ✅ 你可以手動在VPS上部署

## 🔄 手動部署流程

如果不設置Secrets，你可以使用手動部署：

1. **推送代碼到GitHub**：
   ```bash
   git add .
   git commit -m "更新代碼"
   git push origin main
   ```

2. **在VPS上手動部署**：
   ```bash
   cd /home/chaser/chaser
   git pull origin main
   ./deploy.sh all
   ```

## 📊 查看GitHub Actions狀態

1. 前往 https://github.com/randy20000924/Chaser/actions
2. 查看最新的工作流程執行狀態
3. 點擊具體的執行查看詳細日誌

## 🛠️ 故障排除

### 如果GitHub Actions失敗
1. 檢查Secrets是否正確設置
2. 確認VPS SSH連接正常
3. 查看Actions日誌中的錯誤信息

### 如果手動部署失敗
1. 檢查VPS上的文件權限
2. 確認Docker服務正常運行
3. 查看部署腳本的錯誤輸出
