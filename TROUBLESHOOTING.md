# 🔧 故障排除指南

本文件提供常見問題的診斷和解決方案。

## 🚨 常見錯誤和解決方案

### 1. Discord 連接錯誤

**症狀**：機器人無法連接到 Discord，日誌顯示 `discord.py` 連接錯誤

**可能原因**：
- Discord Bot Token 無效或過期
- 網絡連接問題
- Discord 伺服器宕機

**診斷步驟**：

```bash
# 驗證 Token 格式
echo $DISCORD_BOT_TOKEN | wc -c  # 應該是 72 個字符

# 測試網絡連接
ping discord.com

# 檢查日誌中的具體錯誤
tail -f logs/crypto_bot_$(date +%Y-%m-%d).log | grep -i error
```

**解決方案**：

1. 從 [Discord Developer Portal](https://discord.com/developers/applications) 重新生成 Bot Token
2. 確保 `.env` 檔案中的 Token 沒有額外的空格或換行符
3. 驗證機器人在 Discord 伺服器中有 "Send Messages" 和 "Embed Links" 權限
4. 重啟機器人

### 2. 頻道 ID 無效

**症狀**：日誌顯示 `Channel not found` 錯誤

**診斷步驟**：

```bash
# 驗證頻道 ID 格式（應該是純數字）
echo $DISCORD_CHANNEL_ID | grep -E '^[0-9]+$'

# 檢查機器人是否可以訪問該頻道
# 在 Discord 中，右鍵點擊頻道 → 複製頻道 ID
```

**解決方案**：

1. 確保 `DISCORD_CHANNEL_ID` 是正確的數字 ID（不是頻道名稱）
2. 驗證機器人在該頻道中有權限
3. 確保頻道不是私有的或受限的

### 3. Nitter 實例無法訪問

**症狀**：日誌顯示 `Nitter instance returned 403/429`，無法抓取 KOL 貼文

**診斷步驟**：

```bash
# 測試 Nitter 實例的可用性
for instance in nitter.net nitter.poast.org nitter.privacydev.net; do
  echo "Testing $instance..."
  curl -s -o /dev/null -w "%{http_code}" "https://$instance/VitalikButerin"
  echo ""
done

# 檢查日誌中的 Nitter 狀態
grep -i "nitter" logs/crypto_bot_$(date +%Y-%m-%d).log
```

**解決方案**：

1. **增加請求延遲**：編輯 `.env` 中的 `NITTER_REQUEST_DELAY`
   ```env
   NITTER_REQUEST_DELAY=3.5  # 增加到 3.5 秒
   ```

2. **添加新的 Nitter 實例**：編輯 `.env` 中的 `NITTER_INSTANCES`
   ```env
   NITTER_INSTANCES=nitter.net,nitter.poast.org,nitter.privacydev.net,nitter.privacytools.io,nitter.moomoo.me
   ```

3. **檢查實例健康狀態**：訪問 Nitter 實例的主頁
   ```bash
   curl -s "https://nitter.net" | head -20
   ```

4. **使用代理**：如果 ISP 阻止 Nitter，考慮使用 VPN

### 4. 沒有足夠的內容項目

**症狀**：機器人在降級模式下運行或完全跳過發布

**日誌示例**：
```
WARNING - Insufficient items for briefing: 2 (minimum: 3)
```

**診斷步驟**：

```bash
# 檢查評分閾值設置
grep "MIN_" .env

# 查看評分日誌
grep -i "scored\|threshold" logs/crypto_bot_$(date +%Y-%m-%d).log

# 手動觸發簡報以查看詳細日誌
# 在 Discord 中輸入: !crypto-pulse-now
```

**解決方案**：

1. **降低評分閾值**：編輯 `.env` 中的閾值
   ```env
   MIN_IMPACT_SCORE=6      # 從 7 降低到 6
   MIN_KOL_SCORE=55        # 從 60 降低到 55
   ```

2. **驗證 API 金鑰**：
   ```bash
   # 測試 CryptoPanic API
   curl "https://cryptopanic.com/api/v1/posts/?auth_token=YOUR_KEY&kind=news" | head -20
   ```

3. **檢查 KOL 帳戶**：確保 KOL 帳戶名稱正確
   ```bash
   # 測試 Nitter 上的 KOL 帳戶
   curl -s "https://nitter.net/VitalikButerin" | grep -i "tweet" | head -5
   ```

4. **增加數據源**：在 `src/data_fetcher.py` 中添加更多 RSS 源

### 5. API 速率限制

**症狀**：日誌顯示 429 (Too Many Requests) 錯誤

**診斷步驟**：

```bash
# 檢查 API 調用頻率
grep "429\|rate" logs/crypto_bot_$(date +%Y-%m-%d).log

# 查看 CryptoPanic 速率限制狀態
curl -I "https://cryptopanic.com/api/v1/posts/?auth_token=YOUR_KEY"
```

**解決方案**：

1. **增加請求延遲**
   ```env
   NITTER_REQUEST_DELAY=3.0
   ```

2. **使用 API 金鑰**：確保在 `.env` 中設置了 API 金鑰
   ```env
   CRYPTOPANIC_API_KEY=your_key_here
   ```

3. **減少並發請求**
   ```env
   MAX_CONCURRENT_REQUESTS=5  # 從 10 降低到 5
   ```

4. **實施請求緩存**：已在代碼中實現，檢查 `cache/` 目錄

### 6. 日誌文件權限錯誤

**症狀**：`Permission denied` 錯誤寫入日誌

**診斷步驟**：

```bash
# 檢查目錄權限
ls -la logs/
ls -la cache/

# 檢查當前用戶
whoami
```

**解決方案**：

```bash
# 修復目錄權限
chmod -R 755 logs/
chmod -R 755 cache/

# 或者，更改所有權
sudo chown -R $USER:$USER logs/
sudo chown -R $USER:$USER cache/
```

### 7. 虛擬環境問題

**症狀**：`ModuleNotFoundError` 或 `No module named 'discord'`

**診斷步驟**：

```bash
# 檢查虛擬環境是否激活
echo $VIRTUAL_ENV

# 檢查已安裝的包
pip list | grep discord
```

**解決方案**：

```bash
# 激活虛擬環境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 重新安裝依賴
pip install -r requirements.txt
```

### 8. 時區問題

**症狀**：機器人在錯誤的時間發布簡報

**診斷步驟**：

```bash
# 檢查系統時區
timedatectl  # Linux
date  # 所有系統

# 檢查 .env 中的時區設置
grep TIMEZONE .env

# 檢查日誌中的時間戳
tail logs/crypto_bot_$(date +%Y-%m-%d).log
```

**解決方案**：

1. **設置正確的時區**
   ```env
   TIMEZONE=Asia/Taipei  # 或您的時區
   ```

2. **同步系統時間**
   ```bash
   # Linux
   sudo timedatectl set-timezone Asia/Taipei
   
   # 或使用 NTP
   sudo ntpdate -s time.nist.gov
   ```

3. **驗證時區列表**
   ```bash
   python3 -c "import pytz; print(pytz.all_timezones)"
   ```

## 🔍 調試技巧

### 啟用詳細日誌

編輯 `.env` 以啟用調試日誌：

```env
LOG_LEVEL=DEBUG
```

### 手動測試數據抓取

創建一個測試腳本 `test_fetch.py`：

```python
import asyncio
from src.data_fetcher import DataFetcher

async def test():
    async with DataFetcher() as fetcher:
        data = await fetcher.fetch_all_data()
        print(f"KOL Posts: {len(data['kol_posts'])}")
        print(f"News Items: {len(data['news'])}")
        print(f"Nitter Status: {data['nitter_status']}")

asyncio.run(test())
```

運行測試：

```bash
python3 test_fetch.py
```

### 手動測試評分系統

創建一個測試腳本 `test_score.py`：

```python
from src.scorer import ContentScorer

scorer = ContentScorer()

test_post = {
    "username": "VitalikButerin",
    "text": "Ethereum upgrade announcement with SEC approval",
    "base_score": 50,
}

score = scorer._calculate_kol_score(test_post)
print(f"Score: {score}")
```

### 檢查 Discord 嵌入格式

在 Discord 中手動發送測試嵌入：

```bash
# 使用 !crypto-pulse-now 命令
# 在 Discord 中輸入: !crypto-pulse-now
```

### 監控實時日誌

```bash
# 實時跟蹤日誌
tail -f logs/crypto_bot_$(date +%Y-%m-%d).log

# 搜索特定錯誤
grep -i "error\|warning" logs/crypto_bot_$(date +%Y-%m-%d).log

# 查看最後 50 行
tail -50 logs/crypto_bot_$(date +%Y-%m-%d).log
```

## 📊 性能監控

### 檢查執行時間

日誌中會記錄執行時間：

```bash
grep "successfully in" logs/crypto_bot_$(date +%Y-%m-%d).log
```

### 監控內存使用

```bash
# 在 Docker 中
docker stats crypto-morning-pulse-bot

# 在本地
ps aux | grep "src.main"
```

### 檢查緩存大小

```bash
# 查看緩存檔案大小
du -sh cache/

# 查看緩存內容
cat cache/content_cache.json | python3 -m json.tool
```

## 🆘 獲取幫助

如果以上解決方案都不能解決您的問題：

1. **檢查日誌**：查看 `logs/` 目錄中的完整日誌
2. **運行測試**：執行 `tests/test_scorer.py` 和 `tests/test_formatter.py`
3. **驗證配置**：確保所有環境變數都正確設置
4. **提交 Issue**：在 GitHub 上提交詳細的問題報告，包括：
   - 完整的錯誤訊息
   - 相關的日誌摘錄
   - 您的配置（不包括敏感信息）
   - 您的系統信息（OS、Python 版本等）

## 📚 其他資源

- [discord.py 文檔](https://discordpy.readthedocs.io/)
- [APScheduler 文檔](https://apscheduler.readthedocs.io/)
- [Nitter 實例列表](https://github.com/zedeus/nitter/wiki/Instances)
- [CryptoPanic API 文檔](https://cryptopanic.com/developers/api/)
- [CoinGecko API 文檔](https://www.coingecko.com/en/api)

---

**最後更新**：2025 年 1 月 8 日
