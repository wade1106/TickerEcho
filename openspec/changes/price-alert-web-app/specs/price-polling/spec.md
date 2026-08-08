## ADDED Requirements

### Requirement: 盤中定時輪詢股價
系統 SHALL 在台股交易時間（週一至週五 09:00–13:30 台北時間）以可設定的間隔輪詢所有 active 警報的股價，並與目標條件比對。

#### Scenario: 盤中輪詢正常執行
- **WHEN** 當前時間為台股交易時間內
- **THEN** scheduler 每隔 POLL_INTERVAL_MINUTES 分鐘取得所有 is_active=TRUE 的警報，批次查詢其股價，比對條件

#### Scenario: 盤外不執行輪詢
- **WHEN** 當前時間為非交易時間（盤後、假日、週末）
- **THEN** scheduler 跳過本次輪詢，不查詢 yfinance

#### Scenario: 無 active 警報
- **WHEN** 輪詢時 is_active=TRUE 的警報數量為 0
- **THEN** 系統跳過 yfinance 查詢，不產生不必要的 API 呼叫

### Requirement: 輪詢間隔可透過環境變數設定
系統 SHALL 從 `.env` 的 `POLL_INTERVAL_MINUTES` 讀取輪詢間隔，預設值為 5 分鐘。

#### Scenario: 自訂輪詢間隔
- **WHEN** .env 設定 POLL_INTERVAL_MINUTES=1
- **THEN** scheduler 每 1 分鐘執行一次輪詢

#### Scenario: 未設定時使用預設值
- **WHEN** .env 未設定 POLL_INTERVAL_MINUTES
- **THEN** scheduler 使用預設值 5 分鐘

### Requirement: 輪詢錯誤不中斷服務
系統 SHALL 在單次輪詢發生例外（如 yfinance 無回應）時，記錄錯誤 log 並繼續下一輪排程，不終止 scheduler。

#### Scenario: yfinance 查詢失敗
- **WHEN** yfinance 回傳錯誤或逾時
- **THEN** 系統捕捉例外、記錄 log，該輪詢結束，不觸發任何警報，不影響下一次輪詢
