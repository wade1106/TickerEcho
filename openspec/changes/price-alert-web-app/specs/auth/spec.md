## ADDED Requirements

### Requirement: 固定帳密登入取得 JWT
系統 SHALL 提供登入端點，接受 username 與 password，與 `.env` 中的 APP_USERNAME / APP_PASSWORD 比對，驗證通過後回傳 JWT token。

#### Scenario: 登入成功
- **WHEN** 用戶提交正確的 username 與 password
- **THEN** 系統回傳 { access_token, token_type: "bearer" }，token 有效期 7 天

#### Scenario: 登入失敗（帳密錯誤）
- **WHEN** 用戶提交錯誤的 username 或 password
- **THEN** 系統回傳 401 Unauthorized，不揭露是哪個欄位錯誤

### Requirement: JWT 保護所有 API 端點
除登入端點外，所有 `/api/*` 端點 SHALL 要求有效的 Bearer token，無效或過期的 token 回傳 401。

#### Scenario: 攜帶有效 token 的請求
- **WHEN** 請求 header 包含有效的 Authorization: Bearer <token>
- **THEN** 系統正常處理請求

#### Scenario: 無 token 的請求
- **WHEN** 請求未包含 Authorization header
- **THEN** 系統回傳 401 Unauthorized

#### Scenario: Token 過期
- **WHEN** 請求攜帶已過期的 token
- **THEN** 系統回傳 401 Unauthorized

### Requirement: 前端未登入時導向登入頁
前端 SHALL 在未持有 token 或收到 401 響應時，自動導向登入頁面。

#### Scenario: 未登入訪問受保護頁面
- **WHEN** 用戶直接訪問 Dashboard 等頁面但無 token
- **THEN** 前端自動導向 /login

#### Scenario: Token 過期後的 API 請求
- **WHEN** 前端發出 API 請求收到 401 響應
- **THEN** 前端清除 localStorage 的 token 並導向 /login
