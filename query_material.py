# -*- coding: utf-8 -*-
"""查詢工廠1800、物料40052897的價目信息"""
import json
import requests

BASE = "https://api-sjfood3.sjfood.us"
s = requests.Session()
s.headers.update({"Accept": "application/json"})

login = s.post(BASE + "/api/De020_Login/Login",
               json={"username": "HEBE.ZHENG", "password": "FF!123456", "Comments": ""},
               timeout=30).json()
token = login["token"]
print("登入 OK, token 過期:", login.get("expiration"))

params = [("SearchKey", ""), ("Material", "40052897"), ("Limit", 20),
          ("PreSalesOff", "false"), ("Plants", "1800")]
r = s.get(BASE + "/api/Price/GetSalesPriceList", params=params,
          headers={"Authorization": "Bearer " + token}, timeout=60)
print("HTTP", r.status_code)
data = r.json()
items = {k.lower(): v for k, v in data.items()}.get("data") or []
print("返回物料數:", len(items))
with open(r"C:\Users\HEBE.ZHENG\WorkBuddy\2026-08-04-22-29-05\hifood\material_40052897.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(json.dumps(items, ensure_ascii=False, indent=2)[:3000])
