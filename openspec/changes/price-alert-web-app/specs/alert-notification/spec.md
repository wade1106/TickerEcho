## ADDED Requirements

### Requirement: 警報觸發時發送 Email 通知
系統 SHALL 在股價警報條件觸達時，向警報記錄的 user_email 發送 Email，內容包含股票名稱、代碼、觸發價格與目標條件。

#### Scenario: 成功發送通知 Email
- **WHEN** 輪詢偵測到股價符合警報條件且 SMTP 已設定
- **THEN** 系統發送 Email 至 user_email，主旨包含股票名稱與「已達目標價」，內文包含 ticker、name、condition、target_price、current_price、triggered_at

#### Scenario: Email 發送失敗
- **WHEN** SMTP 連線失敗或發送逾時
- **THEN** 系統記錄錯誤 log，但仍將警報標記為已觸發（is_active=FALSE），不重試

### Requirement: SMTP 設定可透過環境變數配置
系統 SHALL 從 `.env` 讀取 SMTP 連線設定，不將任何憑證寫死於程式碼中。

#### Scenario: 使用 Gmail SMTP
- **WHEN** .env 設定 MAIL_SERVER=smtp.gmail.com、MAIL_PORT=587、MAIL_USERNAME、MAIL_PASSWORD
- **THEN** 系統使用 TLS 連線 Gmail SMTP 發送 Email

#### Scenario: 缺少 SMTP 設定
- **WHEN** .env 缺少 MAIL_USERNAME 或 MAIL_PASSWORD
- **THEN** 系統在啟動時記錄 warning，Email 通知停用，輪詢與 LINE 通知仍正常運作

### Requirement: 警報觸發時發送 LINE 通知
系統 SHALL 在股價警報條件觸達時，透過 LINE Messaging API 向設定的 LINE User ID 推播通知，內容與 Email 一致。

#### Scenario: 成功發送 LINE 推播
- **WHEN** 輪詢偵測到股價符合警報條件且 LINE 已設定
- **THEN** 系統呼叫 LINE push_message，發送包含股票名稱、代碼、條件、目標價、當前價的文字訊息至 LINE_USER_ID

#### Scenario: LINE 發送失敗
- **WHEN** LINE API 回傳錯誤或連線逾時
- **THEN** 系統記錄錯誤 log，仍將警報標記為已觸發（is_active=FALSE），不重試

### Requirement: LINE Messaging API 設定可透過環境變數配置
系統 SHALL 從 `.env` 讀取 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_USER_ID，不將任何憑證寫死於程式碼中。

#### Scenario: LINE 設定完整
- **WHEN** .env 設定 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_USER_ID
- **THEN** 系統在警報觸發時呼叫 LINE Messaging API 發送推播

#### Scenario: 缺少 LINE 設定
- **WHEN** .env 缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID
- **THEN** 系統在啟動時記錄 warning，LINE 通知停用，Email 通知仍正常運作

### Requirement: 雙管道同時通知
系統 SHALL 在警報觸發時，依據 .env 設定同時發送所有已啟用的通知管道（Email、LINE），兩者獨立執行，互不影響。

#### Scenario: Email 與 LINE 皆已設定
- **WHEN** 警報觸發，且 Email 與 LINE 設定皆完整
- **THEN** 系統同時發送 Email 與 LINE 通知，任一管道失敗不影響另一管道

#### Scenario: 僅 Email 已設定
- **WHEN** 警報觸發，.env 只有 SMTP 設定
- **THEN** 系統僅發送 Email 通知

#### Scenario: 僅 LINE 已設定
- **WHEN** 警報觸發，.env 只有 LINE 設定
- **THEN** 系統僅發送 LINE 通知
