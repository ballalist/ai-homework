# 📝 AI Prompt Log — HW03 AI Food Decision

**Project:** HW03 · AI Food Decision Report  
**Zone:** ทองหล่อ (Thonglor) · 5 ย่านกรุงเทพฯ  
**Model:** Claude Sonnet 4.6  
**Stack:** Apify · Google Sheets · Claude Sonnet 4.6 · HTML/CSS/JS  
**Date:** 5 มิถุนายน 2568

---

## PROMPT #1 · DATA CLEANING

**Direction:** `USER → CLAUDE`

```
คุณคือผู้ช่วยวิเคราะห์ข้อมูลร้านอาหาร ฉันมีข้อมูลดิบจาก Apify Google Maps Scraper:

{{restaurant_json_array}}

กรุณาทำสิ่งต่อไปนี้:
1. ลบร้านที่ไม่ใช่ "restaurant" (เช่น mini-mart, spa, hotel)
2. ปรับรูปแบบราคาให้เป็น "฿XXX" ต่อคน (ประมาณการถ้าไม่มี)
3. ตรวจสอบว่าร้านเปิดช่วงเย็น (17:00–21:00)
4. เพิ่ม field: suitable_for_group_8_to_12 (true/false)
5. Return เป็น JSON array ที่ clean แล้ว

ตอบเป็น JSON เท่านั้น
```

---

## PROMPT #2 · SCORING PER RESTAURANT

**Direction:** `USER → CLAUDE`

```
ให้คะแนนร้าน "{{restaurant_name}}" สำหรับกลุ่มทีม 8–12 คน มื้อเย็น ย่านทองหล่อ

ข้อมูล:
- Rating: {{rating}}★ ({{reviews}} รีวิว)
- ราคา: {{price}}/คน
- BTS: {{bts_dist}}m

ให้คะแนนตาม 6 มิติ:
- D1 Rating     (0–25)
- D2 Group      (0–20)
- D3 Price      (0–15)
- D4 Travel     (0–15)
- D5 Menu       (0–15)
- D6 Experience (0–10)

พร้อม pros[] 3 ข้อ · cons[] 2 ข้อ

Return JSON: {d1, d2, d3, d4, d5, d6, total, pros[], cons[]}
```

---

## PROMPT #3 · TOP 3 RECOMMENDATION

**Direction:** `USER → CLAUDE`

```
จาก 10 ร้านที่ผ่านการ score แล้ว:

{{scored_restaurants_json}}

แนะนำ Top 3 สำหรับทีม 8–12 คน มื้อเย็น ทองหล่อ

อธิบาย:
- ทำไมเลือก?
- เหมาะกับทีมอย่างไร?
- ข้อควรระวัง?

Format JSON: [{rank, name, reason, warning}]
```

---

## RESPONSE #3 · TOP RECOMMENDATION

**Direction:** `CLAUDE → RESPONSE`

```json
{
  "rank": 1,
  "name": "The Commons Thonglor",
  "score": 88,
  "reason": "เป็น multi-concept food market ที่มีร้านอาหารหลายร้านในที่เดียว ทีมสามารถแยกกินต่างร้านได้ตามใจชอบ แต่ยังนั่งโต๊ะด้วยกันได้ พื้นที่กว้าง รองรับกลุ่มใหญ่โดยไม่ต้องจองล่วงหน้า ราคาเฉลี่ย ฿200–300/คน เหมาะกับงบทีม",
  "warning": "ที่นั่งกลางแจ้ง อาจร้อนช่วงต้นเย็น ควรให้คนหนึ่งไป hold โต๊ะก่อน"
}
```

---

## Scoring Criteria — Weighted 6-Dimension Model

| Dimension     | Weight | Description                       |
| ------------- | ------ | --------------------------------- |
| D1 Rating     | 25%    | Google Maps rating + review count |
| D2 Group      | 20%    | สามารถรองรับกลุ่ม 8–12 คนได้      |
| D3 Price      | 15%    | ราคาต่อหัวเหมาะสมกับงบทีม         |
| D4 Travel     | 15%    | ระยะทางจาก BTS ทองหล่อ            |
| D5 Menu       | 15%    | ความหลากหลายของเมนู               |
| D6 Experience | 10%    | บรรยากาศ / ความโดดเด่น            |

**Total Score:** 0–100 คะแนน  
**Threshold:** ≥ 80 = เหมาะสม (sb-hi) · 70–79 = ปานกลาง (sb-mid) · < 70 = ควรพิจารณา (sb-lo)
