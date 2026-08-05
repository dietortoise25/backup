# HIFOOD 認證模塊分析 與 GetSalesPriceList 實測報告

> 日期：2026-08-04 ｜ 測試賬號：HEBE.ZHENG（銷售權限）｜ 結果：✅ 全鏈路跑通

## 一、認證流程（反編譯自 `SJFOOD3.UI.Home.Login`）

系統有**兩條認證路徑**：

### 路徑 A：SJFood API 直接登入（實測使用，最簡單）
```
POST https://api-sjfood3.sjfood.us/api/De020_Login/Login
Content-Type: application/json

{"username": "<賬號>", "password": "<密碼>", "Comments": "<域賬號,可空>"}
```
- 回應：`{"token": "<JWT>", "expiration": "<UTC過期時間>"}`
- 失敗會自動重試 3 次；仍失敗則 fallback 到超級管理員（`LoginSpecial`，賬密存在 DB 的 special_config 表 `IS/SjfoodApiUserName`、`IS/SjfoodApiUserPassWord`）⚠️ 這是一個後門設計

### 路徑 B：Passport 統一認證（AS，單點登入用）
```
POST https://passport.sjfood.us/Token
Authorization: Basic <AsBaseBasic 解密後的值>
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=<賬號>&password=<密碼>
```
- 標準 OAuth2 password grant；`AsBaseBasic` 在 exe.config 中加密存儲（`CryptogramTool.Decryption(value, "IsSjfood")`）

### Token 使用方式
所有業務 API 統一帶 JWT：
```
Authorization: Bearer <SJToken>
```

## 二、JWT 結構（實測解碼）

```json
{
  "sub": "HEBE.ZHENG",
  "Username": "HEBE.ZHENG",
  "DepartmentName": "WXF承揽",
  "domainUser": "",
  "SalesGroup": "283",
  "jti": "a5c96f5a-...",
  "exp": 1786170612,
  "iss": "core",
  "aud": "SJFOOD_3.Api"
}
```
- HS256 簽名，有效期約 **3~4 天**（本次簽發 8/4 → 過期 8/8 UTC）
- 權限判斷依據：`SalesGroup`、`DepartmentName` 聲明，由 API 服務端校驗

## 三、實測結果

### Step 1：登入 ✅
```
POST /api/De020_Login/Login → HTTP 200
token: eyJhbGciOiJIUzI1NiIs...（JWT）
expiration: 2026-08-08T06:31:26Z
```

### Step 2：調用價目 API ✅
```
GET /api/Price/GetSalesPriceList?SearchKey=&Material=&Limit=5&PreSalesOff=false
Authorization: Bearer <token>
→ HTTP 200，返回 5 筆真實物料價目
```

返回樣例（真實生產數據）：
| 物料號 | 描述 | 單位 | 工廠 |
|---|---|---|---|
| 000000000010011899 | (Party) Wings·PG·#40·中錘翼 | LB | 100B |
| 000000000040052278 | H/ON·Champmar·40/50·#24·有頭蝦 | LB | 100B |
| 000000000040052299 | H/ON·Champmar·30/40·#24·有頭蝦 | LB | 100B |
| 000000000040052366 | H/ON·Champmar·50/60·#24·有頭蝦 | LB | 100B |
| 30031642CWR | R/T (Light Sparerib) Side Rib·CBCO·CW·燒 | LB | 100A |

> 注意：回應 JSON 欄位為**小寫**（`data`、`matnr`、`priceinfo`），與 C# DTO 的 PascalCase 不同（服務端用了 camelCase 序列化）。空 SearchKey 時按 Limit 返回熱門物料。

## 四、可復用的調用模板

```python
import requests
s = requests.Session()
login = s.post("https://api-sjfood3.sjfood.us/api/De020_Login/Login",
               json={"username": "...", "password": "...", "Comments": ""}).json()
headers = {"Authorization": "Bearer " + login["token"]}
# 之後任意 API：
s.get("https://api-sjfood3.sjfood.us/api/Price/GetSalesPriceList",
      params={"SearchKey": "", "Material": "", "Limit": 5, "PreSalesOff": "false"},
      headers=headers)
```

測試腳本：`hifood/test_price_api.py`（可重複使用）
完整回應樣本：`hifood/price_api_result.json`

## 五、安全觀察（建議回報開發團隊）

1. **後門賬號**：`LoginSpecial` 超管賬密存在 DB 配置表，客戶端登入失敗 3 次會自動用超管登入——任何能運行客戶端的人實質上擁有超管 API 權限
2. **JWT 有效期過長**（3~4 天）且無刷新機制
3. **密碼明文傳輸**（雖走 HTTPS，但無客戶端加密/防重放）
4. exe.config 中 FTP 密碼明文（前次已發現）
