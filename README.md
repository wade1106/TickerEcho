# TickerEcho

台股股價警報 Web App。設定目標價，觸發時發送 Email 與 LINE 通知。

## 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`，填入：

| 變數 | 說明 |
|------|------|
| `APP_USERNAME` | 登入帳號 |
| `APP_PASSWORD` | 登入密碼 |
| `JWT_SECRET` | 隨機字串（用於簽發 token） |
| `MAIL_SERVER` | SMTP 伺服器（例如 smtp.gmail.com） |
| `MAIL_PORT` | SMTP 埠（Gmail 用 587） |
| `MAIL_USERNAME` | 寄件 Email |
| `MAIL_PASSWORD` | Email 應用程式密碼 |
| `MAIL_FROM` | 寄件者顯示地址 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API Channel Access Token |
| `LINE_CHANNEL_SECRET` | LINE Messaging API Channel Secret |
| `POLL_INTERVAL_MINUTES` | 輪詢間隔（分鐘），預設 5 |

> Email 與 LINE 設定皆為選填，未設定的管道會自動停用，不影響另一管道。

### 2. 部署（Docker）

```bash
docker compose up --build -d
```

服務啟動於 `http://localhost:8888`。

### 3. 設定 Cloudflare Tunnel

1. 安裝並登入 cloudflared
2. 建立 Tunnel，指向 `http://localhost:8888`
3. 記下你的 Tunnel URL（例如 `https://tickerecho.example.com`）

### 4. 設定 LINE Webhook

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 找到你的 Channel → Messaging API
3. 將 Webhook URL 設為：`https://<你的Tunnel網址>/api/line/webhook`
4. 啟用 Webhook
5. 用手機加 Bot 好友，即自動訂閱 LINE 通知；封鎖 Bot 則自動取消訂閱

---

## 開發模式

### 後端

```bash
cd backend
uv venv --python 3.12
uv pip install -r requirements.txt
cp ../.env.example ../.env   # 填入設定
uv run uvicorn main:app --reload --port 8888
```

### 前端

```bash
cd frontend
npm install
npm run dev   # 開啟於 http://localhost:5173，/api 自動 proxy 至 8888
```

---

## 注意事項

- 股價資料來源為 yfinance，有約 15 分鐘延遲
- 輪詢僅在台股交易時間（週一至週五 09:00–13:30 台北時間）執行
- 警報觸發後自動停用（one-shot），不會重複通知
- SQLite 資料庫存於 `./data/tickerecho.db`，Docker volume 掛載確保重啟不遺失
