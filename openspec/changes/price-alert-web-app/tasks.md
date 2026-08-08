## 1. 專案初始化

- [x] 1.1 建立專案目錄結構：`backend/`、`frontend/`、`data/`
- [x] 1.2 建立 `docker-compose.yml`（單一服務，port 8888；掛載 `./data:/app/data` volume 確保 SQLite 資料在 container 重啟後不遺失）
- [x] 1.3 建立 `Dockerfile`（多階段：Node build Vue → Python FastAPI）
- [x] 1.4 建立 `.env.example`，包含所有必要環境變數（APP_USERNAME、APP_PASSWORD、JWT_SECRET、MAIL_*、LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET、POLL_INTERVAL_MINUTES）
- [x] 1.5 建立 `.gitignore`（排除 .env、data/、__pycache__、node_modules、dist）

## 2. 後端基礎建設

- [x] 2.1 建立 `backend/requirements.txt`（fastapi、uvicorn、sqlmodel、python-jose、passlib、fastapi-mail、line-bot-sdk、yfinance、twstock、apscheduler）
- [x] 2.2 建立 `backend/main.py`：FastAPI app 初始化、掛載靜態檔案（`/`）、包含 API router（`/api`）、lifespan 管理
- [x] 2.3 建立 `backend/database.py`：SQLite 連線設定（SQLModel）；實作 `init_db()` 函式，呼叫 `SQLModel.metadata.create_all()` 建立所有資料表（冪等，每次啟動都執行，需在 FastAPI lifespan 的第一步呼叫，早於 scheduler 啟動）
- [x] 2.4 建立 `backend/models.py`：Alert 與 LineSubscriber 兩個 SQLModel 資料模型（Alert: id、user_email、ticker、name、condition、target_price、is_active、triggered_at、created_at；LineSubscriber: id、line_user_id、display_name、created_at）
- [x] 2.5 建立 `backend/config.py`：從 `.env` 讀取所有設定值

## 3. 認證模組（auth）

- [x] 3.1 建立 `backend/routers/auth.py`：`POST /api/auth/login` 端點，比對 .env 帳密，回傳 JWT
- [x] 3.2 建立 `backend/auth.py`：JWT 產生與驗證工具函式（python-jose），token 有效期 7 天
- [x] 3.3 建立 FastAPI dependency `get_current_user`，驗證 Bearer token，無效時回傳 401
- [x] 3.4 在所有受保護路由套用 `get_current_user` dependency

## 4. 股票搜尋模組（stock-search）

- [x] 4.1 建立 `backend/stock_data.py`：載入 twstock 股票清單，建立代碼→中文名稱對照表，區分上市（.TW）與上櫃（.TWO）
- [x] 4.2 實作搜尋函式：接受關鍵字，回傳匹配的股票清單（代碼、名稱）
- [x] 4.3 建立 `backend/routers/stocks.py`：`GET /api/stocks/search?q=<keyword>` 端點，回傳最多 10 筆結果
- [x] 4.4 實作 `GET /api/stocks/{ticker}/price` 端點：用 yfinance 查詢即時報價（price、change_percent）

## 5. K 線圖模組（stock-chart）

- [x] 5.1 實作 `GET /api/stocks/{ticker}/chart?period=3mo` 端點：用 yfinance 取得 OHLCV 歷史資料
- [x] 5.2 將 yfinance 回傳的 DataFrame 轉換為前端所需格式（time、open、high、low、close、volume 陣列）
- [x] 5.3 驗證 period 參數只接受 1mo/3mo/6mo/1y，其他回傳 422

## 6. 警報 CRUD 模組（price-alert）

- [x] 6.1 建立 `backend/routers/alerts.py`：定義 AlertCreate Pydantic schema（ticker、target_price、condition、user_email）
- [x] 6.2 實作 `POST /api/alerts` 端點：接受陣列，一次建立一或多筆警報，回傳 201 與警報陣列
- [x] 6.3 實作 `GET /api/alerts` 端點：回傳所有警報，依 created_at 倒序排列
- [x] 6.4 實作 `DELETE /api/alerts/{id}` 端點：刪除指定警報，不存在回傳 404

## 7. 輪詢與通知模組（price-polling + alert-notification）

- [x] 7.1 建立 `backend/scheduler.py`：初始化 APScheduler BackgroundScheduler
- [x] 7.2 實作盤中時間判斷函式（週一至週五 09:00–13:30 台北時間）
- [x] 7.3 實作 `check_alerts()` 輪詢函式：取得 active 警報 → 批次查詢股價 → 比對條件
- [x] 7.4 建立 `backend/notifier.py`：實作 Email 通知（fastapi-mail）與 LINE 通知（line-bot-sdk multicast 至所有 line_subscribers）兩個獨立函式，內容包含股票名稱、代碼、條件、目標價、當前價
- [x] 7.5 在 `backend/config.py` 加入通知管道偵測邏輯：啟動時檢查 SMTP 與 LINE 設定是否完整，記錄 warning 若任一未設定
- [x] 7.6 在 `check_alerts()` 中：觸發警報時依設定同時呼叫 Email/LINE notifier（獨立 try/except），更新 is_active=FALSE 與 triggered_at
- [x] 7.7 捕捉輪詢例外（yfinance 失敗），記錄 log 後繼續排程，不中斷服務
- [x] 7.8 在 FastAPI lifespan 啟動時初始化 scheduler，從 .env 讀取 POLL_INTERVAL_MINUTES（預設 5）

## 8. LINE Webhook 訂閱者管理

- [x] 8.1 建立 `backend/routers/line_webhook.py`：`POST /api/line/webhook` 端點（不需 JWT，供 LINE 伺服器呼叫）
- [x] 8.2 實作 LINE Signature 驗證：用 `LINE_CHANNEL_SECRET` 驗證每個 Webhook 請求的 `X-Line-Signature` header，驗證失敗回傳 400
- [x] 8.3 處理 follow 事件：將 `event.source.userId` 與 `display_name` 寫入 `line_subscribers`（若已存在則跳過）
- [x] 8.4 處理 unfollow 事件：從 `line_subscribers` 刪除對應的 `line_user_id`
- [x] 8.5 在 LINE Developers Console 設定 Webhook URL 為 `https://<tunnel網址>/api/line/webhook` 並啟用 Webhook（部署後手動操作，記錄於 README）

## 9. 前端初始化（Vue 3）

- [x] 9.1 建立 `frontend/`：用 `npm create vue@latest` 初始化 Vue 3 + Vite + TypeScript 專案
- [x] 9.2 安裝依賴：pinia、vue-router、axios、lightweight-charts
- [x] 9.3 設定 Vite proxy（開發模式下 `/api` → `http://localhost:8888`）
- [x] 9.4 建立 axios instance（`src/api/client.ts`）：設定 baseURL、自動帶入 Authorization header、攔截 401 並導向登入

## 10. 前端認證（auth）

- [x] 10.1 建立 `src/stores/auth.ts`（Pinia）：管理 token 狀態、login/logout action
- [x] 10.2 建立 `src/views/LoginView.vue`：帳密表單、呼叫 `POST /api/auth/login`、儲存 token 至 localStorage
- [x] 10.3 設定 Vue Router：定義 /login（公開）與其他路由（需登入）
- [x] 10.4 實作 Navigation Guard：未登入時導向 /login

## 11. 前端主要頁面

- [x] 11.1 建立 `src/views/DashboardView.vue`：警報列表、顯示 ticker/name/condition/target_price/狀態/triggered_at
- [x] 11.2 建立新增警報元件（`src/components/AddAlertForm.vue`）：股票搜尋 input（debounce）、搜尋結果下拉選單、條件與目標價設定、支援逐筆新增
- [x] 11.3 實作刪除警報功能（呼叫 DELETE /api/alerts/{id}，更新列表）
- [x] 11.4 建立 `src/views/ChartView.vue`：整合 TradingView Lightweight Charts，顯示 K 線圖與成交量
- [x] 11.5 實作時間範圍切換（1M/3M/6M/1Y）並重新載入圖表資料

## 12. Docker 整合與部署

- [x] 12.1 撰寫多階段 Dockerfile：第一階段 Node 建置 Vue（`npm run build`），第二階段 Python 複製 dist 至 FastAPI static 目錄
- [x] 12.2 確認 FastAPI `StaticFiles` 掛載路徑與 Dockerfile 複製路徑一致
- [ ] 12.3 本地執行 `docker compose up --build`，驗證 http://localhost:8888 可正常存取前端與 API
- [x] 12.4 撰寫部署說明（README.md）：.env 設定、Docker 啟動、Cloudflare Tunnel 設定、LINE Webhook URL 設定步驟
