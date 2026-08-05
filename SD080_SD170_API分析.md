# SD080 價錢表 與 SD170 出貨記錄 — API 功能提取報告

> 來源：反編譯代碼 `decompiled/`（UI 層 HIFOOD_MAIN、業務層 SJFOOD3.BLL.v9）
> API 基礎位址：`SJFoodApiUrl` = `https://api-sjfood3.sjfood.us/`（exe.config）
> 認證方式：HTTP Header 帶 `Global.user.SJToken`（由 passport.sjfood.us 登入取得）

---

## 一、SD080 價錢表（frm_SD080_price）

主窗體 → `FrmSd080Api`（BLL），全部走 `/api/Price/*` 控制器：

| # | Method | 端點 | 功能 | 備註 |
|---|--------|------|------|------|
| 1 | GET | `/api/Price/GetSalesPriceList` | **查詢銷售價目**（關鍵字/物料/廠別/LevelCode/更新時間） | 主要查詢；結果記憶體緩存 1 分鐘；Polly 重試，超時 30s |
| 2 | POST | `/api/Price/GetSalesPriceDataPage` | **分頁查詢價目**（主窗體載入用） | 超時 30 分鐘；回傳後處理 T 品項、TAX 標記、拉貨預警 |
| 3 | POST | `/api/Price/GeneratePreSaleData` | 生成預售資料（可訂日期/送貨日期/虛擬庫存） | 緩存 20 分鐘；SD085 預售窗體也用 |
| 4 | GET | `/api/Price/GetSalesNotice` | 銷售公告（夏令時間/星期/是否最新） | 回傳 `tb_100_notice`；SD084 公告管理 |
| 5 | POST | `/api/Price/GetMultipleMaterial` | 批量物料價格查詢 | |
| 6 | POST | `/api/Price/GetPriceInfoData` | 價目明細資料 | 回傳 `tb_pricelist_info` |
| 7 | POST | `/api/Price/GetReservationInfo` | 查詢預留信息 | 回傳 SAP 結構 `ZRFMM141` |

附屬調用：

| # | Method | 端點 | 功能 | 來源 |
|---|--------|------|------|------|
| 8 | POST | `/api/SD560StoDoNotPrintTheMaterialConfiguration/FactoryMatching` | 工廠匹配（STO 不打印物料配置） | `Sd560StoDoNotPrintTheMaterialApi` |
| 9 | GET/POST | `/api/SalesAsk/GetAskLock`、`/api/SalesAsk/UpdateReadTime` | 問貨鎖定/已讀（價目表內問價功能） | `SalesAskBll`（SD060） |
| 10 | POST | Metis 翻譯接口（`GetTranslationTextApiForMetis`） | 多語言物料描述翻譯 | `MultiLanguageApi`，走 FastApi `https://metahub.wiltechs.com/` |

**查詢參數**（GetSalesPriceList）：`SearchKey`（URL 編碼）、`Material`、`Limit`、`PreSalesOff`、`UpDate`、`Plants[]`、`LevelCode[]`
**回應**：`SjFoodMaterialPriceDto[]`（物料主檔 + `PriceInfo[]` 價目明細）→ 映射為 `MySJFoodView`

---

## 二、SD170 出貨記錄（rfrm_SD170_ShipmentHistory）

### 2.1 出貨記錄主查詢 — `RfrmSd170Api`

| # | Method | 端點 | 功能 |
|---|--------|------|------|
| 1 | POST | `/api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelCountBySql` | 出貨記錄**總筆數**（vw_169 視圖） |
| 2 | POST | `/api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelBySql` | 出貨記錄**分頁查詢**（客戶+等級維度） |
| 3 | POST | `/api/ShipmentHistory/GetTb12GHistoryCustomerComentLogModel` | 客戶評論記錄查詢 |
| 4 | POST | `/api/ShipmentHistory/GetTb12FHistoryCommentComboboxItemModel` | 評論類型下拉選項 |
| 5 | POST | `/api/ShipmentHistory/InsertOrUpdateTb12GHistoryCustomerComentLogModel` | 新增/更新客戶評論 |
| 6 | GET | `/api/Sd170ShipmentHistory/GetHistoryShipmentsRecord?Fkdat={date}&Vbeln={單號}&Posnr={行號}` | **單筆出貨明細**（SD17A 歷史出貨記錄窗體） |
| 7 | POST | `/api/Sd170ShipmentHistory/GetResidueMatnrAtr` | 物料剩餘 ATR（可出貨量） |
| 8 | POST | `/api/Sd170ShipmentHistory/SmartiesHistoryReasonFeedbackManualLabel` | 退貨原因**人工標籤**（AI 訓練回饋，SD17C/E） |
| 9 | POST | `/api/MaintenanCeoffreight/GetBydInvDataByEccInv` | 依 ECC 發票取 BYD 發票資料（SD17M 開發票） |

### 2.2 行背景色配置 — `BackColorConfigApi`

| # | Method | 端點 | 功能 |
|---|--------|------|------|
| 10 | POST | `/api/BackColorConfig/GetBackColorConfig` | 讀取使用者行顏色配置 |
| 11 | POST | `/api/BackColorConfig/SaveBackColorConfig` | 保存行顏色配置 |

### 2.3 維護資訊（SD17O）— `MaintenanceInfoApi`

| # | Method | 端點 | 功能 |
|---|--------|------|------|
| 12 | GET | `/api/MaintenanceInfo/GetGuestConsultingTypeList` | 客訴類型清單 |
| 13 | POST | `/api/MaintenanceInfo/AddGuestConsultingType` | 新增客訴類型 |
| 14 | POST | `/api/MaintenanceInfo/UpdateGuestConsultingType` | 更新客訴類型 |
| 15 | GET | `/api/MaintenanceInfo/GetPlantResponsibleList` | 廠別負責人清單 |
| 16 | POST | `/api/MaintenanceInfo/AddOrUpdatePlantResponsible` | 維護廠別負責人 |
| 17 | POST | `/api/MaintenanceInfo/GetCityStatesList` | 城市/州清單 |
| 18 | POST | `/api/MaintenanceInfo/SaveRemark` | 保存備註 |
| 19 | POST | `/api/MaintenanceInfo/GetHistory` | 維護歷史記錄 |

### 2.4 助理諮詢（SD17N）— `SD17NAssistantConsultingApi`

| # | Method | 端點 | 功能 |
|---|--------|------|------|
| 20 | POST | `/api/Sd17NAssistantConsulting/GetNearestLeaderIdAsync` | 查最近業務主管（提醒推送用） |

### 2.5 AI 相關

| # | Method | 端點 | 功能 | 來源 |
|---|--------|------|------|------|
| 21 | POST | `/api/Sd170ShipmentHistory/tb12LevelGHistoryCustomerCommentLogModel/insert` | Level 評論記錄寫入（Job 任務） | `FeedBackLevelBll` |
| 22 | POST | `/api/Sd170ShipmentHistory/ai/uploadTraningMaterial` | 上傳退貨原因 AI 訓練素材 | `UploadHistoryReasonTrainingMaterialBll` |
| 23 | GET | `/api/HistoricalAiReason/GetAiClassificationAccuracy?StartTime=&EndTime=` | AI 原因分類準確率 | `HistoryReasonAiClassificationBll` |

### 2.6 物料使用意向維護（SD17M）— `rfrmSd17MItemUsageIntentionMaintenanceApi`

| # | Method | 端點 | 功能 |
|---|--------|------|------|
| 24 | POST | `/api/Sd170ShipmentHistory/GetSd17MLeftCustomer` | 左側客戶清單 |
| 25 | POST | `/api/Sd170ShipmentHistory/RemoveMatnrCheckNumber` | 移除物料勾選數 |
| 26 | POST | `/api/Sd170ShipmentHistory/ExportItemUsageIntentionMaintenance` | 匯出使用意向維護 |
| 27 | POST | `/api/Sd170ShipmentHistory/MatnrMay` | 物料模糊查詢 |
| 28 | POST | `/api/Sd170ShipmentHistory/InsertOrUpdateIsAssign` | 指派標記維護 |
| 29 | POST | `/api/Sd170ShipmentHistory/GetIsAssign` | 查詢指派標記 |
| 30 | POST | `/api/IntentionOfUsageAi/GetIntentionOfUsageAiData` | AI 使用意向資料 |
| 31 | POST | `/api/IntentionOfUsageAi/UpdateSalesType` | 更新銷售類型 |
| 32 | POST | `/api/IntentionOfUsageAi/GetUseAiTypeExcel` | 匯出 AI 類型 Excel |

### 2.7 內嵌價目（SD179 PriceList）
SD170 內嵌的客戶價目表**直接復用 SD080 的 `FrmSd080Api`**（`GetSalesPriceData`、`GetMultipleMaterialAsync`），`RfrmSd179PriceListController` 只是 UI 欄位配置，無獨立 API。

### 2.8 直連資料庫（非 API，舊模式）
主窗體仍使用 SqlSugar 直連 MySQL 的 BLL：`vw_169_history_all_customer_and_level_excel_BLL`、`vw_167/168_history_comment`、`tb_12k_matnr_employ_maintain_BLL`、`tb_190_history_base_log_BLL`——新代碼已改走 2.1 的 API，這些屬於過渡期殘留。

---

## 三、共同特徵

- **統一入口**：所有 API 都是 `api-sjfood3.sjfood.us` 的 ASP.NET WebAPI 控制器，Request/Response 均為 JSON DTO（Model 層定義）
- **調用封裝**：`BaseAPI.PostModelAndReturnModelAsync<TRes,TReq>` / `GetAsyncNew` / `GetAsyncWithPollyRetry`（Polly 重試）
- **緩存策略**：價目類查詢用 `Global.MemoryCache`（1~20 分鐘）
- **認證**：每個請求帶 `SJToken`
