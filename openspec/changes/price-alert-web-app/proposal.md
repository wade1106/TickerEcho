## Why

個人需要一個能即時監控台股股價並在觸達目標價位時發送通知的工具，現有解決方案不是功能過於複雜就是無法自訂部署環境。TickerEcho 旨在提供一個輕量、自託管、可從外部存取的股價警報 Web App。

## What Changes

- 全新建立 Vue 3 前端，提供股票搜尋、警報設定與 K 線圖介面
- 全新建立 FastAPI 後端，統一從 port 8888 提供 API 與靜態前端檔案
- 整合 yfinance（台股資料）與 twstock（中文名稱查詢）作為資料來源
- 內嵌 APScheduler，台股盤中（09:00–13:30 週一至週五）每 5 分鐘輪詢一次
- 警報觸發後同時發送 Email 與 LINE 通知，並自動停止該警報監控
- 固定帳密 JWT 登入（credentials 儲存於 .env），不設用戶資料表
- SQLite 儲存警報資料，適合個人使用規模
- Docker Compose 打包，搭配 Cloudflare Tunnel 對外公開服務

## Capabilities

### New Capabilities

- `stock-search`: 依代碼（2330.TW）或中文名稱搜尋台股，回傳即時報價與基本資訊
- `price-alert`: 建立、查詢、刪除股價警報（高於/低於目標價），觸發後停止監控
- `alert-notification`: 警報觸發時同時發送 Email 與 LINE 通知（依 .env 設定決定啟用哪些管道）
- `price-polling`: 盤中定時輪詢所有 active 警報的股價
- `auth`: 固定帳密 JWT 登入機制，credentials 從 .env 讀取
- `stock-chart`: 顯示台股 K 線圖（TradingView Lightweight Charts）

### Modified Capabilities

## Impact

- 新增 Python 依賴：fastapi, uvicorn, yfinance, twstock, apscheduler, fastapi-mail, line-bot-sdk, sqlmodel, python-jose
- 新增 Node.js 依賴：vue 3, vite, pinia, lightweight-charts
- 部署：Docker Compose（單一容器），Cloudflare Tunnel 指向 localhost:8888
- 資料：SQLite 檔案持久化於 `./data/` 目錄
