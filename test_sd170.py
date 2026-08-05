# -*- coding: utf-8 -*-
"""測試 SD170 出貨記錄：客戶 108716 在 2026/08/04 的出貨記錄"""
import json
import requests

BASE = "https://api-sjfood3.sjfood.us"
s = requests.Session()
s.headers["Accept"] = "application/json"

login = s.post(BASE + "/api/De020_Login/Login",
               json={"username": "HEBE.ZHENG", "password": "FF!123456", "Comments": ""},
               timeout=30).json()
h = {"Authorization": "Bearer " + login["token"]}
print("登入 OK")

# --- 測試 1: vw_169 客戶出貨視圖 ---
print("\n[1] POST /api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelBySql")
r = s.post(BASE + "/api/ShipmentHistory/GetVw169HistoryAllCustomerAndLevelExcelBySql",
           json={"CustomerIds": ["108716"], "CustomerIdStart": None, "PageIndex": 0, "PageSize": 50},
           headers=h, timeout=60)
print("    HTTP", r.status_code)
if r.status_code == 200:
    d = r.json()
    dci = {k.lower(): v for k, v in d.items()}
    lst = dci.get("list") or dci.get("data") or []
    print("    筆數:", len(lst))
    if lst:
        row = {k.lower(): v for k, v in lst[0].items()}
        for k, v in list(row.items()):
            print(f"      {k}: {v}")
    with open(r"C:\Users\HEBE.ZHENG\WorkBuddy\2026-08-04-22-29-05\hifood\sd170_108716_vw169.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
else:
    print("    body:", r.text[:500])

# --- 測試 2: 按日期取出貨明細 ---
print("\n[2] GET /api/Sd170ShipmentHistory/GetHistoryShipmentsRecord (Fkdat=2026-08-04)")
r2 = s.get(BASE + "/api/Sd170ShipmentHistory/GetHistoryShipmentsRecord",
           params={"Fkdat": "2026-08-04", "Vbeln": "", "Posnr": ""},
           headers=h, timeout=60)
print("    HTTP", r2.status_code)
if r2.status_code == 200:
    d2 = r2.json()
    d2ci = {k.lower(): v for k, v in d2.items()}
    lst2 = d2ci.get("list") or d2ci.get("data") or []
    print("    當日總筆數:", len(lst2) if isinstance(lst2, list) else lst2)
    # 過濾客戶 108716（若回應含客戶欄位）
    if isinstance(lst2, list) and lst2:
        keys = {k.lower() for k in lst2[0].keys()}
        print("    欄位:", sorted(keys)[:20])
        cust_rows = [x for x in lst2 if "108716" in json.dumps(x)]
        print("    含 108716 的筆數:", len(cust_rows))
    with open(r"C:\Users\HEBE.ZHENG\WorkBuddy\2026-08-04-22-29-05\hifood\sd170_2026-08-04_records.json", "w", encoding="utf-8") as f:
        json.dump(d2, f, ensure_ascii=False, indent=2)
else:
    print("    body:", r2.text[:500])
