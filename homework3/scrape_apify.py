#!/usr/bin/env python3
"""
Scrape restaurant data for all 5 Bangkok zones via Apify Google Maps Scraper
then write results to Google Sheets (via Sheets API v4 + Service Account).
index.html fetches live data from the Sheet via gviz JSON endpoint.
"""
import os, sys, json, time, re, math
import urllib.request, urllib.error

# ─── CONFIG ──────────────────────────────────────────────────────────────────
ACTOR_ID   = "nwua9Gu5YrADL7ZDj"    # compass/crawler-google-places (Google Maps Scraper)
API_BASE   = "https://api.apify.com/v2"
MAX_RESULTS = 20   # scrape 20, keep best 10 after scoring

# Area configs: key, JS var name, search term, BTS coords (lat, lng), area label (Thai)
AREAS = [
    {
        "key": "thonglor",
        "var": "DATA_THONGLOR",
        "search": "restaurant thonglor bangkok group dining",
        "bts_lat": 13.7295, "bts_lng": 100.5840,
        "label": "ทองหล่อ",
    },
    {
        "key": "asok",
        "var": "DATA_ASOK",
        "search": "restaurant asok terminal21 bangkok group dining",
        "bts_lat": 13.7368, "bts_lng": 100.5607,
        "label": "อโศก",
    },
    {
        "key": "siam",
        "var": "DATA_SIAM",
        "search": "restaurant siam square bangkok group dining",
        "bts_lat": 13.7463, "bts_lng": 100.5342,
        "label": "สยาม",
    },
    {
        "key": "ari",
        "var": "DATA_ARI",
        "search": "restaurant ari bts bangkok group dining",
        "bts_lat": 13.7764, "bts_lng": 100.5397,
        "label": "อารีย์",
    },
    {
        "key": "prompong",
        "var": "DATA_PROMPONG",
        "search": "restaurant phrom phong emquartier bangkok group dining",
        "bts_lat": 13.7294, "bts_lng": 100.5694,
        "label": "พร้อมพงษ์",
    },
]

# ─── READ TOKEN ──────────────────────────────────────────────────────────────
token = os.environ.get("APIFY_TOKEN", "").strip()
if not token:
    token = input("Apify API Token: ").strip()
if not token:
    print("❌  No token provided. Abort."); sys.exit(1)

print(f"✅  Token loaded ({token[:6]}...)")

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def api(path, method="GET", body=None):
    sep = "&" if "?" in path else "?"
    url = f"{API_BASE}{path}{sep}token={token}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data,
           headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}"); sys.exit(1)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def price_estimate(item):
    p = item.get("price") or ""
    mapping = {"฿": 150, "฿฿": 300, "฿฿฿": 600, "฿฿฿฿": 1000,
               "$": 150, "$$": 300, "$$$": 600, "$$$$": 1000}
    return mapping.get(p.strip(), 300)

def bts_distance(item, bts_lat, bts_lng):
    lat = item.get("location", {}).get("lat") or item.get("lat")
    lng = item.get("location", {}).get("lng") or item.get("lng")
    if lat is None: return 800
    R = 6371000
    φ1, λ1 = math.radians(bts_lat), math.radians(bts_lng)
    φ2, λ2 = math.radians(float(lat)), math.radians(float(lng))
    dφ = φ2-φ1; dλ = λ2-λ1
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return int(R * 2*math.asin(math.sqrt(a)))

def score_item(item, bts_lat, bts_lng):
    r   = float(item.get("totalScore", 4.0) or 4.0)
    rev = int(item.get("reviewsCount", 50) or 50)
    p   = price_estimate(item)
    d   = bts_distance(item, bts_lat, bts_lng)
    d1  = min(25, round((r * 4 + math.log10(max(rev,1)) * 2), 1))
    d2  = 18 if rev > 500 else 14
    d3  = 15 if p<=200 else 13 if p<=350 else 9 if p<=500 else 5 if p<=700 else 2
    d4  = 15 if d<200 else 13 if d<500 else 10 if d<1000 else 7 if d<2000 else 4
    d5  = 12
    d6  = 8
    return {"d1":round(d1),"d2":d2,"d3":d3,"d4":d4,"d5":d5,"d6":d6,
            "total": round(d1)+d2+d3+d4+d5+d6}

def price_level(p):
    return "low" if p<=350 else "mid" if p<=600 else "high"

def safe(s, fallback=""):
    return str(s or fallback).replace("'","\\'").replace("\\","\\\\").replace("\n"," ").strip()

def scrape_area(area):
    """Run Apify for one area, return sorted top10 items."""
    print(f"\n🚀  [{area['label']}] Starting scrape: {area['search']}")
    run = api(f"/acts/{ACTOR_ID}/runs", method="POST", body={
        "searchStringsArray": [area["search"]],
        "maxCrawledPlacesPerSearch": MAX_RESULTS,
        "language": "th",
        "countryCode": "th",
        "includeHistogram": False,
        "includeOpeningHours": True,
        "includePeopleAlsoSearch": False,
        "maxImages": 0,
        "maxReviews": 0,
    })
    run_id = run["data"]["id"]
    print(f"   Run ID: {run_id}")

    print(f"⏳  Waiting", end="", flush=True)
    for _ in range(60):
        time.sleep(5)
        status = api(f"/actor-runs/{run_id}")["data"]["status"]
        print(".", end="", flush=True)
        if status == "SUCCEEDED": break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"\n❌  Run {status} for {area['label']}"); return []
    else:
        print(f"\n⚠️  Timeout for {area['label']}"); return []
    print(" done!")

    dataset_id = api(f"/actor-runs/{run_id}")["data"]["defaultDatasetId"]
    items_resp  = api(f"/datasets/{dataset_id}/items?limit=50")
    items = items_resp if isinstance(items_resp, list) else items_resp.get("items", [])
    print(f"📦  Got {len(items)} raw results")

    valid = []
    for item in items:
        cats = " ".join(str(c) for c in item.get("categories", [])).lower()
        if any(x in cats for x in ["hotel","spa","beauty","salon","shop","market","7-eleven"]):
            continue
        if float(item.get("totalScore", 0) or 0) < 3.8: continue
        item["_score"] = score_item(item, area["bts_lat"], area["bts_lng"])
        item["_price"] = price_estimate(item)
        item["_bts"]   = bts_distance(item, area["bts_lat"], area["bts_lng"])
        valid.append(item)

    valid.sort(key=lambda x: x["_score"]["total"], reverse=True)
    top = valid[:10]
    print(f"🔢  Top {len(top)} restaurants for {area['label']}")
    return top

# ─── MAIN: scrape all areas ───────────────────────────────────────────────────
all_results = {}
for area in AREAS:
    top = scrape_area(area)
    all_results[area["var"]] = (top, area["label"])
    print(f"\nTop for {area['label']}:")
    for i, item in enumerate(top):
        sc = item["_score"]
        print(f"  {i+1:2}. {item.get('title','?')[:40]:<40} score={sc['total']}  ★{item.get('totalScore','-')}")

# ─── WRITE TO GOOGLE SHEETS via Apps Script ──────────────────────────────────
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbziViDkm7et6i1KHGEeXvRTItUghJrfUNi3xrMIedXs1gu5M2D4ySRF_J0Y9E-29mZ0/exec"

print("\n📊  Writing data to Google Sheets via Apps Script...")

sheet_rows = []
for area in AREAS:
    top, label = all_results[area["var"]]
    for i, item in enumerate(top):
        sc = item["_score"]
        p  = item["_price"]
        oh = item.get("openingHours", [])
        hours = oh[0].get("hours", "—") if oh and isinstance(oh[0], dict) else (str(oh[0]) if oh else "—")
        cats  = item.get("categories", [])
        name  = item.get("title", "")
        gmap  = item.get("url","") or item.get("website","") or \
                f"https://maps.google.com/?q={name.replace(' ','+')}+Bangkok"
        sheet_rows.append({
            "area": area["key"], "rank": i + 1,
            "name": name, "type": cats[0] if cats else "ร้านอาหาร",
            "price": p, "priceLabel": f"฿{p}",
            "pl": "low" if p <= 350 else "mid" if p <= 600 else "high",
            "rating": float(item.get("totalScore", 4.0) or 4.0),
            "reviews": int(item.get("reviewsCount", 0) or 0),
            "bts": item["_bts"],
            "group_ok": str(sc["d2"] >= 15).lower(), "gmax": 20,
            "address": item.get("address", "") or "", "hours": hours, "gmap": gmap,
            "d1": sc["d1"], "d2": sc["d2"], "d3": sc["d3"],
            "d4": sc["d4"], "d5": sc["d5"], "d6": sc["d6"],
            "total": sc["total"],
            "pros": json.dumps([f"ข้อมูลจาก Google Maps จริง",
                                f"Rating {item.get('totalScore',4.0)}★ ({int(item.get('reviewsCount',0) or 0):,} รีวิว)",
                                f"อยู่ในย่าน{label}"], ensure_ascii=False),
            "cons": json.dumps(["โปรดตรวจสอบที่นั่งก่อนไป",
                                "อาจต้องจองล่วงหน้าสำหรับกลุ่มใหญ่"], ensure_ascii=False),
            "ideal": "ข้อมูลจริงจาก Google Maps",
        })

payload = json.dumps({"rows": sheet_rows})
try:
    import requests as _req
    r = _req.post(APPS_SCRIPT_URL, data=payload,
                  headers={"Content-Type": "application/json"}, timeout=60)
    resp = r.json()
    print(f"✅  Written {resp.get('count', len(sheet_rows))} rows to Google Sheets!")
except Exception as e:
    print(f"❌  Error posting to Apps Script: {e}")
    sys.exit(1)

print(f"\n🔗  Apps Script URL: {APPS_SCRIPT_URL}")
print(f"👉  index.html will fetch data live from this URL")
