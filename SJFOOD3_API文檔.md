# SJFOOD 3.0 API 文檔

> 版本：基於 HIFOOD 1.0 PRD v2026.1.1.57 反編譯整理 + 生產環境實測驗證
> 整理日期：2026-08-04
> 涵蓋範圍：認證模塊、SD080 價錢表、SD170 出貨記錄

---

## 1. 總覽

| 項目 | 值 |
|---|---|
| API Base URL | `https://api-sjfood3.sjfood.us` |
| 認證方式 | JWT Bearer Token（HS256） |
| 數據格式 | JSON（**回應欄位為小寫/camelCase**，與 C# DTO PascalCase 不同） |
| 字符編碼 | UTF-8 |
| 客戶端緩存 | 價目類查詢 1~20 分鐘（服務端另有 cacheDateTime） |
| 重試機制 | 客戶端 Polly 重試（GetSalesPriceList 超時 30s，分頁查詢 30min） |

### 通用約定

1. **SAP 物料號（MATNR）**：`Material` 參數必須為 **18 位補零**格式（如 `000000000040052897`）；`SearchKey` 參數可用原始短號（如 `40052897`）
2. **SAP 客戶號（KUNNR）**：`CustomerIds` 參數必須為 **10 位補零**格式（如 `0000108716`），短號查無數據且不報錯
3. **SearchKey** 需 URL Encode（UTF-8）
4. 多值參數（Plants、LevelCode）以重複 query key 傳遞：`&Plants=1800&Plants=100A`
5. 日期格式：query 用 `yyyy/MM/dd HH:mm:ss` 或 `yyyy-MM-dd`（視端點而定）
6. 所有請求帶 `Accept: application/json`
7. **回應信封不統一**：`/api/Price/*` 用 `{data: [...]}`；`/api/ShipmentHistory/*` 用 `{list: [...]}`；`/api/Sd170ShipmentHistory/GetHistoryShipmentsRecord` 用 `{resultCode, resultMsg, resultData}`

---

## 2. 認證

### 2.1 登入取 Token ✅已實測

```
POST /api/De020_Login/Login
```

**Request**
```json
{
  "username": "HEBE.ZHENG",
  "password": "<密碼>",
  "Comments": ""
}
```
| 欄位 | 類型 | 說明 |
|---|---|---|
| username | string | 域賬號 |
| password | string | 密碼（明文，依賴 HTTPS） |
| Comments | string | 域賬號备注，可空 |

**Response 200**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expiration": "2026-08-08T06:31:26Z"
}
```

**JWT Payload 結構**
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
- 有效期約 3~4 天；過期需重新登入
- 服務端依 `SalesGroup`/`DepartmentName` 做權限控制

**調用示例（Python）**
```python
import requests
login = requests.post(
    "https://api-sjfood3.sjfood.us/api/De020_Login/Login",
    json={"username": "HEBE.ZHENG", "password": "***", "Comments": ""}
).json()
headers = {"Authorization": "Bearer " + login["token"]}
```

**調用示例（curl）**
```bash
curl -X POST https://api-sjfood3.sjfood.us/api/De020_Login/Login \
  -H "Content-Type: application/json" \
  -d '{"username":"HEBE.ZHENG","password":"***","Comments":""}'
```

### 2.2 超管登入（後門，慎用）

```
POST /api/De020_Login/LoginSpecial
```
- 賬密存於 DB `special_config`（`IS/SjfoodApiUserName`、`IS/SjfoodApiUserPassWord`）
- 客戶端在普通登入失敗 3 次後自動調用 ⚠️ 安全風險

### 2.3 Passport 統一認證（SSO 用）

```
POST https://passport.sjfood.us/Token
Authorization: Basic <AsBaseBasic>
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=<賬號>&password=<密碼>
```
- 標準 OAuth2 password grant；`AsBaseBasic` 加密存於客戶端 exe.config

---

## 3. SD080 價錢表 API（/api/Price/*）

### 3.1 查詢銷售價目 ✅已實測

```
GET /api/Price/GetSalesPriceList
```

**Query 參數**
| 參數 | 類型 | 必填 | 說明 |
|---|---|---|---|
| SearchKey | string | 否 | 關鍵字（支援物料短號，需 URL Encode） |
| Material | string | 否 | 物料號（**18 位補零**） |
| Limit | int | 否 | 返回筆數上限 |
| PreSalesOff | bool | 否 | 是否排除預售 |
| UpDate | datetime | 否 | 增量查詢起點 `yyyy/MM/dd HH:mm:ss` |
| Plants | string[] | 否 | 工廠代碼（重複 key 傳多值，如 1800/100A/100B） |
| LevelCode | string[] | 否 | 分類層級代碼 |

**Response 200**
```json
{
  "data": [
    {
      "matnr": "000000000040052897",
      "maktx": "HLSO·Bay River·26/30·#40·殼蝦",
      "meins": "LB", "vrkme": "CS",
      "mtart": "ZHW4", "matkl": "SE005", "ekgrp": "D02",
      "levelcode": "001004001002003013001003",
      "level1": "凍肉", "level2": "SHRIMP 蝦類", "level3": "WHITE SHRIMP 白蝦",
      "attri1": "ECUADOR", "attri2": "BLOCK FROZEN", "attri3": "10 BOXES * 4 LB",
      "storagetype": "FZ", "hasimage": 1,
      "priceinfo": [
        {
          "werks": "1800",
          "matnr": "000000000040052897",
          "sapMAP": 3.43, "sapCOST": 3.65, "updCOST": 3.65,
          "sjCost": 3.75, "kfCost": 3.68, "osCost": null,
          "onhand": 0, "openSO": 0, "openPO": 0, "sapATR": 0,
          "status": "NMC",
          "comments": "該貨品暫時買不回來；售賣完后請向客人推薦購買40054493 Ever Max；",
          "flag3": "10箱/層，5層/板",
          "cacheDateTime": "2026-07-21T10:24:53"
        }
      ]
    }
  ]
}
```

**priceinfo 主要欄位**
| 欄位 | 說明 |
|---|---|
| werks | 工廠代碼 |
| sapMAP | SAP 移動平均價 |
| sapCOST / updCOST | SAP 成本 / 更新成本 |
| sjCost / kfCost / osCost | SJ / KF / OS 三公司成本 |
| onhand / onhand1 | 庫存 |
| openSO / openPO / outSTO | 未清銷單 / 採單 / STO |
| sapATR | 可用量（Available to Receive） |
| status | 狀態碼（如 NMC） |
| comments | 採購備註 |
| cacheDateTime | 數據緩存時間 |

**調用示例（Python）**——工廠 1800、物料 40052897 ✅實測成功
```python
r = requests.get(
    "https://api-sjfood3.sjfood.us/api/Price/GetSalesPriceList",
    params=[("SearchKey",""),("Material","000000000040052897"),
            ("Limit",20),("PreSalesOff","false"),("Plants","1800")],
    headers=headers, timeout=60)
items = r.json()["data"]
```

**調用示例（curl）**
```bash
curl -G "https://api-sjfood3.sjfood.us/api/Price/GetSalesPriceList" \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "SearchKey=" \
  --data-urlencode "Material=000000000040052897" \
  --data-urlencode "Limit=20" \
  --data-urlencode "PreSalesOff=false" \
  --data-urlencode "Plants=1800"
```

### 3.2 分頁查詢價目

```
POST /api/Price/GetSalesPriceDataPage
Body: GetSalesPricePageRequest（JSON）
```
主窗體載入用；超時 30 分鐘；回應結構同 3.1。

### 3.3 生成預售資料

```
POST /api/Price/GeneratePreSaleData
Body: {}（GeneratePreSaleDataRequest）
```
**Response**：`{ "list": [{ "werks", "materialId", "orderAvailableStartDate", "orderAvailableEndDate", "orderAvailableDeliveryStartDate", "orderAvailableDeliveryEndDate", "preSaleVirtualStock", "notOverdue" }] }`

### 3.4 銷售公告

```
GET /api/Price/GetSalesNotice?DaylightSavingTime={bool}&WeekDay={weekDay}&IsNewest={bool}
```
**Response**：`{ "data": [tb_100_notice] }`

### 3.5 批量物料價格

```
POST /api/Price/GetMultipleMaterial
Body: GetMultipleMaterialRequest（物料號清單）
```

### 3.6 價目明細資料

```
POST /api/Price/GetPriceInfoData
Body: GetPriceInfoDataRequest
```
**Response**：`{ "tbPricelistInfos": [...] }`

### 3.7 查詢預留信息

```
POST /api/Price/GetReservationInfo
Body: GetReservationInfoRequest
```
**Response**：`{ "data": ZRFMM141 }`（SAP 預留單結構）

### 3.8 附屬 API

| Method | 端點 | 功能 |
|---|---|---|
| POST | `/api/SD560StoDoNotPrintTheMaterialConfiguration/FactoryMatching` | STO 不打印物料工廠匹配 |
| GET/POST | `/api/SalesAsk/GetAskLock`、`/api/SalesAsk/UpdateReadTime` | 問價鎖定/已讀 |
| POST | Metis 翻譯（`https://metahub.wiltechs.com/`） | 多語言物料描述 |

---

## 4. SD170 出貨記錄 API

### 4.1 出貨記錄查詢（/api/ShipmentHistory/*）

| Method | 端點 | 功能 |
|---|---|---|
| POST | `/api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelCountBySql` | 總筆數（先取 count 再分頁） |
| POST | `/api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelBySql` | 分頁查詢（客戶+等級維度，vw_169 視圖） |
| POST | `/api/ShipmentHistory/GetTb12GHistoryCustomerComentLogModel` | 客戶評論記錄 |
| POST | `/api/ShipmentHistory/GetTb12FHistoryCommentComboboxItemModel` | 評論類型下拉選項 |
| POST | `/api/ShipmentHistory/InsertOrUpdateTb12GHistoryCustomerComentLogModel` | 新增/更新評論 |

**調用示例** ✅已實測（2026-08-04，客戶 0000108716「H K CAFÉ」）
```python
# 客戶號必須 10 位補零；返回該客戶按 level5 品類聚合的出貨分析（173 行）
rows = requests.post(BASE+"/api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelBySql",
                     json={"CustomerIds": ["0000108716"], "PageIndex": 0, "PageSize": 500},
                     headers=headers).json()["list"]
# 按 levelLastShipmentDate 篩選即得指定日期出貨品類
# 實測 2026-08-04 該客戶出貨 3 個品類：B/L LOIN C.C 裏脊肉 / PORK CHOP 切豬扒 / CALIFORNIA SQUID GOOD魷魚仔
```

**vw_169 回應主要欄位**：`customerId`、`customerName`、`sales`（負責業務）、`werks`、`levelCode5`/`level5`（品類）、`levelLastShipmentDate`（該品類最後出貨日）、`customerWeightTopCustomBase`/`customerWeightByMountBase`/`customerWeightDiffBase`（重量分析）、`customerDaysWithoutDeliveryBase`（未出貨天數）、金額/利潤佔比系列、`levelCauseListComment`（原因評論）等

### 4.2 單筆發票明細（SD17A/SD17M）✅已實測

```
GET /api/Sd170ShipmentHistory/GetHistoryShipmentsRecord?Fkdat={yyyy-MM-dd}&Vbeln={發票號}&Posnr={行號}
```
**回應信封**：`{"resultCode": 0, "resultMsg": null, "resultData": {...單筆...}}`
- `resultData` 欄位：`invoiceNumber`、`matnr`、`maktx`、`price`、`salesUnit`、`weight`、`invoiceDate`、`level5`、`fkimg`（數量）、`iamt`（金額）、`fkart`（發票類型）等
- 不帶 Vbeln/Posnr 時返回該日期第一筆發票（實測 2026-08-04 → 發票 0500162627「PC-Red Onion 紫洋蔥」$4.02）

**調用示例（curl）**
```bash
curl -G "$BASE/api/Sd170ShipmentHistory/GetHistoryShipmentsRecord" \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "Fkdat=2026-07-01" \
  --data-urlencode "Vbeln=0080001234" \
  --data-urlencode "Posnr=000010"
```

### 4.3 其他 Sd170ShipmentHistory 端點

| Method | 端點 | 功能 |
|---|---|---|
| POST | `/api/Sd170ShipmentHistory/GetResidueMatnrAtr` | 物料剩餘 ATR |
| POST | `/api/Sd170ShipmentHistory/SmartiesHistoryReasonFeedbackManualLabel` | 退貨原因人工標籤（AI 訓練） |
| POST | `/api/Sd170ShipmentHistory/tb12LevelGHistoryCustomerCommentLogModel/insert` | Level 評論記錄寫入（Job） |
| POST | `/api/Sd170ShipmentHistory/ai/uploadTraningMaterial` | 上傳 AI 訓練素材 |
| POST | `/api/Sd170ShipmentHistory/GetSd17MLeftCustomer` | SD17M 左側客戶清單 |
| POST | `/api/Sd170ShipmentHistory/RemoveMatnrCheckNumber` | 移除物料勾選數 |
| POST | `/api/Sd170ShipmentHistory/ExportItemUsageIntentionMaintenance` | 匯出使用意向 |
| POST | `/api/Sd170ShipmentHistory/MatnrMay` | 物料模糊查詢 |
| POST | `/api/Sd170ShipmentHistory/InsertOrUpdateIsAssign` | 指派標記維護 |
| POST | `/api/Sd170ShipmentHistory/GetIsAssign` | 查詢指派標記 |

### 4.4 BYD 發票（SD17M 開發票）

```
POST /api/MaintenanCeoffreight/GetBydInvDataByEccInv
Body: GetBydInvDataByEccInvRequest（ECC 發票號）
```

### 4.4b 客戶發票清單（SD290）✅已實測

```
POST /api/SD290_Credit/GetCustomerInvoice
Body: {"CustomerId": "0000108716", "StartDate": "2026-08-04T00:00:00",
       "EndDate": "2026-08-04T23:59:59", "ItemType": "INVOICE/INVOICE記錄"}
```
- `ItemType` 必填（否則返回「單據類型不能為空」），可選：`STM` / `付款記錄` / `INVOICE/INVOICE記錄`
- 回應 `{code:200, message:"OK", data:[{invoicesNum, invoicesDate, amount, print, ...}]}`——發票抬頭級

**組合用法：查客戶某日物料級出貨明細**（本系統無單一接口，需兩步）：
1. `GetCustomerInvoice` 取當日發票號（如 0500164755）
2. `GetHistoryShipmentsRecord?Fkdat=...&Vbeln=<發票號>&Posnr=<行號>` 逐行取明細
   - ⚠️ **行號會跳號**（實測 0500164755 為 000010/000020/000040），遇到空行不要立即停止，建議連續 8 個空號才結束掃描
   - 每行返回：`matnr`（物料18位）、`maktx`（名稱）、`price`（單價）、`fkimg`（數量）、`vrkme`（銷售單位）、`weight`（重量）、`iamt`（金額）

### 4.5 行背景色配置

```
POST /api/BackColorConfig/GetBackColorConfig    # 讀取
POST /api/BackColorConfig/SaveBackColorConfig   # 保存
```

### 4.6 維護資訊（SD17O，/api/MaintenanceInfo/*）

| Method | 端點 | 功能 |
|---|---|---|
| GET | `/api/MaintenanceInfo/GetGuestConsultingTypeList` | 客訴類型清單 |
| POST | `/api/MaintenanceInfo/AddGuestConsultingType` | 新增客訴類型 |
| POST | `/api/MaintenanceInfo/UpdateGuestConsultingType` | 更新客訴類型 |
| GET | `/api/MaintenanceInfo/GetPlantResponsibleList` | 廠別負責人清單 |
| POST | `/api/MaintenanceInfo/AddOrUpdatePlantResponsible` | 維護廠別負責人 |
| POST | `/api/MaintenanceInfo/GetCityStatesList` | 城市/州清單 |
| POST | `/api/MaintenanceInfo/SaveRemark` | 保存備註 |
| POST | `/api/MaintenanceInfo/GetHistory` | 維護歷史 |

### 4.7 助理諮詢（SD17N）

```
POST /api/Sd17NAssistantConsulting/GetNearestLeaderIdAsync
Body: GetSalesLeaderIdRequest → 返回最近業務主管 ID（提醒推送用）
```

### 4.8 AI 使用意向（/api/IntentionOfUsageAi/*）

| Method | 端點 | 功能 |
|---|---|---|
| POST | `/api/IntentionOfUsageAi/GetIntentionOfUsageAiData` | AI 使用意向資料 |
| POST | `/api/IntentionOfUsageAi/UpdateSalesType` | 更新銷售類型 |
| POST | `/api/IntentionOfUsageAi/GetUseAiTypeExcel` | 匯出 AI 類型 Excel |
| GET | `/api/HistoricalAiReason/GetAiClassificationAccuracy?StartTime=&EndTime=` | AI 原因分類準確率 |

---

## 5. 通用調用模板

### Python（完整可運行）
```python
import requests

BASE = "https://api-sjfood3.sjfood.us"

class SJFoodClient:
    def __init__(self, username, password):
        self.s = requests.Session()
        self.s.headers["Accept"] = "application/json"
        self.login(username, password)

    def login(self, username, password):
        r = self.s.post(BASE + "/api/De020_Login/Login",
                        json={"username": username, "password": password, "Comments": ""},
                        timeout=30)
        r.raise_for_status()
        self.token = r.json()["token"]
        self.s.headers["Authorization"] = "Bearer " + self.token

    def get_price_list(self, material="", search_key="", plants=None, limit=20):
        params = [("SearchKey", search_key), ("Material", material),
                  ("Limit", limit), ("PreSalesOff", "false")]
        for p in (plants or []):
            params.append(("Plants", p))
        r = self.s.get(BASE + "/api/Price/GetSalesPriceList", params=params, timeout=60)
        r.raise_for_status()
        return r.json().get("data", [])

# 使用
client = SJFoodClient("HEBE.ZHENG", "***")
items = client.get_price_list(material="000000000040052897", plants=["1800"])
for m in items:
    print(m["matnr"], m["maktx"], m["priceinfo"][0]["sapCOST"])
```

### 注意事項
1. `Material` 必須 18 位補零；用短號請走 `SearchKey`
2. 回應 JSON 為小寫 key，解析時建議統一 `.lower()` 處理
3. Token 過期（約 3~4 天）需重新登入；401 時重新 login
4. 價目數據有服務端緩存，注意 `cacheDateTime` 欄位
5. 大量查詢建議用 `GetSalesPriceDataPage`（分頁）而非加大 Limit

---

## 附錄 A：已驗證實測記錄

| 日期 | 端點 | 結果 |
|---|---|---|
| 2026-08-04 | POST /api/De020_Login/Login | ✅ 200，取得 JWT |
| 2026-08-04 | GET /api/Price/GetSalesPriceList（空條件 Limit=5） | ✅ 200，5 筆熱門物料 |
| 2026-08-04 | GET /api/Price/GetSalesPriceList（Material 補零 + Plants=1800） | ✅ 200，物料 40052897「HLSO·Bay River·26/30·#40·殼蝦」完整價目 |
| 2026-08-04 | POST /api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelBySql（CustomerIds=["0000108716"]） | ✅ 200，173 行品類聚合；客戶 H K CAFÉ 8/4 出貨 3 品類（裏脊肉/切豬扒/魷魚仔） |
| 2026-08-04 | GET /api/Sd170ShipmentHistory/GetHistoryShipmentsRecord?Fkdat=2026-08-04 | ✅ 200，返回當日首張發票 0500162627（紫洋蔥 $4.02） |
| 2026-08-04 | 同上（短號 "108716" 不補零） | ⚠️ 200 但 0 筆——客戶號必須 10 位補零 |
| 2026-08-05 | POST /api/SD290_Credit/GetCustomerInvoice（0000108716, 2026-08-04） | ✅ 發票 0500164755，$446.16 |
| 2026-08-05 | GET /api/Sd170ShipmentHistory/GetHistoryShipmentsRecord（Vbeln=0500164755, Posnr 迭代） | ✅ 3 行物料明細（豬扒$137.28/魷魚仔$219.60/裏脊肉$89.28），合計與抬頭一致；⚠️ 行號跳號 000030→000040 |

## 附錄 B：相關文件

- `test_price_api.py` — 認證+價目查詢測試腳本
- `query_material.py` — 指定物料查詢腳本
- `price_api_result.json` / `material_40052897.json` — 真實回應樣本
- `SD080_SD170_API分析.md` — 端點提取過程與代碼來源對照
- `認證模塊分析與API實測.md` — 認證流程詳解與安全觀察
