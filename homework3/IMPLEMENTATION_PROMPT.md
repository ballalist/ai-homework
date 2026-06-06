# Homework 3: Scrape & Reload Buttons — Implementation Prompt

## Summary
ติดตั้ง 2 ปุ่มใหม่ใน `index.html`:
1. **🕷️ Scrape ใหม่** — เรียก Apify Google Maps Scraper โดยตรงจาก Browser
2. **⟳ รีโหลด** — โหลดข้อมูลจาก Google Sheets (ปรับปรุง)

## What Was Implemented

### 1. Scrape Modal UI
- Modal overlay with token input field
- Area selection dropdown (thonglor, asok, siam, ari, prompong, all)
- Progress log for real-time status updates
- Start/Cancel buttons

### 2. Apify Integration
Browser-direct API calls (no backend):
- POST `/acts/{ACTOR_ID}/runs` → Start scrape job
- GET `/actor-runs/{runId}` → Poll for completion (5s intervals, max 5 min)
- GET `/datasets/{datasetId}/items` → Fetch results
- Filter, score, map to internal format

### 3. Scoring Functions (Ported from Python)
```js
_priceEstimate(item)           // ฿ → number
_btsDistance(lat, lng, ...)    // Haversine formula
_scoreItem(item, ...)          // 6-dimensional scoring (d1-d6)
```

### 4. Data Flow
```
Scrape Button
  ↓ (show modal)
User enters token + selects area
  ↓ (click "เริ่ม Scrape")
startApifyScrape() → _runApify()
  ↓
Apify API: create run → poll → fetch results
  ↓
Score & filter → update DATA arrays
  ↓
Re-render: rankTable, top3, compare
  ↓
Update timestamp + area count
```

## Usage

### For Apify Scraping:
1. Click **🕷️ Scrape ใหม่** button
2. Paste your Apify token (saved to localStorage)
3. Select area (or "ทุกพื้นที่" for all)
4. Click **▶ เริ่ม Scrape**
5. Watch progress log
6. UI updates automatically

### For Google Sheets Reload:
1. Click **⟳ รีโหลด** button
2. Data loads from Google Apps Script
3. All areas updated from Sheets

## Key Files
- `index.html` — All changes in this single file (~540 new lines)
- `scrape_apify.py` — Unchanged (CLI tool still works)

## Configuration
```js
const APIFY_ACTOR_ID = "nwua9Gu5YrADL7ZDj";  // Google Maps Scraper
const APIFY_API_BASE = "https://api.apify.com/v2";

const AREAS_CONFIG = {
  thonglor: { search: "...", bts_lat: 13.7295, ... },
  asok: { search: "...", bts_lat: 13.7368, ... },
  // ... etc
};
```

## Error Handling
- Token validation
- API error responses (HTTP status checks)
- Run status checks (FAILED, ABORTED, TIMED-OUT)
- 5-minute timeout protection
- User feedback via progress log

## localStorage
- `apifyToken` — Saved on modal submit, loaded on modal open

## How to Test
1. Open `index.html` in browser
2. Page loads data from Sheets (existing functionality)
3. Click **🕷️ Scrape ใหม่** → Modal opens
4. Enter Apify token (get from https://apify.com)
5. Select area → Click "เริ่ม Scrape"
6. Watch progress log in real-time
7. Click **⟳ รีโหลด** → Data reloads from Sheets

## Prompt for Further AI Assistance

If you need to enhance or debug this implementation, use this prompt:

```
I'm working on homework3/index.html which has:
- Scrape Modal (id="scrapeModal") with token input, area dropdown
- Apify integration via browser-direct API calls
- 6-dimensional scoring functions (_scoreItem, _btsDistance, _priceEstimate)
- Modal functions: showScrapeModal(), closeScrapeModal(), startApifyScrape(), _runApify()
- localStorage for Apify token persistence

[Describe your issue/request here]
```

## Implementation Details

### Modal HTML Structure
- Overlay (z-index: 9998)
- Header with title and close button
- Token input with localStorage integration
- Area select dropdown (6 options)
- Progress log div (hidden by default)
- Start/Cancel buttons

### JavaScript Entry Points
1. `showScrapeModal()` — Opens modal, loads token
2. `closeScrapeModal()` — Closes modal
3. `startApifyScrape()` — Validates, triggers scrape
4. `_runApify(token, areaKey)` — Main API orchestration
5. `_logScrape(msg)` — Progress log updates

### Data Format Mapping
Apify item → Internal format:
```
{
  name, type, price, priceLabel, pl,
  rating, reviews, bts, group_ok, gmax,
  address, hours, gmap,
  scores: { d1, d2, d3, d4, d5, d6 },
  total, pros, cons, ideal
}
```

---

✅ **Implementation Complete** — Ready for browser testing
