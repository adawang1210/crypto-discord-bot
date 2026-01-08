# 🚀 Railway.app 部署指南

本指南將引導您在 Railway.app 上部署 Crypto Morning Pulse Discord Bot。

## 📋 前置要求

- Railway.app 帳戶（免費註冊：https://railway.app）
- GitHub 帳戶（已完成）
- Discord Bot Token、頻道 ID 和用戶 ID（已準備）

## 🚀 部署步驟

### 步驟 1：訪問 Railway.app

1. 前往 https://railway.app
2. 使用 GitHub 帳戶登錄（點擊 "Login with GitHub"）
3. 授權 Railway 訪問您的 GitHub 帳戶

### 步驟 2：創建新項目

1. 在 Railway 儀表板上，點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 搜索並選擇 `crypto-discord-bot` 倉庫
4. 點擊 "Deploy"

Railway 將自動檢測 Python 項目並開始構建。

### 步驟 3：配置環境變數

部署開始後，進行以下操作：

1. 在 Railway 儀表板中，點擊您的項目
2. 進入 "Variables" 標籤
3. 添加以下環境變數：

| 變數名 | 值 | 說明 |
|--------|-----|------|
| `DISCORD_BOT_TOKEN` | `your_bot_token_here` | Discord Bot Token |
| `DISCORD_CHANNEL_ID` | `your_channel_id_here` | 發送簡報的頻道 ID |
| `ADMIN_CHANNEL_ID` | `your_admin_channel_id_here` | 發送健康檢查的管理員頻道 ID |
| `BOT_OWNER_ID` | `your_owner_id_here` | 機器人擁有者的用戶 ID |
| `TIMEZONE` | `Asia/Taipei` | 時區設置 |
| `LOG_LEVEL` | `INFO` | 日誌級別 |

**可選變數**（如果您有 API 金鑰）：

| 變數名 | 值 | 說明 |
|--------|-----|------|
| `CRYPTOPANIC_API_KEY` | `your_key_here` | CryptoPanic API 金鑰（可選） |
| `COINGECKO_API_KEY` | `your_key_here` | CoinGecko API 金鑰（可選） |

### 步驟 4：配置啟動命令

1. 進入 "Settings" 標籤
2. 找到 "Start Command" 或 "Run Command"
3. 設置為：
   ```
   python -m src.main
   ```

### 步驟 5：部署

1. 所有環境變數設置完成後，Railway 將自動重新部署
2. 在 "Logs" 標籤中監控部署進度
3. 當您看到以下訊息時，表示部署成功：
   ```
   ============================================================
   🚀 Crypto Morning Pulse Bot Starting
   ============================================================
   ✅ Configuration validated successfully
   Bot logged in as CryptoBot#XXXX
   ```

## ✅ 驗證部署

部署完成後，驗證機器人是否正常運行：

### 1. 檢查日誌

在 Railway 儀表板的 "Logs" 標籤中，您應該看到：

```
2025-01-08 09:00:00 - crypto_bot - INFO - ✅ Configuration validated successfully
2025-01-08 09:00:01 - crypto_bot - INFO - Bot logged in as CryptoBot#1234
2025-01-08 09:00:02 - crypto_bot - INFO - Scheduled jobs registered
```

### 2. 測試機器人命令

在 Discord 中，在您的目標頻道中輸入：

```
!crypto-pulse-now
```

機器人應該立即發送一份簡報。

### 3. 檢查定時任務

機器人應該在每天 09:00 AM UTC+8 自動發送簡報。您可以在 Discord 中看到：

- 09:00 AM：每日簡報發布
- 09:05 AM：健康檢查報告發布到管理員頻道

## 🔍 故障排除

### 部署失敗

**症狀**：Railway 顯示構建失敗

**解決方案**：
1. 檢查 "Logs" 標籤中的錯誤訊息
2. 確保 `requirements.txt` 中的所有依賴都正確
3. 驗證 Python 版本（應該是 3.10+）
4. 點擊 "Redeploy" 重新部署

### 機器人無法連接到 Discord

**症狀**：日誌顯示 `discord.py` 連接錯誤

**解決方案**：
1. 驗證 `DISCORD_BOT_TOKEN` 是否正確
2. 確保 Discord Bot 在伺服器中有適當的權限
3. 檢查網絡連接（Railway 應該有互聯網訪問）
4. 重新生成 Bot Token 並更新環境變數

### 沒有足夠的內容項目

**症狀**：機器人在降級模式下運行

**解決方案**：
1. 檢查 Nitter 實例是否可用
2. 驗證 API 金鑰（如果已設置）
3. 降低評分閾值（編輯 `src/config.py`）
4. 檢查日誌以查看具體的數據源故障

## 📊 監控和維護

### 查看實時日誌

在 Railway 儀表板中：
1. 點擊您的項目
2. 進入 "Logs" 標籤
3. 實時查看機器人輸出

### 更新代碼

當您更新 GitHub 倉庫中的代碼時：
1. Railway 將自動檢測更改
2. 自動重新構建並部署
3. 機器人將自動重啟

### 手動重啟

如果需要手動重啟機器人：
1. 在 Railway 儀表板中進入 "Settings"
2. 點擊 "Restart" 按鈕

### 查看環境變數

1. 進入 "Variables" 標籤
2. 驗證所有環境變數都正確設置
3. 如需修改，編輯後 Railway 將自動重新部署

## 🔐 安全建議

1. **保護 Bot Token**：不要在公開的地方分享您的 Bot Token
2. **環境變數安全**：Railway 會加密存儲所有環境變數
3. **定期更新**：保持代碼和依賴最新
4. **監控日誌**：定期檢查日誌以查找異常活動

## 📞 獲取幫助

如有問題，請參考：

1. **Railway 文檔**：https://docs.railway.app/
2. **項目 README**：查看 `README.md` 中的故障排除部分
3. **Discord 開發者文檔**：https://discord.com/developers/docs

## 🎉 部署完成

恭喜！您的 Crypto Morning Pulse Discord Bot 現在已在 Railway.app 上運行。

機器人將在每天 09:00 AM UTC+8 自動發送加密貨幣市場簡報到您指定的 Discord 頻道。

---

**部署日期**：2025 年 1 月 8 日  
**版本**：1.0.0  
**平台**：Railway.app
