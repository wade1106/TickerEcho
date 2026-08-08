## Context

TickerEcho 是一個自託管的台股股價警報 Web App，供 1-2 位個人用戶使用。服務透過 Cloudflare Tunnel 對外公開，部署在本地機器上。目前無任何既有程式碼，從零開始建立。

系統需在台股盤中定時輪詢股價、比對警報條件，並在觸達目標價時發送 Email 與 LINE 通知。LINE 訂閱者透過加/封鎖 Bot 好友自動管理，不需要任何 UI 操作。

## Goals / Non-Goals

**Goals:**
- 單一 port（8888）提供前端靜態檔與 API，簡化部署
- 台股股價輪詢間隔可透過 `.env` 設定，預設 5 分鐘
- 警報觸發後自動停止監控（one-shot 設計）
- 固定帳密 JWT 登入，不需要用戶資料表
- Docker Compose 一鍵部署

**Non-Goals:**
- 多用戶管理、權限系統
- 即時 WebSocket 股價推播（輪詢已足夠）
- 美股或其他市場支援
- 技術指標（MA/RSI/MACD）與分價圖（第二版）
- 行動 App

## Decisions

### 1. FastAPI 同時服務 API 與 Vue 靜態檔

**決定**：Vue build 後的靜態檔由 FastAPI `StaticFiles` 掛載於 `/`，API 路由前綴為 `/api`。

**理由**：單一 port 讓 Cloudflare Tunnel 設定最簡單，不需要 nginx 反代兩個服務，也不存在 CORS 問題。

**替代方案**：nginx 反代前端 + 後端 → 增加部署複雜度，對 1-2 人使用規模不值得。

---

### 2. APScheduler 內嵌於 FastAPI（非獨立 worker）

**決定**：使用 `APScheduler` 的 `BackgroundScheduler`，在 FastAPI lifespan 啟動時初始化，與主程序同一個 process 運行。

**理由**：省去 Celery + Redis 的部署複雜度。1-2 人使用、最多數十筆警報，單 process 輪詢完全足夠。

**輪詢頻率**：從 `.env` 讀取 `POLL_INTERVAL_MINUTES`，預設 5。盤中時間（09:00–13:30 週一至五）才執行，其餘時間 scheduler 仍運行但跳過輪詢。

**替代方案**：Celery Beat → 需要 Redis，過度設計。

---

### 3. 資料來源：yfinance + twstock

**決定**：
- 股價查詢：`yfinance`，台股代碼格式 `2330.TW`（上市）/ `6669.TWO`（上櫃）
- 中文名稱搜尋：`twstock` 的股票清單作為查詢索引

**理由**：yfinance 免費、Python 生態成熟、支援歷史 OHLCV 資料（K 線圖用）。twstock 補足中文名稱對應，讓用戶可以輸入「台積電」查詢。

**限制**：yfinance 有 15 分鐘延遲，個人警報用途可接受。

---

### 4. 認證：固定帳密 + JWT

**決定**：
- `POST /api/auth/login` 接受 `username` / `password`，與 `.env` 中 `APP_USERNAME` / `APP_PASSWORD` 比對
- 驗證通過後回傳 JWT（`python-jose` 簽發，`JWT_SECRET` 從 `.env` 讀取）
- 前端將 token 存於 `localStorage`，每次 API request 帶 `Authorization: Bearer <token>`
- 沒有 refresh token，token 有效期 7 天

**理由**：不需要資料庫用戶表，簡單到最低限度，對 1-2 人使用足夠。

---

### 5. 資料庫：SQLite + SQLModel

**決定**：使用 SQLite 儲存警報資料，ORM 使用 `SQLModel`（FastAPI 作者開發，整合 Pydantic + SQLAlchemy）。

**資料表**：`alerts` + `line_subscribers` 兩張表。

```
alerts
├── id            INTEGER PRIMARY KEY
├── user_email    TEXT NOT NULL
├── ticker        TEXT NOT NULL       -- e.g. "2330.TW"
├── name          TEXT NOT NULL       -- e.g. "台積電"
├── condition     TEXT NOT NULL       -- "above" | "below"
├── target_price  REAL NOT NULL
├── is_active     BOOLEAN DEFAULT TRUE
├── triggered_at  DATETIME NULL
└── created_at    DATETIME DEFAULT NOW

line_subscribers
├── id            INTEGER PRIMARY KEY
├── line_user_id  TEXT NOT NULL UNIQUE  -- Uxxxxxxxxx
├── display_name  TEXT                  -- LINE 顯示名稱（選填）
└── created_at    DATETIME DEFAULT NOW
```

**替代方案**：PostgreSQL → 過度設計，SQLite 對此規模完全足夠。

---

### 6. 通知管道：Email + LINE，雙管道獨立運作

**決定**：支援 Email（`fastapi-mail`）與 LINE Messaging API（`line-bot-sdk`）兩個通知管道，各自獨立，依 `.env` 設定決定啟用哪些。

- **Email**：SMTP 設定從 `.env` 讀取，發送至警報的 `user_email`
- **LINE**：Channel Access Token 從 `.env` 讀取（`LINE_CHANNEL_ACCESS_TOKEN`），發送對象為 `line_subscribers` 表中所有訂閱者（multicast）

**通知邏輯**：啟動時偵測各管道設定是否完整，未設定的記錄 warning 並跳過。警報觸發時兩個管道用獨立 `try/except` 執行，任一失敗不影響另一個。

警報觸發後：
1. 同時呼叫已啟用的通知管道（Email / LINE multicast）
2. 更新 `alerts.is_active = FALSE`、`triggered_at = now()`

---

### 7. LINE 訂閱者管理：Webhook follow/unfollow 自動化

**決定**：透過 LINE Webhook 自動管理訂閱者，不需要任何 UI 或指令操作。

```
用戶加 Bot 好友  → follow 事件  → 寫入 line_subscribers
用戶封鎖/刪除 Bot → unfollow 事件 → 從 line_subscribers 刪除
```

**Webhook 端點**：`POST /api/line/webhook`，不需要 JWT 保護（LINE 伺服器呼叫），但需驗證 LINE 的 `X-Line-Signature` header 確保請求來自 LINE。

**為何不用 broadcast**：broadcast 傳給所有好友，無法區分是否真的想收通知。follow/unfollow 事件讓訂閱行為更明確，且 LINE 已有這個機制，實作成本低。

**Cloudflare Tunnel 的角色**：LINE 伺服器需要公開 HTTPS URL 才能呼叫 Webhook，Cloudflare Tunnel 提供這個能力，不需要額外設定。

---

### 8. 前端：Vue 3 + Vite + Pinia + TradingView Lightweight Charts

**決定**：
- 狀態管理：`Pinia`
- K 線圖：`lightweight-charts`（TradingView 開源版，免費）
- HTTP client：`axios`
- UI：`naive-ui` 或純 CSS（待定，偏向輕量）

## Risks / Trade-offs

| 風險 | 說明 | 緩解措施 |
|------|------|----------|
| yfinance 資料延遲 15 分鐘 | 警報觸發時機可能落後實際成交 | 文件說明此限制，個人使用可接受 |
| yfinance API 不穩定 | 偶爾因 Yahoo Finance 變更而失效 | 捕捉 exception，記錄 log，不中斷 scheduler |
| APScheduler 與 FastAPI 同 process | 輪詢阻塞時可能影響 API 響應 | 股票數量少（個人用），實際影響微乎其微 |
| SQLite 無法多 process 寫入 | Docker Compose 若擴展為多 replica 會有問題 | 此場景不在 scope，單一 container 即可 |
| JWT 存於 localStorage | XSS 風險 | 個人自託管 App，風險可接受；httpOnly cookie 為未來改進方向 |
| LINE Webhook 簽章驗證失敗 | 若 Channel Secret 設定錯誤，所有 follow/unfollow 事件會被拒絕 | 啟動時記錄 log 確認設定，提供明確錯誤訊息 |
| LINE multicast 上限 | 免費方案每月有訊息則數限制 | 個人用量遠低於限制，可接受 |

## Migration Plan

1. `git clone` 專案
2. 複製 `.env.example` 為 `.env`，填入 SMTP 設定、帳密、LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET
3. `docker compose up -d`
4. 設定 Cloudflare Tunnel 指向 `localhost:8888`
5. 在 LINE Developers Console 將 Webhook URL 設為 `https://<tunnel網址>/api/line/webhook`，啟用 Webhook
6. 瀏覽器開啟 Tunnel URL，登入即可使用
7. 用手機加 Bot 好友即自動訂閱 LINE 通知

**Rollback**：`docker compose down`，無資料庫遷移問題（SQLite 檔案保留於 `./data/`）。

## Open Questions

- 前端 UI library 選擇：naive-ui vs. 純 Tailwind CSS？（偏向 Tailwind，減少依賴）
- twstock 上市/上櫃代碼格式轉換邏輯是否需要手動維護清單？
