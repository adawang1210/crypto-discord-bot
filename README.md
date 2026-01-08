# 🚀 Crypto Morning Pulse Discord Bot

一個自動化的 Discord 機器人，每天早上 09:00 UTC+8 發送加密貨幣市場簡報。該機器人從 X (Twitter) 的 Nitter 實例、CryptoPanic API 和多個新聞來源抓取數據，並通過智能評分系統篩選出最具影響力的市場動態。

## 📋 功能概述

該機器人實現了以下核心功能：

**內容策劃與來源整合**：機器人從六個不同的內容類別中精選信息，包括宏觀政策、資本流動、主要加密貨幣更新、新興代幣、技術敘述和關鍵意見領袖 (KOL) 的見解。系統優先使用 Nitter 實例抓取 X 上的實時討論，並通過 CryptoPanic 和 CoinGecko API 進行交叉驗證。

**智能評分系統**：每條內容都根據多維度評分標準進行評估，包括 KOL 層級（Tier 1-3）、內容關鍵字匹配、時間新鮮度和多源驗證。只有達到最低質量閾值的內容才會被發布。

**Nitter 實例輪詢**：系統維護多個 Nitter 實例的健康狀態，當某個實例返回 403 或 429 狀態碼時，自動標記為不健康並在 1 小時內跳過。

**內容去重與緩存**：機器人維護 7 天的發布內容緩存，使用關鍵字相似度匹配（60% 閾值）識別重複項目，確保內容多樣性。

**降級模式**：當數據源不足時，系統會以降級模式運行，發布至少 3 條高質量內容，並在 Discord 嵌入中添加警告標誌。

**健康檢查與監控**：每天 09:05 AM 發送狀態報告到管理員頻道，包括發布成功狀況、數據源響應情況、Nitter 實例健康狀態和執行時間。

## 🛠️ 技術棧

該項目使用以下技術和庫：

| 組件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 核心語言 |
| discord.py | 2.3.2 | Discord 機器人框架 |
| aiohttp | 3.9.1 | 異步 HTTP 請求 |
| BeautifulSoup4 | 4.12.2 | HTML 解析 |
| feedparser | 6.0.10 | RSS 源解析 |
| APScheduler | 3.10.4 | 任務排程 |
| python-dotenv | 1.0.0 | 環境變數管理 |

## 📦 項目結構

```
crypto-discord-bot/
├── src/
│   ├── __init__.py              # 包初始化
│   ├── main.py                  # 應用入口點
│   ├── bot.py                   # Discord 機器人主邏輯
│   ├── config.py                # 配置管理
│   ├── logger.py                # 日誌系統
│   ├── data_fetcher.py          # 數據抓取模組
│   ├── scorer.py                # 評分和過濾系統
│   └── formatter.py             # Discord 訊息格式化
├── tests/
│   ├── __init__.py
│   ├── test_scorer.py           # 評分系統單元測試
│   └── test_formatter.py        # 格式化系統單元測試
├── logs/                        # 日誌檔案目錄
├── cache/                       # 內容緩存目錄
├── requirements.txt             # Python 依賴
├── .env.example                 # 環境變數範本
├── Dockerfile                   # Docker 容器化配置
├── docker-compose.yml           # Docker Compose 配置
├── example_outputs.md           # 輸出範例文件
└── README.md                    # 本檔案
```

## 🚀 快速開始

### 前置要求

在開始之前，確保您擁有以下內容：

- Python 3.10 或更高版本
- Discord 伺服器和管理員權限
- Discord 機器人令牌（從 [Discord Developer Portal](https://discord.com/developers/applications) 獲取）
- 目標頻道 ID 和管理員頻道 ID

### 安裝步驟

**第 1 步：克隆或下載項目**

```bash
cd crypto-discord-bot
```

**第 2 步：建立虛擬環境**

```bash
python3 -m venv venv
source venv/bin/activate  # 在 Windows 上使用: venv\Scripts\activate
```

**第 3 步：安裝依賴**

```bash
pip install -r requirements.txt
```

**第 4 步：配置環境變數**

複製 `.env.example` 為 `.env` 並填入您的配置：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，設置以下必需的變數：

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
ADMIN_CHANNEL_ID=your_admin_channel_id_here
BOT_OWNER_ID=your_user_id_here
TIMEZONE=Asia/Taipei
```

可選的 API 金鑰：

```env
CRYPTOPANIC_API_KEY=your_key_here
COINGECKO_API_KEY=your_key_here
```

**第 5 步：運行機器人**

```bash
python3 -m src.main
```

機器人將連接到 Discord 並開始運行。您應該看到類似以下的日誌輸出：

```
2025-01-08 09:00:00 - crypto_bot - INFO - ============================================================
2025-01-08 09:00:00 - crypto_bot - INFO - 🚀 Crypto Morning Pulse Bot Starting
2025-01-08 09:00:00 - crypto_bot - INFO - ============================================================
2025-01-08 09:00:00 - crypto_bot - INFO - ✅ Configuration validated successfully
2025-01-08 09:00:01 - crypto_bot - INFO - Bot logged in as CryptoBot#1234
```

## 🧪 測試

該項目包含全面的單元測試，確保所有核心功能正常運行。

**運行所有測試**

```bash
source venv/bin/activate
python3 tests/test_scorer.py
python3 tests/test_formatter.py
```

**測試涵蓋的內容**

評分系統測試驗證 KOL 貼文評分、新聞質量評分、內容去重、分類邏輯和項目選擇。格式化系統測試驗證 Discord 嵌入創建、降級模式、健康檢查報告和 Markdown 格式化。

## 🐳 Docker 部署

該項目包含 Dockerfile 和 docker-compose.yml，用於容器化部署。

**使用 Docker Compose 運行**

```bash
docker-compose up -d
```

**手動構建和運行 Docker 容器**

```bash
docker build -t crypto-morning-pulse-bot .
docker run -d \
  -e DISCORD_BOT_TOKEN=your_token \
  -e DISCORD_CHANNEL_ID=your_channel_id \
  -e ADMIN_CHANNEL_ID=your_admin_channel_id \
  -e BOT_OWNER_ID=your_owner_id \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/cache:/app/cache \
  crypto-morning-pulse-bot
```

## 📋 環境變數說明

| 變數 | 說明 | 必需 | 預設值 |
|------|------|------|--------|
| `DISCORD_BOT_TOKEN` | Discord 機器人令牌 | ✅ | 無 |
| `DISCORD_CHANNEL_ID` | 發送簡報的頻道 ID | ✅ | 無 |
| `ADMIN_CHANNEL_ID` | 發送健康檢查的管理員頻道 ID | ✅ | 無 |
| `BOT_OWNER_ID` | 機器人擁有者的用戶 ID | ✅ | 無 |
| `TIMEZONE` | 時區設置 | ❌ | Asia/Taipei |
| `CRYPTOPANIC_API_KEY` | CryptoPanic API 金鑰 | ❌ | 無 |
| `COINGECKO_API_KEY` | CoinGecko API 金鑰 | ❌ | 無 |
| `NITTER_INSTANCES` | Nitter 實例列表 | ❌ | 預設實例 |
| `NITTER_REQUEST_DELAY` | Nitter 請求延遲（秒） | ❌ | 2.5 |
| `MIN_IMPACT_SCORE` | 新聞最低影響分數 | ❌ | 7 |
| `MIN_KOL_SCORE` | KOL 貼文最低分數 | ❌ | 60 |
| `LOG_LEVEL` | 日誌級別 | ❌ | INFO |

## 🎮 機器人命令

機器人支持以下管理員命令（僅限機器人擁有者）：

**手動觸發簡報**

```
!crypto-pulse-now
```

立即發送當天的簡報，無需等待排定時間。

**查看機器人狀態**

```
!crypto-pulse-status
```

顯示機器人的當前狀態，包括運行時間、最後發布時間和連續失敗次數。

**關閉機器人**

```
!crypto-pulse-shutdown
```

安全地關閉機器人。

## 📊 評分系統詳解

### KOL 貼文評分

KOL 貼文根據以下因素進行評分：

**基礎分數**：根據 KOL 層級分配
- Tier 1（全球思想領袖）：50 分
- Tier 2（行業分析師）：30 分
- Tier 3（地區影響者）：30 分

**內容關鍵字倍數**（可疊加）
- SEC/監管/訴訟：+15 分
- ETF/批准：+15 分
- 黑客/漏洞：+20 分
- 歷史高位/ATH：+10 分
- 價格目標：+10 分
- 合作/收購：+10 分
- 多個主要幣種提及：+5 分

**時間獎勵**
- 2 小時內發布：+15 分
- 6 小時內發布：+10 分
- 12 小時內發布：+5 分

**最低閾值**：60 分

### 新聞質量評分

新聞項目根據以下標準進行評分（0-10 分）：

- 多源驗證（3+ 來源）：+3 分
- 財務重要性（>$100M 或前 20 資產）：+2 分
- 官方來源：+3 分
- 網路效應（多平台趨勢）：+2 分

**最低閾值**：7 分

## 📝 日誌

機器人生成詳細的日誌，存儲在 `logs/` 目錄中，文件名格式為 `crypto_bot_YYYY-MM-DD.log`。

日誌條目包含：
- 時間戳
- 使用的數據源
- 抓取的項目數量
- 計算的影響分數
- 任何錯誤或觸發的回退

查看最新日誌：

```bash
tail -f logs/crypto_bot_$(date +%Y-%m-%d).log
```

## 🔧 故障排除

### 機器人無法連接到 Discord

**問題**：`discord.py` 報告連接錯誤

**解決方案**：
1. 驗證 `DISCORD_BOT_TOKEN` 是否正確
2. 確保機器人在 Discord 伺服器中有適當的權限
3. 檢查網絡連接

### Nitter 實例無法訪問

**問題**：所有 Nitter 實例都返回 403 或 429 錯誤

**解決方案**：
1. 檢查 `NITTER_INSTANCES` 配置中的實例是否可用
2. 增加 `NITTER_REQUEST_DELAY` 以減少速率限制
3. 嘗試添加新的 Nitter 實例到列表中

### 沒有足夠的內容項目

**問題**：機器人在降級模式下運行或完全跳過發布

**解決方案**：
1. 檢查 `MIN_IMPACT_SCORE` 和 `MIN_KOL_SCORE` 設置是否過高
2. 驗證 API 金鑰是否有效（CryptoPanic、CoinGecko）
3. 檢查日誌以查看具體的數據源故障

### 日誌文件權限錯誤

**問題**：無法寫入日誌檔案

**解決方案**：
```bash
chmod -R 755 logs/
chmod -R 755 cache/
```

## 📈 性能考慮

該機器人設計用於高效運行，具有以下性能特性：

- **執行時間**：目標在 5 分鐘內完成所有數據抓取和處理
- **內存使用**：目標 < 512MB RAM
- **並發請求**：最多 10 個並發連接
- **緩存管理**：7 天的滾動緩存，自動清理舊條目

## 🔐 安全建議

在生產環境中部署時，遵循以下安全最佳實踐：

1. **保護 Bot Token**：永遠不要將 `DISCORD_BOT_TOKEN` 提交到版本控制系統
2. **使用環境變數**：通過 `.env` 檔案或環境變數管理所有敏感信息
3. **限制權限**：確保機器人只有必要的 Discord 權限（發送訊息、嵌入鏈接）
4. **監控日誌**：定期檢查日誌以查找異常活動
5. **更新依賴**：定期更新 Python 依賴以修復安全漏洞

## 📚 API 參考

### DataFetcher 類

```python
async def fetch_all_kol_posts() -> List[Dict]:
    """從所有 KOL 帳戶抓取貼文"""

async def fetch_cryptopanic_news() -> List[Dict]:
    """從 CryptoPanic API 抓取新聞"""

async def fetch_all_data() -> Dict[str, List]:
    """從所有來源抓取數據"""
```

### ContentScorer 類

```python
def score_kol_posts(posts: List[Dict]) -> List[Dict]:
    """評分和過濾 KOL 貼文"""

def score_news_items(items: List[Dict]) -> List[Dict]:
    """評分和過濾新聞項目"""

def select_top_items(...) -> List[Dict]:
    """選擇多樣化的頂級項目"""
```

### DiscordFormatter 類

```python
@staticmethod
def create_daily_briefing_embed(items: List[Dict]) -> discord.Embed:
    """創建每日簡報嵌入"""

@staticmethod
def create_health_check_embed(...) -> discord.Embed:
    """創建健康檢查報告嵌入"""
```

## 🤝 貢獻

歡迎提交問題和改進建議。請確保任何新功能都包含相應的測試。

## 📄 許可證

本項目採用 MIT 許可證。詳見 LICENSE 檔案。

## 📞 支持

如有問題或需要幫助，請檢查 `TROUBLESHOOTING.md` 或提交 GitHub Issue。

---

**作者**：Manus AI  
**版本**：1.0.0  
**最後更新**：2025 年 1 月 8 日
