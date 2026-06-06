import json
import re
from collections import Counter, defaultdict
from datetime import datetime

base = r'\\wsl.localhost\Ubuntu\home\bond\projects\ai-homework-test'

with open(f'{base}\\feedback_data.json', encoding='utf-8') as f:
    data = json.load(f)

# ========================
# AI CLASSIFICATION ENGINE
# ========================

def classify_sentiment(text):
    text = text.lower()
    positive_kw = [
        'ชอบ','ดีมาก','สนุก','ขอบคุณ','ดีขึ้น','ประทับใจ','ยอดเยี่ยม','เยี่ยม','ดีใจ',
        'สวยงาม','น่ารัก','เก่ง','ทำได้ดี','ยอด','awesome','great','love','perfect',
        'สุดยอด','ดีครับ','ดีค่ะ','happy','satisfied','excellent','ขอให้เยี่ยม',
        'ดีขึ้นมาก','พัฒนาดีขึ้น','อัปเดตดี','ดีมากครับ','ดีมากค่ะ','ชื่นชม','ปลื้ม',
        'ไม่ผิดหวัง','คุ้มค่า','ราคาดี','เหมาะสม','ฟรีดี','ของฟรีดี',
    ]
    negative_kw = [
        'ไม่ดี','แย่','น่าเศร้า','ผิดหวัง','โกรธ','รำคาญ','เด้ง','ค้าง','ช้า',
        'ล่ม','bug','บั๊ก','error','ไม่แฟร์','เยอะเกิน','แพง','ไม่คุ้ม','ท้อ',
        'เบื่อ','หนัก','น่าหงุดสิ','กวน','หงุดหงิด','น่าหงุดสิ','ถ้าไม่แก้',
        'ไม่ชอบ','ไม่พอใจ','รายงาน','ร้องเรียน','ไม่ได้รับ','ของไม่เข้า',
        'หนักเกิน','ยากเกิน','โหดเกิน','one shot','imbalance','overpowered',
        'pay to win','p2w','กาชาแย่','rate ต่ำ','โรลไม่ได้','ไม่ได้ตัว',
        'แพ็กแพง','เติมแล้วไม่ได้','login ไม่ได้','เข้าไม่ได้','ข้อมูลหาย',
        'โดนแบน','แบนผิด','เสียเงินฟรี','เสียไปเปล่า','เสียดาย','น่าเสียดาย',
        'frustrated','unfair','disappointed','terrible','worst','horrible',
        'ไม่ตอบ','ไม่ช่วย','support แย่','ทีมงานเฉย','ทีมงานไม่',
        'อยาก quit','เลิกเล่น','ถอนตัว','uninstall','ลบเกม',
    ]
    neg_score = sum(1 for kw in negative_kw if kw in text)
    pos_score = sum(1 for kw in positive_kw if kw in text)
    
    # Boosts
    if any(x in text for x in ['ขอแนะนำ','อยากให้','ขอให้','ฝากทีม','รบกวน','น่าจะ']):
        # Suggestions can be neutral or mild negative
        if neg_score == 0 and pos_score == 0:
            return 'Neutral'
    
    if neg_score > pos_score:
        return 'Negative'
    elif pos_score > neg_score:
        return 'Positive'
    else:
        return 'Neutral'

def classify_category(text, game_area_hint=None):
    text_lower = text.lower()
    hint = (game_area_hint or '').lower()
    
    bug_kw = ['เด้ง','ค้าง','บั๊ก','bug','error','ล่ม','หน้าดำ','หน้าขาว',
              'ของไม่เข้า','reward ไม่เข้า','เติมแล้วไม่ได้','ไอเทมหาย',
              'ข้อมูลหาย','เกมปิดเอง','crash','freeze','lag','โหลด','ช้ามาก',
              'ไม่โหลด','ปุ่มกดไม่ได้','ใช้งานไม่ได้','ระบบล่ม','server down',
              'login ไม่ได้','เข้าไม่ได้','เข้าเกมไม่ได้','technical']
    
    account_kw = ['บัญชี','account','login','ล็อกอิน','เข้าระบบ','รหัสผ่าน',
                  'password','email','สมัคร','ย้ายเครื่อง','transfer','bind',
                  'เติมเงิน','payment','เติมแล้วไม่ได้','invoice','ใบเสร็จ',
                  'คืนเงิน','refund','charge','แจ้งปัญหา support','ติดต่อ support']
    
    gacha_kw = ['กาชา','gacha','rate up','pity','โรล','pull','สุ่ม','สุ่มได้',
                'ไม่ได้ตัว','ตัว rate','rate ต่ำ','ออกยาก','แพ็กแพง','แพ็ก',
                'pay to win','p2w','เติมเงิน','ซื้อของ','shop','ราคา',
                'gems','crystal','diamond','เพชร','coin shop','battle pass',
                'คุ้มค่า','ไม่คุ้ม','โอกาสน้อย']
    
    event_kw = ['event','อีเวนต์','ภารกิจ','mission','quest','กิจกรรม',
                'seasonal','daily','weekly','login bonus','daily quest',
                'เวลา event','event จบ','event สั้น','event ยาว',
                'grind','farm event','ทำ event','pass event']
    
    reward_kw = ['รางวัล','reward','ทอง','gold','เหรียญ','coin','resource',
                 'ทรัพยากร','วัตถุดิบ','crafting','material','ไอเทม','item',
                 'stamina','energy','เพื่อน referral','การฟาร์ม','farm',
                 'drop rate','drop ต่ำ','ฟาร์มไม่คุ้ม','ต้องการ resource']
    
    gameplay_kw = ['บอส','boss','ด่าน','stage','level','pvp','guild war',
                   'arena','ตัวละคร','character','สกิล','skill','balance',
                   'แฟร์','ไม่แฟร์','one shot','overpowered','imbalance',
                   'เมต้า','meta','nerf','buff','ยากเกิน','โหดเกิน',
                   'ระบบต่อสู้','combat','damage','hp','def','crit',
                   'difficult','hard','easy','ง่ายเกิน','ยากเกิน']
    
    ux_kw = ['ui','ux','หน้าจอ','เมนู','menu','ปุ่ม','button','font',
             'ตัวหนังสือ','อ่านยาก','ตัวเล็ก','interface','navigation',
             'ไอคอน','icon','layout','design','สี','color','theme',
             'claim all','auto','ระบบแจ้งเตือน','notification','filter',
             'search','sort','inventory management','drag drop']
    
    content_kw = ['ขอ','อยากได้','อยากให้เพิ่ม','เพิ่มระบบ','ระบบใหม่',
                  'feature','โหมดใหม่','mode','co-op','guild boss',
                  'story','เนื้อเรื่อง','lore','skin','costume','outfit',
                  'voice','พากย์','อยาก replay','อยากมี','น่าจะมี',
                  'เสนอ','แนะนำเพิ่ม','request','สิ่งที่อยากเห็น',
                  'อยากให้ทำ','ขอให้ทำ','ฝากทำ','อยากเห็น']
    
    positive_kw_cat = ['ชอบมาก','ดีมาก','สนุกมาก','ยอดเยี่ยม','ชื่นชม',
                       'ขอบคุณมาก','ขอบคุณทีมงาน','ทำได้ดีมาก','ประทับใจมาก',
                       'สุดยอด','อัปเดตดีมาก','เยี่ยมมาก','ปลื้มมาก',
                       'รักเกมนี้','เป็นแฟนเกม','เล่นมานาน']
    
    def score(kw_list):
        return sum(1 for kw in kw_list if kw in text_lower)
    
    scores = {
        'Bug / Technical Issue': score(bug_kw),
        'Account / Payment': score(account_kw),
        'Gacha / Monetization': score(gacha_kw),
        'Event Feedback': score(event_kw),
        'Reward / Economy': score(reward_kw),
        'Gameplay / Balance': score(gameplay_kw),
        'UX / UI': score(ux_kw),
        'Content Request': score(content_kw),
        'Positive Feedback': score(positive_kw_cat),
    }
    
    # Apply hint boost
    hint_map = {
        'inventory': 'UX / UI',
        'gacha': 'Gacha / Monetization',
        'event': 'Event Feedback',
        'guild': 'Gameplay / Balance',
        'pvp': 'Gameplay / Balance',
        'shop': 'Gacha / Monetization',
        'story': 'Content Request',
        'reward': 'Reward / Economy',
        'support': 'Account / Payment',
    }
    for k, v in hint_map.items():
        if k in hint:
            scores[v] = scores.get(v, 0) + 1
    
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # Fallback: check positive vs request
        if any(kw in text_lower for kw in ['ชอบ','ขอบคุณ','สนุก','ดีมาก','ดีใจ']):
            return 'Positive Feedback'
        elif any(kw in text_lower for kw in ['อยากได้','ขอให้','อยากให้','เสนอ','แนะนำ','รบกวน']):
            return 'Content Request'
        else:
            return 'Gameplay / Balance'
    return best

def classify_priority(category, sentiment, text):
    text_lower = text.lower()
    
    # High priority conditions
    high_kw = ['เลิกเล่น','quit','uninstall','ลบเกม','1 ดาว','1ดาว',
               'เสียเงินเปล่า','เสียไปเปล่า','ล่ม','server down','เข้าไม่ได้',
               'ข้อมูลหาย','บัญชีถูกแบน','แบนผิด','เติมแล้วไม่ได้ของ',
               'จ่ายเงินแล้วไม่ได้','error ซื้อไม่ได้','คืนเงิน','refund',
               'หน้าดำ','crash','หยุดเล่น','ไม่เล่นแล้ว','เลิกแล้ว']
    
    medium_kw = ['ไม่แฟร์','one shot','overpowered','balance','เมต้า',
                 'rate ต่ำ','ออกยาก','ทำ event ไม่ได้','ทำ quest ไม่ได้',
                 'รางวัลน้อย','ไม่คุ้ม','pay to win','p2w','grind หนัก']
    
    if any(kw in text_lower for kw in high_kw):
        return 'High'
    if category in ['Bug / Technical Issue', 'Account / Payment'] and sentiment == 'Negative':
        return 'High'
    if any(kw in text_lower for kw in medium_kw):
        return 'Medium'
    if sentiment == 'Negative' and category in ['Gacha / Monetization', 'Gameplay / Balance', 'Reward / Economy', 'Event Feedback']:
        return 'Medium'
    if sentiment == 'Negative':
        return 'Medium'
    if category == 'Content Request':
        return 'Low'
    if sentiment == 'Positive' or category == 'Positive Feedback':
        return 'Low'
    return 'Low'

def generate_summary(text, category, sentiment):
    text = text.strip()
    if len(text) > 100:
        text_short = text[:80] + '...'
    else:
        text_short = text
    
    templates = {
        'Bug / Technical Issue': f'พบปัญหาทางเทคนิค: {text_short}',
        'Reward / Economy': f'ผู้เล่นแสดงความคิดเห็นเรื่องรางวัล/เศรษฐกิจในเกม: {text_short}',
        'Gameplay / Balance': f'ผู้เล่นแสดงความเห็นเรื่องความสมดุลของเกม: {text_short}',
        'Event Feedback': f'ความคิดเห็นเกี่ยวกับ Event: {text_short}',
        'Gacha / Monetization': f'ผู้เล่นแสดงความคิดเห็นเรื่องกาชา/การเงิน: {text_short}',
        'UX / UI': f'ผู้เล่นแสดงความคิดเห็นเรื่อง UX/UI: {text_short}',
        'Content Request': f'คำขอเพิ่มคอนเทนต์: {text_short}',
        'Positive Feedback': f'ผู้เล่นให้ Feedback เชิงบวก: {text_short}',
        'Account / Payment': f'ปัญหาด้านบัญชี/การชำระเงิน: {text_short}',
    }
    return templates.get(category, f'Feedback: {text_short}')

def get_suggested_owner(category, priority):
    owner_map = {
        'Bug / Technical Issue': 'QA / Engineering',
        'Reward / Economy': 'Game Design',
        'Gameplay / Balance': 'Game Design',
        'Event Feedback': 'Event Team / Game Design',
        'Gacha / Monetization': 'Product / Monetization',
        'UX / UI': 'UX / Engineering',
        'Content Request': 'Game Design / Product',
        'Positive Feedback': 'Community',
        'Account / Payment': 'Customer Support / Finance',
    }
    return owner_map.get(category, 'Product')

# Classify all feedback
classified = []
for item in data:
    text = item.get('player_feedback', '') or ''
    hint = item.get('game_area_hint', '') or ''
    
    sentiment = classify_sentiment(text)
    category = classify_category(text, hint)
    priority = classify_priority(category, sentiment, text)
    ai_summary = generate_summary(text, category, sentiment)
    suggested_owner = get_suggested_owner(category, priority)
    
    classified.append({
        **item,
        'sentiment': sentiment,
        'category': category,
        'priority': priority,
        'ai_summary': ai_summary,
        'suggested_owner': suggested_owner,
    })

with open(f'{base}\\classified_feedback.json', 'w', encoding='utf-8') as f:
    json.dump(classified, f, ensure_ascii=False, indent=2)

# Print stats
sentiments = Counter(d['sentiment'] for d in classified)
categories = Counter(d['category'] for d in classified)
priorities = Counter(d['priority'] for d in classified)
sources = Counter(d['source'] for d in classified)
segments = Counter(d['player_segment'] for d in classified)
platforms = Counter(d['platform'] for d in classified)

print('=== SENTIMENT ===')
for k,v in sentiments.most_common():
    print(f'  {k}: {v} ({v/300*100:.1f}%)')

print('\n=== CATEGORY ===')
for k,v in categories.most_common():
    print(f'  {k}: {v} ({v/300*100:.1f}%)')

print('\n=== PRIORITY ===')
for k,v in priorities.most_common():
    print(f'  {k}: {v} ({v/300*100:.1f}%)')

print('\n=== SOURCE ===')
for k,v in sources.most_common():
    print(f'  {k}: {v}')

print('\n=== SEGMENT ===')
for k,v in segments.most_common():
    print(f'  {k}: {v}')

print('\nClassification done. Saved to classified_feedback.json')
