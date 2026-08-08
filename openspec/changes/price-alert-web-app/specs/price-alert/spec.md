## ADDED Requirements

### Requirement: 建立一或多筆股價警報
系統 SHALL 允許用戶一次建立一或多筆警報，每筆包含股票代碼、目標價格、條件（高於/低於）與通知 Email。

#### Scenario: 成功建立單筆警報
- **WHEN** 用戶提交包含一筆 { ticker, target_price, condition, user_email } 的陣列
- **THEN** 系統建立該警報，is_active=TRUE，回傳 201 與所建立的警報陣列

#### Scenario: 成功建立多筆警報
- **WHEN** 用戶提交包含多筆警報資料的陣列
- **THEN** 系統建立所有警報，回傳 201 與所有建立成功的警報陣列

#### Scenario: 同一支股票可設多個條件
- **WHEN** 用戶針對同一 ticker 提交「高於 1000」與「低於 850」兩筆
- **THEN** 系統建立兩筆獨立警報，各自輪詢與觸發

#### Scenario: 建立警報時缺少必填欄位
- **WHEN** 任一筆警報缺少 ticker 或 target_price
- **THEN** 系統回傳 422 Unprocessable Entity，不建立任何一筆

### Requirement: 查詢警報列表
系統 SHALL 提供所有警報的列表，包含 active 與已觸發的警報，依建立時間倒序排列。

#### Scenario: 取得警報列表
- **WHEN** 已登入用戶請求 GET /api/alerts
- **THEN** 系統回傳所有警報陣列，每筆包含 id、ticker、name、condition、target_price、is_active、triggered_at、created_at

### Requirement: 刪除警報
系統 SHALL 允許用戶刪除任一警報，無論其狀態為 active 或已觸發。

#### Scenario: 成功刪除警報
- **WHEN** 用戶請求 DELETE /api/alerts/{id}
- **THEN** 系統刪除該筆記錄，回傳 204 No Content

#### Scenario: 刪除不存在的警報
- **WHEN** 用戶請求刪除不存在的 id
- **THEN** 系統回傳 404 Not Found

### Requirement: 警報觸發後自動停用
警報觸發並發送通知後，系統 SHALL 將該警報標記為非 active（is_active=FALSE），不再輪詢，且不可自動重置。

#### Scenario: 警報觸發後狀態變更
- **WHEN** 輪詢偵測到股價符合警報條件
- **THEN** 系統設定 is_active=FALSE、triggered_at=當前時間，且後續輪詢不再檢查此警報
