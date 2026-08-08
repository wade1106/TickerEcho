## ADDED Requirements

### Requirement: 顯示台股 K 線圖
系統 SHALL 提供股票的日 K 線圖，使用 TradingView Lightweight Charts 在前端渲染，資料來源為 yfinance 歷史 OHLCV 資料，預設顯示近 3 個月。

#### Scenario: 查看股票 K 線圖
- **WHEN** 用戶點擊某支股票的「查看圖表」
- **THEN** 前端顯示該股票近 3 個月的日 K 線圖，包含開高低收與成交量

#### Scenario: 切換時間範圍
- **WHEN** 用戶選擇 1M / 3M / 6M / 1Y
- **THEN** 圖表更新為對應時間範圍的 K 線資料

#### Scenario: 股票無歷史資料
- **WHEN** yfinance 無法取得該股票的歷史資料
- **THEN** 系統回傳空陣列，前端顯示「無可用資料」提示

### Requirement: K 線圖資料由後端提供
後端 SHALL 提供 `GET /api/stocks/{ticker}/chart` 端點，接受 `period` 參數（1mo/3mo/6mo/1y），回傳 OHLCV 陣列供前端渲染。

#### Scenario: 取得 K 線資料
- **WHEN** 請求 GET /api/stocks/2330.TW/chart?period=3mo
- **THEN** 系統回傳 JSON 陣列，每筆包含 time、open、high、low、close、volume

#### Scenario: 不支援的 period 參數
- **WHEN** 請求的 period 不在允許值（1mo/3mo/6mo/1y）內
- **THEN** 系統回傳 422 Unprocessable Entity
