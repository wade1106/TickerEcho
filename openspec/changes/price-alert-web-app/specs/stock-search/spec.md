## ADDED Requirements

### Requirement: 依代碼或中文名稱搜尋台股
系統 SHALL 接受用戶輸入股票代碼（如 2330）或中文名稱（如 台積電），回傳匹配的股票清單，每筆包含代碼、中文名稱、即時報價與漲跌幅。

#### Scenario: 以股票代碼搜尋
- **WHEN** 用戶輸入 "2330"
- **THEN** 系統回傳台積電的資料，包含 ticker="2330.TW"、name="台積電"、price、change_percent

#### Scenario: 以中文名稱搜尋
- **WHEN** 用戶輸入 "台積電"
- **THEN** 系統回傳包含「台積電」的股票清單（最多 10 筆）

#### Scenario: 搜尋無結果
- **WHEN** 用戶輸入不存在的代碼或名稱
- **THEN** 系統回傳空陣列，不報錯

#### Scenario: 輸入少於 2 個字元
- **WHEN** 用戶輸入少於 2 個字元
- **THEN** 系統 SHALL 不發出查詢請求，回傳空結果

### Requirement: 股票代碼格式轉換
系統 SHALL 自動將用戶輸入的純數字代碼轉換為 yfinance 格式，上市股票加上 `.TW` 後綴，上櫃股票加上 `.TWO` 後綴。

#### Scenario: 上市股票代碼轉換
- **WHEN** 輸入代碼為上市股票（TWSE）
- **THEN** 系統將其轉換為 `<code>.TW` 格式供 yfinance 查詢

#### Scenario: 上櫃股票代碼轉換
- **WHEN** 輸入代碼為上櫃股票（TPEx）
- **THEN** 系統將其轉換為 `<code>.TWO` 格式供 yfinance 查詢
