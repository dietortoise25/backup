# -*- coding: utf-8 -*-
"""按反編譯的認證流程實測 /api/Price/GetSalesPriceList"""
import json
import sys
import requests

BASE = "https://api-sjfood3.sjfood.us"
USER = "HEBE.ZHENG"
PWD = "FF!123456"

s = requests.Session()
s.headers.update({"Accept": "application/json"})
s.verify = True

# Step 1: 登入取 SJToken（對應 Login.CheckLoginSjfood → /api/De020_Login/Login）
print("[1] POST /api/De020_Login/Login ...")
r = s.post(
    BASE + "/api/De020_Login/Login",
    json={"username": USER, "password": PWD, "Comments": ""},
    timeout=30,
)
print("    HTTP", r.status_code)
print("    body:", r.text[:500])
r.raise_for_status()
login = r.json()
token = login.get("token")
if not token:
    print("!! 未取得 token，回應中無 token 欄位")
    sys.exit(1)
print("    token:", token[:40] + "..." if len(token) > 40 else token)
print("    expiration:", login.get("expiration"))

# Step 2: 帶 Bearer token 調用 GetSalesPriceList（對應 FrmSd080Api.GetSalesPriceData）
print("\n[2] GET /api/Price/GetSalesPriceList ...")
params = {
    "SearchKey": "",
    "Material": "",
    "Limit": 5,
    "PreSalesOff": "false",
}
r2 = s.get(
    BASE + "/api/Price/GetSalesPriceList",
    params=params,
    headers={"Authorization": "Bearer " + token},
    timeout=60,
)
print("    HTTP", r2.status_code)
if r2.status_code != 200:
    print("    body:", r2.text[:800])
    sys.exit(1)

data = r2.json()
# JSON key 大小寫兼容
data_ci = {k.lower(): v for k, v in data.items()}
items = data_ci.get("data") or []
print("    返回物料數:", len(items))
for m in items[:5]:
    m_ci = {k.lower(): v for k, v in m.items()}
    prices = m_ci.get("priceinfo") or []
    print("    -", m_ci.get("matnr"), "|", (m_ci.get("maktx") or "")[:40],
          "| 單位:", m_ci.get("meins"), "| 價目筆數:", len(prices))
    for p in prices[:3]:
        p_ci = {k.lower(): v for k, v in p.items()}
        print("      *", {k: p_ci[k] for k in list(p_ci)[:8]})
with open(r"C:\Users\HEBE.ZHENG\WorkBuddy\2026-08-04-22-29-05\hifood\price_api_result.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("\n完整回應已存: hifood/price_api_result.json")
