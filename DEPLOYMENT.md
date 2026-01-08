# 🚀 部署指南

本文件提供在各種平台上部署 Crypto Morning Pulse Bot 的詳細說明。

## 📋 部署前檢查清單

在部署到生產環境之前，確保完成以下步驟：

- [ ] 所有環境變數都在託管平台中設置
- [ ] Discord 機器人在目標伺服器中有適當的權限
- [ ] Bot Token 已安全存儲（不在 Git 中）
- [ ] 時區已正確配置為 UTC+8 (Asia/Taipei)
- [ ] 已測試手動觸發命令 (`!crypto-pulse-now`)
- [ ] 管理員通知頻道已配置
- [ ] 日誌目錄有寫入權限
- [ ] 所有測試都通過了

## 🚀 Railway.app 部署（推薦）

Railway.app 是部署此機器人的推薦平台，提供免費層級和簡單的 GitHub 集成。

### 步驟 1：準備 GitHub 倉庫

```bash
# 初始化 Git 倉庫
git init
git add .
git commit -m "Initial commit: Crypto Morning Pulse Bot"

# 推送到 GitHub
git remote add origin https://github.com/YOUR_USERNAME/crypto-discord-bot.git
git push -u origin main
```

### 步驟 2：連接到 Railway

1. 訪問 [Railway.app](https://railway.app/)
2. 使用 GitHub 帳戶登錄
3. 點擊 "New Project"
4. 選擇 "Deploy from GitHub repo"
5. 授權 Railway 訪問您的 GitHub 帳戶
6. 選擇 `crypto-discord-bot` 倉庫

### 步驟 3：配置環境變數

在 Railway 儀表板中：

1. 進入 "Variables" 標籤
2. 添加以下環境變數：

```
DISCORD_BOT_TOKEN=your_token_here
DISCORD_CHANNEL_ID=your_channel_id
ADMIN_CHANNEL_ID=your_admin_channel_id
BOT_OWNER_ID=your_owner_id
TIMEZONE=Asia/Taipei
CRYPTOPANIC_API_KEY=optional_key
COINGECKO_API_KEY=optional_key
```

### 步驟 4：配置啟動命令

在 Railway 儀表板中：

1. 進入 "Settings" 標籤
2. 設置 "Start Command" 為：
   ```
   python -m src.main
   ```

### 步驟 5：部署

1. 點擊 "Deploy" 按鈕
2. Railway 將自動構建並啟動機器人
3. 在 "Logs" 標籤中監控部署進度

### 監控和維護

**查看日誌**：
- 在 Railway 儀表板中點擊 "Logs" 標籤
- 實時查看機器人輸出

**更新代碼**：
- 將更改推送到 GitHub
- Railway 將自動重新部署

**手動重啟**：
- 在 Railway 儀表板中點擊 "Restart" 按鈕

## 🐳 Fly.io 部署

Fly.io 提供全球邊緣部署和免費層級。

### 步驟 1：安裝 Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
choco install flyctl
```

### 步驟 2：登錄 Fly

```bash
flyctl auth login
```

### 步驟 3：初始化應用

```bash
cd crypto-discord-bot
flyctl launch
```

按照提示進行操作：
- 應用名稱：`crypto-morning-pulse-bot`
- 區域：選擇最近的區域
- 不要設置 Postgres 數據庫

### 步驟 4：設置環境變數

```bash
flyctl secrets set \
  DISCORD_BOT_TOKEN=your_token \
  DISCORD_CHANNEL_ID=your_channel_id \
  ADMIN_CHANNEL_ID=your_admin_channel_id \
  BOT_OWNER_ID=your_owner_id \
  TIMEZONE=Asia/Taipei
```

### 步驟 5：部署

```bash
flyctl deploy
```

### 監控

```bash
# 查看日誌
flyctl logs

# 查看應用狀態
flyctl status

# SSH 進入應用
flyctl ssh console
```

## 🖥️ 自託管 VPS 部署

如果您想完全控制，可以在 DigitalOcean、Linode 或 AWS EC2 上自託管。

### 步驟 1：設置 VPS

**在 DigitalOcean 上**：

1. 創建一個新的 Droplet（最低 512MB RAM）
2. 選擇 Ubuntu 22.04 LTS
3. 添加 SSH 金鑰

### 步驟 2：安裝依賴

```bash
# 連接到 VPS
ssh root@your_vps_ip

# 更新系統
apt update && apt upgrade -y

# 安裝 Python 和必要工具
apt install -y python3.10 python3.10-venv python3-pip git curl

# 安裝 Docker（可選）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 步驟 3：克隆項目

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/crypto-discord-bot.git
cd crypto-discord-bot
```

### 步驟 4：設置虛擬環境

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 步驟 5：配置環境變數

```bash
cp .env.example .env
nano .env  # 編輯環境變數
```

### 步驟 6：使用 Systemd 設置服務

創建 `/etc/systemd/system/crypto-bot.service`：

```ini
[Unit]
Description=Crypto Morning Pulse Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/crypto-discord-bot
Environment="PATH=/opt/crypto-discord-bot/venv/bin"
ExecStart=/opt/crypto-discord-bot/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
systemctl daemon-reload
systemctl enable crypto-bot
systemctl start crypto-bot
systemctl status crypto-bot
```

### 步驟 7：設置日誌輪轉

創建 `/etc/logrotate.d/crypto-bot`：

```
/opt/crypto-discord-bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
}
```

## 🐳 Docker 部署

### 使用 Docker Compose（推薦）

```bash
# 構建和運行
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止
docker-compose down
```

### 手動 Docker 部署

```bash
# 構建鏡像
docker build -t crypto-morning-pulse-bot:latest .

# 運行容器
docker run -d \
  --name crypto-bot \
  -e DISCORD_BOT_TOKEN=your_token \
  -e DISCORD_CHANNEL_ID=your_channel_id \
  -e ADMIN_CHANNEL_ID=your_admin_channel_id \
  -e BOT_OWNER_ID=your_owner_id \
  -e TIMEZONE=Asia/Taipei \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/cache:/app/cache \
  --restart unless-stopped \
  crypto-morning-pulse-bot:latest

# 查看日誌
docker logs -f crypto-bot

# 停止容器
docker stop crypto-bot
```

## 🔒 安全部署最佳實踐

### 1. 環境變數管理

**永遠不要**：
- 將 `.env` 檔案提交到 Git
- 在代碼中硬編碼敏感信息
- 在日誌中記錄敏感信息

**應該做的**：
- 使用 `.env.example` 作為範本
- 在託管平台中設置環境變數
- 使用 `.gitignore` 排除 `.env`

### 2. Bot Token 安全

```bash
# 定期輪轉 Token
# 在 Discord Developer Portal 中重新生成 Token
# 更新託管平台中的環境變數
# 重啟機器人
```

### 3. 權限管理

確保機器人只有必要的 Discord 權限：

```
- Send Messages
- Embed Links
- Read Message History
```

不要授予以下權限：
- Administrator
- Manage Server
- Delete Messages
- Ban Members

### 4. 監控和告警

設置告警以監控機器人健康狀況：

```bash
# 檢查機器人是否運行
curl http://localhost:8080/health

# 監控 CPU 和內存使用
docker stats crypto-bot

# 檢查磁盤空間
df -h
```

### 5. 備份和恢復

定期備份緩存和日誌：

```bash
# 備份
tar -czf crypto-bot-backup-$(date +%Y%m%d).tar.gz logs/ cache/

# 恢復
tar -xzf crypto-bot-backup-20250108.tar.gz
```

## 📊 監控和維護

### 健康檢查

機器人每天 09:05 AM 發送健康檢查報告到管理員頻道。檢查以下指標：

- 發布成功狀況
- 數據源響應情況
- Nitter 實例健康狀態
- 執行時間

### 日誌分析

```bash
# 查看最近的錯誤
grep ERROR logs/crypto_bot_*.log | tail -20

# 統計每天的發布次數
grep "Posted daily briefing" logs/crypto_bot_*.log | wc -l

# 查看平均執行時間
grep "successfully in" logs/crypto_bot_*.log | \
  awk '{print $NF}' | \
  sed 's/s//' | \
  awk '{sum+=$1; count++} END {print "Average: " sum/count "s"}'
```

### 定期維護

**每週**：
- 檢查日誌中的錯誤
- 驗證機器人是否正常運行
- 檢查磁盤空間

**每月**：
- 更新依賴
- 檢查 Nitter 實例可用性
- 清理舊日誌

**每季度**：
- 審查和優化評分閾值
- 更新 KOL 監視列表
- 性能優化

## 🔄 更新和升級

### 更新代碼

```bash
# 拉取最新更改
git pull origin main

# 安裝新依賴
pip install -r requirements.txt

# 運行測試
python3 tests/test_scorer.py
python3 tests/test_formatter.py

# 重啟機器人
systemctl restart crypto-bot
```

### 更新依賴

```bash
# 檢查過期的包
pip list --outdated

# 更新所有包
pip install --upgrade -r requirements.txt

# 重新生成 requirements.txt
pip freeze > requirements.txt
```

## 🆘 部署故障排除

### 機器人無法啟動

```bash
# 檢查日誌
journalctl -u crypto-bot -n 50

# 驗證環境變數
env | grep DISCORD

# 測試 Python 環境
python3 -m src.main
```

### 內存使用過高

```bash
# 檢查內存使用
free -h

# 重啟機器人
systemctl restart crypto-bot

# 檢查是否有內存洩漏
ps aux | grep python
```

### 磁盤空間不足

```bash
# 檢查磁盤使用
df -h

# 清理舊日誌
find logs/ -name "*.log" -mtime +30 -delete

# 清理緩存
rm -f cache/content_cache.json
```

## 📞 部署支持

如有部署問題，請參考：

1. 檢查 `TROUBLESHOOTING.md`
2. 查看託管平台的文檔
3. 檢查機器人日誌
4. 提交 GitHub Issue

---

**最後更新**：2025 年 1 月 8 日
