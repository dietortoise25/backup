# -*- coding: utf-8 -*-
"""迭代 Posnr 提取發票 0500164755 的全部行項目"""
import json
import requests

BASE = "https://api-sjfood3.sjfood.us"
s = requests.Session()
login = s.post(BASE + "/api/De020_Login/Login",
               json={"username": "HEBE.ZHENG", "password": "FF!123456", "Comments": ""},
               timeout=30).json()
h = {"Authorization": "Bearer " + login["token"]}

items = []
for i in range(10, 400, 10):  # SAP 行號 000010 起, 步進 10
    posnr = f"{i:06d}"
    r = s.get(BASE + "/api/Sd170ShipmentHistory/GetHistoryShipmentsRecord",
              params={"Fkdat": "2026-08-04", "Vbeln": "0500164755", "Posnr": posnr},
              headers=h, timeout=30)
    d = r.json()
    rd = d.get("resultData")
    if not rd:
        print(f"Posnr={posnr}: 無數據, 停止 (resultCode={d.get('resultCode')}, msg={d.get('resultMsg')})")
        break
    items.append(rd)
    print(f"Posnr={posnr}: {rd.get('matnr')} | {rd.get('maktx')[:35]} | ${rd.get('price')}/{rd.get('salesUnit')} | 數量 {rd.get('fkimg')} {rd.get('vrkme')} | 重量 {rd.get('weight')} | 金額 ${rd.get('iamt')}")

total = sum(x.get("iamt") or 0 for x in items)
print(f"\n共 {len(items)} 行, 合計金額 ${total:.2f} (發票抬頭 $446.16)")
with open(r"C:\Users\HEBE.ZHENG\WorkBuddy\2026-08-04-22-29-05\hifood\invoice_0500164755_items.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print("已存 invoice_0500164755_items.json")
