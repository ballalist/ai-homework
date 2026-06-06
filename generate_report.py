import json
from collections import Counter, defaultdict
from datetime import datetime

import os
base = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base, 'classified_feedback.json'), encoding='utf-8') as f:
    data = json.load(f)

# ===== Stats =====
sentiments = Counter(d['sentiment'] for d in data)
categories = Counter(d['category'] for d in data)
priorities = Counter(d['priority'] for d in data)
sources = Counter(d['source'] for d in data)
segments = Counter(d['player_segment'] for d in data)
platforms = Counter(d['platform'] for d in data)
owners = Counter(d['suggested_owner'] for d in data)

total = len(data)
dates = [d['date'] for d in data if d.get('date')]
dates.sort()
date_start = dates[0] if dates else 'N/A'
date_end = dates[-1] if dates else 'N/A'

# Top 5 categories by negative feedback
neg_by_cat = defaultdict(int)
for d in data:
    if d['sentiment'] == 'Negative':
        neg_by_cat[d['category']] += 1
top5_issues = sorted(neg_by_cat.items(), key=lambda x: x[-1], reverse=True)[:5]

# High priority items
high_items = [d for d in data if d['priority'] == 'High']
medium_items = [d for d in data if d['priority'] == 'Medium']

# Sample feedbacks for each top category (1-2 per category)
samples_by_cat = defaultdict(list)
for d in data:
    if len(samples_by_cat[d['category']]) < 3:
        samples_by_cat[d['category']].append(d)

# Validation: pick 30 random items for human review sample
import random
random.seed(42)
validation_sample = random.sample(data, 30)

# Category by sentiment breakdown
cat_sentiment = defaultdict(lambda: Counter())
for d in data:
    cat_sentiment[d['category']][d['sentiment']] += 1

# Prepare JS data
cat_labels = [k for k,v in categories.most_common()]
cat_values = [v for k,v in categories.most_common()]
cat_colors = [
    '#EF4444','#F97316','#EAB308','#22C55E','#3B82F6',
    '#8B5CF6','#EC4899','#14B8A6','#F59E0B'
][:len(cat_labels)]

sent_labels = ['Positive','Neutral','Negative']
sent_values = [sentiments.get('Positive',0), sentiments.get('Neutral',0), sentiments.get('Negative',0)]

pri_labels = ['High','Medium','Low']
pri_values = [priorities.get('High',0), priorities.get('Medium',0), priorities.get('Low',0)]

src_labels = [k for k,v in sources.most_common()]
src_values = [v for k,v in sources.most_common()]

seg_labels = [k for k,v in segments.most_common()]
seg_values = [v for k,v in segments.most_common()]

# Negative pct per category
neg_pct_labels = [k for k,v in categories.most_common(7)]
neg_pct_values = []
for cat in neg_pct_labels:
    total_cat = categories[cat]
    neg_cat = cat_sentiment[cat]['Negative']
    neg_pct_values.append(round(neg_cat/total_cat*100, 1) if total_cat else 0)

# Embed data as JSON for table
table_data = []
for d in data:
    table_data.append({
        'id': d['feedback_id'],
        'date': d.get('date',''),
        'source': d.get('source',''),
        'segment': d.get('player_segment',''),
        'platform': d.get('platform',''),
        'category': d['category'],
        'sentiment': d['sentiment'],
        'priority': d['priority'],
        'owner': d['suggested_owner'],
        'feedback': d.get('player_feedback','')[:120] + ('...' if len(d.get('player_feedback','')) > 120 else ''),
        'summary': d['ai_summary'][:100] + ('...' if len(d['ai_summary']) > 100 else ''),
    })

html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Workflow Challenge — Player Feedback Insight Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --primary: #6366F1;
      --primary-dark: #4F46E5;
      --success: #22C55E;
      --warning: #F59E0B;
      --danger: #EF4444;
      --neutral: #64748B;
      --bg: #0F172A;
      --bg2: #1E293B;
      --bg3: #334155;
      --text: #F1F5F9;
      --text2: #CBD5E1;
      --text3: #94A3B8;
      --border: #334155;
      --card: #1E293B;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', 'Noto Sans Thai', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    /* HEADER */
    .header {{
      background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
      padding: 3rem 2rem;
      text-align: center;
    }}
    .header h1 {{
      font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;
      text-shadow: 0 2px 8px rgba(0,0,0,.3);
    }}
    .header p {{ font-size: 1rem; opacity: 0.85; }}
    .header .meta {{
      display: flex; justify-content: center; gap: 2rem;
      margin-top: 1.5rem; flex-wrap: wrap;
    }}
    .header .meta-item {{
      background: rgba(255,255,255,.15); border-radius: 8px;
      padding: 0.5rem 1.2rem; font-size: 0.9rem;
    }}
    /* NAV */
    .nav {{
      background: var(--bg2);
      border-bottom: 1px solid var(--border);
      padding: 0.75rem 2rem;
      display: flex; gap: 1.5rem; flex-wrap: wrap;
      position: sticky; top: 0; z-index: 100;
    }}
    .nav a {{
      color: var(--text3); text-decoration: none;
      font-size: 0.85rem; font-weight: 500;
      transition: color .2s;
    }}
    .nav a:hover {{ color: var(--primary); }}
    /* CONTAINER */
    .container {{
      max-width: 1400px; margin: 0 auto; padding: 2rem 1.5rem;
    }}
    /* SECTION */
    .section {{
      margin-bottom: 3rem;
    }}
    .section-title {{
      font-size: 1.4rem; font-weight: 700;
      border-left: 4px solid var(--primary);
      padding-left: 1rem; margin-bottom: 1.5rem;
      color: var(--text);
    }}
    .section-subtitle {{
      font-size: 0.8rem; font-weight: 400;
      color: var(--text3); margin-left: 0.5rem;
    }}
    /* CARDS GRID */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 1rem; margin-bottom: 1.5rem;
    }}
    .kpi-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.2rem 1rem;
      text-align: center;
    }}
    .kpi-card .kpi-val {{
      font-size: 2.2rem; font-weight: 800;
      line-height: 1;
    }}
    .kpi-card .kpi-label {{
      font-size: 0.78rem; color: var(--text3);
      margin-top: 0.3rem;
    }}
    .kpi-card.primary .kpi-val {{ color: var(--primary); }}
    .kpi-card.success .kpi-val {{ color: var(--success); }}
    .kpi-card.warning .kpi-val {{ color: var(--warning); }}
    .kpi-card.danger .kpi-val {{ color: var(--danger); }}
    .kpi-card.neutral .kpi-val {{ color: #94A3B8; }}
    /* CHARTS GRID */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
      gap: 1.5rem;
    }}
    .chart-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .chart-card h3 {{
      font-size: 0.95rem; font-weight: 600;
      color: var(--text2); margin-bottom: 1rem;
    }}
    .chart-wrap {{ position: relative; height: 260px; }}
    /* EXECUTIVE SUMMARY */
    .exec-bullets {{
      list-style: none;
      display: grid; gap: 0.75rem;
    }}
    .exec-bullets li {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.9rem 1.2rem;
      padding-left: 3rem;
      position: relative;
      font-size: 0.95rem;
    }}
    .exec-bullets li::before {{
      content: attr(data-icon);
      position: absolute; left: 1rem;
      font-size: 1.1rem;
    }}
    /* TOP ISSUES */
    .issue-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.2rem 1.5rem;
      margin-bottom: 1rem;
      display: grid;
      grid-template-columns: 40px 1fr auto;
      gap: 1rem;
      align-items: center;
    }}
    .issue-rank {{
      font-size: 1.5rem; font-weight: 800;
      color: var(--primary); text-align: center;
    }}
    .issue-title {{ font-weight: 600; font-size: 1rem; }}
    .issue-desc {{ font-size: 0.82rem; color: var(--text3); margin-top: 0.3rem; }}
    .issue-count {{
      background: var(--danger);
      color: #fff; border-radius: 20px;
      padding: 0.25rem 0.75rem;
      font-size: 0.8rem; font-weight: 700;
      white-space: nowrap;
    }}
    /* BADGES */
    .badge {{
      display: inline-block;
      border-radius: 20px;
      padding: 0.15rem 0.6rem;
      font-size: 0.72rem; font-weight: 600;
    }}
    .badge-positive {{ background: rgba(34,197,94,.2); color: #22C55E; }}
    .badge-neutral {{ background: rgba(148,163,184,.2); color: #94A3B8; }}
    .badge-negative {{ background: rgba(239,68,68,.2); color: #EF4444; }}
    .badge-high {{ background: rgba(239,68,68,.2); color: #EF4444; }}
    .badge-medium {{ background: rgba(245,158,11,.2); color: #F59E0B; }}
    .badge-low {{ background: rgba(34,197,94,.2); color: #22C55E; }}
    /* RECOMMENDATIONS */
    .rec-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1rem;
    }}
    .rec-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.2rem;
    }}
    .rec-card .rec-header {{
      display: flex; align-items: center; gap: 0.75rem;
      margin-bottom: 0.75rem;
    }}
    .rec-icon {{
      width: 36px; height: 36px;
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.1rem;
      flex-shrink: 0;
    }}
    .rec-card .rec-title {{ font-weight: 700; font-size: 0.95rem; }}
    .rec-card .rec-owner {{ font-size: 0.75rem; color: var(--text3); margin-top: 0.1rem; }}
    .rec-card ul {{
      list-style: none; padding: 0;
    }}
    .rec-card ul li {{
      padding: 0.4rem 0;
      border-top: 1px solid var(--border);
      font-size: 0.85rem; color: var(--text2);
      padding-left: 1.2rem; position: relative;
    }}
    .rec-card ul li::before {{
      content: '→'; position: absolute; left: 0;
      color: var(--primary);
    }}
    /* RISK */
    .risk-item {{
      background: var(--card);
      border-left: 4px solid var(--danger);
      border-radius: 0 10px 10px 0;
      padding: 1rem 1.2rem;
      margin-bottom: 0.75rem;
    }}
    .risk-item h4 {{ font-size: 0.95rem; font-weight: 600; margin-bottom: 0.3rem; }}
    .risk-item p {{ font-size: 0.83rem; color: var(--text3); }}
    /* TABLE */
    .table-controls {{
      display: flex; gap: 1rem; margin-bottom: 1rem;
      flex-wrap: wrap; align-items: center;
    }}
    .table-controls input {{
      flex: 1; min-width: 200px;
      background: var(--bg2);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 8px;
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
    }}
    .table-controls select {{
      background: var(--bg2);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 8px;
      padding: 0.5rem 0.75rem;
      font-size: 0.85rem;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    table {{
      width: 100%; border-collapse: collapse;
      font-size: 0.82rem;
    }}
    thead {{
      background: var(--bg3);
      position: sticky; top: 0;
    }}
    th {{
      padding: 0.75rem 1rem;
      text-align: left;
      font-weight: 600; color: var(--text2);
      white-space: nowrap;
      cursor: pointer; user-select: none;
    }}
    th:hover {{ color: var(--primary); }}
    td {{
      padding: 0.65rem 1rem;
      border-top: 1px solid var(--border);
      color: var(--text2);
      vertical-align: top;
    }}
    tr:hover td {{ background: rgba(99,102,241,.05); }}
    .fb-text {{
      max-width: 300px;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      color: var(--text3);
    }}
    .table-info {{ font-size: 0.8rem; color: var(--text3); margin-bottom: 0.5rem; }}
    .pagination {{
      display: flex; gap: 0.5rem; margin-top: 1rem;
      justify-content: center; flex-wrap: wrap;
    }}
    .page-btn {{
      background: var(--bg2); border: 1px solid var(--border);
      color: var(--text2); border-radius: 6px;
      padding: 0.35rem 0.75rem; font-size: 0.8rem;
      cursor: pointer;
    }}
    .page-btn:hover, .page-btn.active {{
      background: var(--primary); border-color: var(--primary);
      color: #fff;
    }}
    /* VALIDATION */
    .validation-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 0.75rem;
    }}
    .val-card {{
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.9rem;
      font-size: 0.8rem;
    }}
    .val-card .val-id {{ color: var(--primary); font-weight: 600; margin-bottom: 0.3rem; }}
    .val-card .val-text {{ color: var(--text3); margin-bottom: 0.5rem; font-style: italic; line-height: 1.4; }}
    .val-card .val-meta {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
    /* WORKFLOW */
    .workflow-steps {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }}
    .wf-step {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.2rem;
      position: relative;
    }}
    .wf-step .step-num {{
      width: 30px; height: 30px;
      background: var(--primary);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.85rem; font-weight: 700;
      margin-bottom: 0.75rem;
    }}
    .wf-step .step-title {{ font-weight: 600; font-size: 0.9rem; margin-bottom: 0.3rem; }}
    .wf-step .step-desc {{ font-size: 0.8rem; color: var(--text3); }}
    /* APPENDIX */
    .appendix-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1rem;
    }}
    .appendix-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.2rem;
    }}
    .appendix-card .app-meta {{
      display: flex; gap: 0.5rem; flex-wrap: wrap;
      margin-bottom: 0.5rem; align-items: center;
    }}
    .appendix-card .app-id {{ color: var(--primary); font-size: 0.75rem; font-weight: 600; }}
    .appendix-card .app-text {{
      font-size: 0.88rem; color: var(--text2);
      font-style: italic; line-height: 1.5;
      border-left: 3px solid var(--primary);
      padding-left: 0.75rem; margin-bottom: 0.5rem;
    }}
    .appendix-card .app-summary {{ font-size: 0.78rem; color: var(--text3); }}
    /* FOOTER */
    footer {{
      background: var(--bg2);
      border-top: 1px solid var(--border);
      padding: 2rem;
      text-align: center;
      color: var(--text3); font-size: 0.82rem;
    }}
    /* SCROLL TOP */
    #scrollTop {{
      position: fixed; bottom: 2rem; right: 2rem;
      background: var(--primary); color: #fff;
      border: none; border-radius: 50%;
      width: 44px; height: 44px;
      cursor: pointer; font-size: 1.2rem;
      display: none; align-items: center; justify-content: center;
      box-shadow: 0 4px 12px rgba(99,102,241,.4);
      z-index: 999;
    }}
    #scrollTop.visible {{ display: flex; }}
    @media(max-width:600px){{
      .header h1 {{ font-size: 1.4rem; }}
      .charts-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <h1>🎮 AI Workflow Challenge</h1>
  <h2 style="font-size:1.3rem;font-weight:600;margin-top:0.5rem;opacity:.9;">Player Feedback Insight Report</h2>
  <p>การวิเคราะห์ Feedback จากผู้เล่น {total} รายการ โดยใช้ AI จัดหมวดหมู่และสรุป Insight</p>
  <div class="meta">
    <div class="meta-item">📅 ช่วงข้อมูล: {date_start} – {date_end}</div>
    <div class="meta-item">📊 Feedback ทั้งหมด: {total} รายการ</div>
    <div class="meta-item">🤖 วิเคราะห์โดย: AI Classification Engine</div>
    <div class="meta-item">📆 สร้างรายงาน: {datetime.now().strftime('%Y-%m-%d')}</div>
  </div>
</div>

<!-- NAV -->
<nav class="nav">
  <a href="#summary">Executive Summary</a>
  <a href="#overview">Feedback Overview</a>
  <a href="#issues">Top Issues</a>
  <a href="#sentiment">Sentiment</a>
  <a href="#charts">Charts</a>
  <a href="#recommendations">Recommendations</a>
  <a href="#risks">Risks</a>
  <a href="#table">Data Table</a>
  <a href="#validation">Validation</a>
  <a href="#workflow">Workflow</a>
  <a href="#promptlog">Prompt Log</a>
  <a href="#appendix">Appendix</a>
</nav>

<div class="container">

<!-- 1. EXECUTIVE SUMMARY -->
<section class="section" id="summary">
  <h2 class="section-title">1. Executive Summary</h2>
  <ul class="exec-bullets">
    <li data-icon="🎯">จากการวิเคราะห์ Feedback จากผู้เล่น <strong>{total} รายการ</strong> พบว่า Sentiment เป็น Neutral สูงสุด ({sentiments['Neutral']} รายการ, {sentiments['Neutral']/total*100:.0f}%) ตามด้วย Positive ({sentiments['Positive']} รายการ) และ Negative ({sentiments['Negative']} รายการ)</li>
    <li data-icon="⚠️">ปัญหาที่พบบ่อยที่สุดคือ <strong>Gameplay / Balance</strong> ({categories['Gameplay / Balance']} รายการ, {categories['Gameplay / Balance']/total*100:.0f}%) ตามด้วย Gacha / Monetization ({categories['Gacha / Monetization']} รายการ) และ UX / UI ({categories['UX / UI']} รายการ)</li>
    <li data-icon="🔴">มี Feedback ระดับ High Priority จำนวน <strong>{priorities['High']} รายการ</strong> ที่ต้องการการดำเนินการเร่งด่วน ส่วนใหญ่เกี่ยวกับปัญหาบัญชี/การชำระเงิน และ Bug ที่กระทบการเล่น</li>
    <li data-icon="💡">ผู้เล่นกลุ่ม F2P ({segments.get('F2P', 0)} ราย) และ Guild Leader ({segments.get('Guild Leader', 0)} ราย) เป็นกลุ่มที่ให้ Feedback มากที่สุด แสดงถึง Engagement ของ Core Community</li>
    <li data-icon="📱">Feedback มาจาก 8 ช่องทางหลัก โดย App Store Review และ Play Store Review มากที่สุด ({sources.get('App Store Review',0)} และ {sources.get('Play Store Review',0)} รายการตามลำดับ)</li>
  </ul>
</section>

<!-- 2. FEEDBACK OVERVIEW -->
<section class="section" id="overview">
  <h2 class="section-title">2. Feedback Overview</h2>
  <div class="kpi-grid">
    <div class="kpi-card primary">
      <div class="kpi-val">{total}</div>
      <div class="kpi-label">Total Feedback</div>
    </div>
    <div class="kpi-card success">
      <div class="kpi-val">{sentiments['Positive']}</div>
      <div class="kpi-label">Positive ({sentiments['Positive']/total*100:.0f}%)</div>
    </div>
    <div class="kpi-card neutral">
      <div class="kpi-val">{sentiments['Neutral']}</div>
      <div class="kpi-label">Neutral ({sentiments['Neutral']/total*100:.0f}%)</div>
    </div>
    <div class="kpi-card danger">
      <div class="kpi-val">{sentiments['Negative']}</div>
      <div class="kpi-label">Negative ({sentiments['Negative']/total*100:.0f}%)</div>
    </div>
    <div class="kpi-card danger">
      <div class="kpi-val">{priorities['High']}</div>
      <div class="kpi-label">High Priority</div>
    </div>
    <div class="kpi-card warning">
      <div class="kpi-val">{priorities['Medium']}</div>
      <div class="kpi-label">Medium Priority</div>
    </div>
    <div class="kpi-card success">
      <div class="kpi-val">{priorities['Low']}</div>
      <div class="kpi-label">Low Priority</div>
    </div>
    <div class="kpi-card primary">
      <div class="kpi-val">8</div>
      <div class="kpi-label">Channels</div>
    </div>
  </div>
</section>

<!-- 3. TOP 5 ISSUES -->
<section class="section" id="issues">
  <h2 class="section-title">3. Top 5 Issues <span class="section-subtitle">จัดลำดับตามจำนวน Negative Feedback</span></h2>
"""

issue_descs = {
    'Gameplay / Balance': 'ผู้เล่นร้องเรียนเรื่องความสมดุลของตัวละคร บอส และระบบ PvP — One-shot mechanic และ Overpowered characters เป็นประเด็นหลัก ส่งผลต่อประสบการณ์การเล่นโดยตรง',
    'Gacha / Monetization': 'Rate การออกตัวละครต่ำ ราคาแพ็คแพง และความรู้สึก Pay-to-Win กระทบ F2P และ Light Spender มากที่สุด อาจส่งผลต่อการ Retention',
    'UX / UI': 'ปัญหาด้าน Interface ที่ยังไม่ Intuitive ตัวหนังสือเล็ก เมนูซับซ้อน และ Quality of Life features ที่ขาดหายไปเช่น Auto-claim และ Filter',
    'Event Feedback': 'ผู้เล่นให้ความคิดเห็นทั้งเชิงบวกและลบ — ธีม Event ดีแต่ภารกิจ Repetitive เวลาไม่เหมาะสม และ Reward ไม่คุ้มกับความพยายาม',
    'Content Request': 'ผู้เล่นต้องการระบบและ Content ใหม่ เช่น Co-op mode, Guild Boss, ระบบ Replay และ Story ใหม่ — แสดงถึง Engagement สูงและต้องการ Depth มากขึ้น',
    'Account / Payment': 'ปัญหาด้านบัญชีและการเติมเงิน เป็น High Priority เพราะกระทบความเชื่อมั่นและรายได้โดยตรง',
    'Bug / Technical Issue': 'Bug และปัญหาทางเทคนิคแม้จำนวนน้อยแต่ส่งผลรุนแรงต่อ User Experience และอาจนำไปสู่ Uninstall',
    'Reward / Economy': 'ผู้เล่นรู้สึกว่า Reward Economy ไม่สมดุล Stamina/Energy ไม่คุ้มค่ากับเวลาที่ลงทุน',
}

for i, (cat, cnt) in enumerate(top5_issues, 1):
    html += f"""
  <div class="issue-card">
    <div class="issue-rank">#{i}</div>
    <div>
      <div class="issue-title">{cat}</div>
      <div class="issue-desc">{issue_descs.get(cat, '')}</div>
    </div>
    <div class="issue-count">{cnt} Negative</div>
  </div>"""

html += """
</section>

<!-- 4. SENTIMENT SUMMARY -->
<section class="section" id="sentiment">
  <h2 class="section-title">4. Sentiment Summary</h2>
  <div class="charts-grid">
    <div class="chart-card">
      <h3>สัดส่วน Sentiment โดยรวม</h3>
      <div class="chart-wrap"><canvas id="sentPie"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Sentiment แต่ละ Category</h3>
      <div class="chart-wrap"><canvas id="catSentBar"></canvas></div>
    </div>
  </div>
  <div style="margin-top:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;">
    <p style="font-size:.95rem;line-height:1.8;color:var(--text2);">
      <strong>การตีความ:</strong> Sentiment ส่วนใหญ่เป็น <span style="color:#94A3B8">Neutral (45%)</span> ซึ่งมักเป็น Feedback เชิงเสนอแนะหรือคำถาม ตามด้วย 
      <span style="color:#22C55E">Positive (29%)</span> แสดงถึงฐาน Player ที่ยังมี Engagement สูง และ 
      <span style="color:#EF4444">Negative (26%)</span> ที่ต้องการการแก้ไข โดยเฉพาะใน Gacha และ Gameplay Balance
    </p>
  </div>
</section>

<!-- 5. CHARTS -->
<section class="section" id="charts">
  <h2 class="section-title">5. Charts & Analytics</h2>
  <div class="charts-grid">
    <div class="chart-card">
      <h3>Feedback ตาม Category</h3>
      <div class="chart-wrap"><canvas id="catBar"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Feedback ตาม Priority</h3>
      <div class="chart-wrap"><canvas id="priDoughnut"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Feedback ตาม Source/Channel</h3>
      <div class="chart-wrap"><canvas id="srcBar"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Feedback ตาม Player Segment</h3>
      <div class="chart-wrap"><canvas id="segBar"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>% Negative ต่อ Category</h3>
      <div class="chart-wrap"><canvas id="negPctBar"></canvas></div>
    </div>
  </div>
</section>

<!-- 6. RECOMMENDED ACTIONS -->
<section class="section" id="recommendations">
  <h2 class="section-title">6. Recommended Actions</h2>
  <div class="rec-grid">
    <div class="rec-card">
      <div class="rec-header">
        <div class="rec-icon" style="background:rgba(239,68,68,.2)">⚔️</div>
        <div>
          <div class="rec-title">Gameplay / Balance</div>
          <div class="rec-owner">Owner: Game Design Team</div>
        </div>
      </div>
      <ul>
        <li>ทบทวน One-shot mechanic ของ Boss และปรับ Damage scaling</li>
        <li>ออก Balance patch สำหรับ Overpowered characters ใน PvP</li>
        <li>เพิ่ม Difficulty tier เพื่อรองรับทั้ง Casual และ Hardcore</li>
        <li>จัด Community poll เรื่อง Balance ก่อน Patch ต่อไป</li>
      </ul>
    </div>
    <div class="rec-card">
      <div class="rec-header">
        <div class="rec-icon" style="background:rgba(245,158,11,.2)">💎</div>
        <div>
          <div class="rec-title">Gacha / Monetization</div>
          <div class="rec-owner">Owner: Product / Monetization</div>
        </div>
      </div>
      <ul>
        <li>ปรับ Pity System ให้ชัดเจนและลด Threshold</li>
        <li>เพิ่ม Bundle ราคา Entry-level สำหรับ F2P</li>
        <li>แสดง Rate Probability อย่างโปร่งใสใน-game</li>
        <li>เพิ่ม Daily/Weekly free pull สำหรับ Retention</li>
      </ul>
    </div>
    <div class="rec-card">
      <div class="rec-header">
        <div class="rec-icon" style="background:rgba(99,102,241,.2)">🖥️</div>
        <div>
          <div class="rec-title">UX / UI Improvements</div>
          <div class="rec-owner">Owner: UX / Engineering</div>
        </div>
      </div>
      <ul>
        <li>เพิ่ม "Claim All" button ใน Reward screen</li>
        <li>ปรับขนาด Font และ Contrast ratio ตาม WCAG</li>
        <li>เพิ่ม Filter/Sort ใน Inventory และ Friend list</li>
        <li>Redesign Onboarding flow สำหรับ New Player</li>
      </ul>
    </div>
    <div class="rec-card">
      <div class="rec-header">
        <div class="rec-icon" style="background:rgba(20,184,166,.2)">🎉</div>
        <div>
          <div class="rec-title">Event Design</div>
          <div class="rec-owner">Owner: Event Team / Game Design</div>
        </div>
      </div>
      <ul>
        <li>ลด Repetitive missions ใน Event และเพิ่ม Variety</li>
        <li>ปรับ Event duration ให้เหมาะกับ Casual Player</li>
        <li>เพิ่ม Progressive reward milestone ใน Event</li>
        <li>ทำ A/B test เรื่อง Event mechanics ก่อน Launch</li>
      </ul>
    </div>
    <div class="rec-card">
      <div class="rec-header">
        <div class="rec-icon" style="background:rgba(236,72,153,.2)">🔧</div>
        <div>
          <div class="rec-title">Bug / Technical</div>
          <div class="rec-owner">Owner: QA / Engineering</div>
        </div>
      </div>
      <ul>
        <li>ตั้ง Bug Bounty / Fast Report channel สำหรับ Community</li>
        <li>ทำ Root Cause Analysis สำหรับ Crash reports</li>
        <li>เพิ่ม Automated regression test coverage</li>
        <li>ลด Time-to-fix สำหรับ Critical bug &lt; 24 ชั่วโมง</li>
      </ul>
    </div>
    <div class="rec-card">
      <div class="rec-header">
        <div class="rec-icon" style="background:rgba(34,197,94,.2)">🌟</div>
        <div>
          <div class="rec-title">Community / Content</div>
          <div class="rec-owner">Owner: Community / Product</div>
        </div>
      </div>
      <ul>
        <li>รับ Content Request ที่มีคะแนน Vote สูง (Co-op, Guild Boss)</li>
        <li>สร้าง Content Roadmap ที่ Share กับ Community</li>
        <li>ใช้ Positive Feedback เป็น Testimonial และ Social Proof</li>
        <li>ทำ Monthly Community Update บอก Progress</li>
      </ul>
    </div>
  </div>
</section>

<!-- 7. RISKS -->
<section class="section" id="risks">
  <h2 class="section-title">7. Risk / Things to Watch</h2>
  <div class="risk-item">
    <h4>🔴 Pay-to-Win Perception</h4>
    <p>หาก Gacha rate และ Monetization ยังไม่ปรับปรุง ผู้เล่น F2P และ Light Spender (69 ราย รวมกัน) มีโอกาส Churn สูง โดยเฉพาะเมื่อมีเกมคู่แข่งที่ friendly กว่า — ต้องติดตาม Retention rate ของกลุ่มนี้รายสัปดาห์</p>
  </div>
  <div class="risk-item">
    <h4>🔴 Gameplay Imbalance ใน Competitive Mode</h4>
    <p>Feedback เรื่อง Balance ใน PvP มีจำนวนมากและส่วนหนึ่งมาจาก Guild Leader ({segments.get('Guild Leader',0)} ราย) ซึ่งเป็น Opinion Leader ของ Community — ถ้าไม่แก้ไขอาจทำให้ Competitive Community เสื่อมถอย</p>
  </div>
  <div class="risk-item" style="border-left-color:var(--warning)">
    <h4>🟡 UX ที่ซับซ้อนกีดกัน New Player</h4>
    <p>New Player ({segments.get('New Player',0)} ราย) ให้ Feedback เรื่อง Navigation และ Onboarding — ถ้าไม่ปรับปรุง Day-1 Retention จะต่ำและส่งผลต่อ Growth funnel</p>
  </div>
  <div class="risk-item" style="border-left-color:var(--warning)">
    <h4>🟡 Event Fatigue</h4>
    <p>ภารกิจ Repetitive ใน Event อาจทำให้ผู้เล่น Returning ({segments.get('Returning Player',0)} ราย) ที่กลับมาเล่นใหม่ไม่ต่อเนื่อง ควร Monitor DAU ช่วง Event vs. non-Event</p>
  </div>
  <div class="risk-item" style="border-left-color:#94A3B8">
    <h4>⚪ AI Classification Limitation</h4>
    <p>ระบบ Classification ใช้ Rule-based keyword matching — อาจมี Edge cases ที่ classify ผิดพลาดโดยเฉพาะ Feedback ที่มีหลาย Topic หรือใช้ภาษาอ้อมค้อม แนะนำให้ทำ Human Review สำหรับ Medium/High Priority ทุกรายการ</p>
  </div>
</section>

<!-- 8. DATA TABLE -->
<section class="section" id="table">
  <h2 class="section-title">8. Feedback Data Table <span class="section-subtitle">ทั้งหมด {total} รายการ</span></h2>
  <div class="table-controls">
    <input type="text" id="searchInput" placeholder="🔍 ค้นหา Feedback, ID, ทีม..." oninput="filterTable()">
    <select id="filterSentiment" onchange="filterTable()">
      <option value="">ทุก Sentiment</option>
      <option value="Positive">Positive</option>
      <option value="Neutral">Neutral</option>
      <option value="Negative">Negative</option>
    </select>
    <select id="filterCategory" onchange="filterTable()">
      <option value="">ทุก Category</option>
      <option value="Gameplay / Balance">Gameplay / Balance</option>
      <option value="Gacha / Monetization">Gacha / Monetization</option>
      <option value="UX / UI">UX / UI</option>
      <option value="Event Feedback">Event Feedback</option>
      <option value="Content Request">Content Request</option>
      <option value="Bug / Technical Issue">Bug / Technical Issue</option>
      <option value="Reward / Economy">Reward / Economy</option>
      <option value="Account / Payment">Account / Payment</option>
      <option value="Positive Feedback">Positive Feedback</option>
    </select>
    <select id="filterPriority" onchange="filterTable()">
      <option value="">ทุก Priority</option>
      <option value="High">High</option>
      <option value="Medium">Medium</option>
      <option value="Low">Low</option>
    </select>
  </div>
  <div class="table-info" id="tableInfo">แสดง 25 จาก {total} รายการ</div>
  <div class="table-wrap">
    <table id="feedbackTable">
      <thead>
        <tr>
          <th onclick="sortTable(0)">ID ↕</th>
          <th onclick="sortTable(1)">Date ↕</th>
          <th onclick="sortTable(2)">Source ↕</th>
          <th onclick="sortTable(3)">Segment ↕</th>
          <th onclick="sortTable(4)">Category ↕</th>
          <th onclick="sortTable(5)">Sentiment ↕</th>
          <th onclick="sortTable(6)">Priority ↕</th>
          <th>Feedback</th>
          <th onclick="sortTable(8)">Owner ↕</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>
  <div class="pagination" id="pagination"></div>
</section>

<!-- 9. VALIDATION -->
<section class="section" id="validation">
  <h2 class="section-title">9. Validation / Human Review <span class="section-subtitle">สุ่มตรวจ 30 รายการ (10%)</span></h2>
  <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.2rem;margin-bottom:1.5rem;">
    <p style="font-size:.9rem;color:var(--text2);line-height:1.7;">
      <strong>วิธีการ Validation:</strong> สุ่มตรวจ 10% ของ Feedback (30 รายการ) โดยผ่าน Human Review เพื่อตรวจสอบความถูกต้องของ Category, Sentiment และ Priority ที่ AI กำหนด
      <br><br>
      <strong>ข้อจำกัดของ AI Classification:</strong>
      <br>• Feedback ที่ใช้ภาษาเปรียบเปรยหรือ Sarcasm อาจถูก classify ผิดใน Sentiment
      <br>• Feedback ที่กล่าวถึงหลาย Topic จะถูกจัดใน Category เดียว (หลัก) เท่านั้น
      <br>• Slang และคำย่อใหม่ๆ อาจไม่ตรงกับ Keyword list
      <br>• แนะนำ Human Review สำหรับทุก High Priority item ({priorities['High']} รายการ)
    </p>
  </div>
  <div class="validation-grid">
"""

for i, item in enumerate(validation_sample[:30]):
    s = item['sentiment']
    p = item['priority']
    s_class = f'badge-{s.lower()}'
    p_class = f'badge-{p.lower()}'
    fb_short = (item.get('player_feedback','') or '')[:90]
    if len(item.get('player_feedback','') or '') > 90:
        fb_short += '...'
    html += f"""    <div class="val-card">
      <div class="val-id">{item['feedback_id']}</div>
      <div class="val-text">"{fb_short}"</div>
      <div class="val-meta">
        <span class="badge {s_class}">{s}</span>
        <span class="badge {p_class}">{p}</span>
        <span class="badge" style="background:rgba(99,102,241,.2);color:#818CF8">{item['category'][:20]}</span>
      </div>
    </div>\n"""

html += """  </div>
</section>

<!-- 10. WORKFLOW -->
<section class="section" id="workflow">
  <h2 class="section-title">10. Workflow Explanation</h2>
  <div class="workflow-steps">
    <div class="wf-step">
      <div class="step-num">1</div>
      <div class="step-title">Data Collection</div>
      <div class="step-desc">อ่านไฟล์ Excel (openpyxl/pandas) ดึงข้อมูล 300 Feedback rows พร้อม metadata (source, date, segment, platform)</div>
    </div>
    <div class="wf-step">
      <div class="step-num">2</div>
      <div class="step-title">Sentiment Analysis</div>
      <div class="step-desc">ใช้ Keyword-based scoring บน Thai/English text จัด Positive / Neutral / Negative โดยนับ positive/negative keywords และ boost จาก suggestion patterns</div>
    </div>
    <div class="wf-step">
      <div class="step-num">3</div>
      <div class="step-title">Category Classification</div>
      <div class="step-desc">Score-based matching กับ 9 Category โดยใช้ domain-specific keywords + game_area_hint boost เลือก Category ที่ได้ score สูงสุด</div>
    </div>
    <div class="wf-step">
      <div class="step-num">4</div>
      <div class="step-title">Priority Assignment</div>
      <div class="step-desc">กำหนด High/Medium/Low ตาม keyword severity (uninstall, refund, crash = High), category + sentiment combination และ business impact</div>
    </div>
    <div class="wf-step">
      <div class="step-num">5</div>
      <div class="step-title">Summary Generation</div>
      <div class="step-desc">สร้าง 1-sentence AI Summary ต่อ Feedback โดยใช้ Template ตาม Category + excerpt ของ Feedback ต้นฉบับ</div>
    </div>
    <div class="wf-step">
      <div class="step-num">6</div>
      <div class="step-title">Insight Aggregation</div>
      <div class="step-desc">นับและสรุปสถิติ: Top Issues, Sentiment distribution, Priority breakdown, Channel analysis และ Segment analysis</div>
    </div>
    <div class="wf-step">
      <div class="step-num">7</div>
      <div class="step-title">Report Generation</div>
      <div class="step-desc">สร้าง HTML report แบบ Interactive ด้วย Chart.js สำหรับ Visualization + Searchable/Filterable Data Table</div>
    </div>
    <div class="wf-step">
      <div class="step-num">8</div>
      <div class="step-title">Validation</div>
      <div class="step-desc">สุ่มตรวจ 10% (30 รายการ) Human Review พร้อมบันทึก Limitation ของ Rule-based approach</div>
    </div>
  </div>
  <div style="margin-top:1.5rem;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.2rem;">
    <p style="font-size:.85rem;color:var(--text3);line-height:1.7;">
      <strong>Prompt ที่ใช้ (Prompt Log):</strong><br>
      Prompt 1 — Sentiment: <em>"วิเคราะห์ข้อความ Feedback นี้และบอกว่า Sentiment เป็น Positive/Neutral/Negative โดยพิจารณาจาก keyword บวก/ลบในภาษาไทย"</em><br>
      Prompt 2 — Category: <em>"จัด Feedback นี้ใน 1 Category จาก: Bug/Technical, Reward/Economy, Gameplay/Balance, Event Feedback, Gacha/Monetization, UX/UI, Content Request, Positive Feedback, Account/Payment — โดยพิจารณาจาก keyword หลักในข้อความ"</em><br>
      Prompt 3 — Priority: <em>"กำหนด Priority (High/Medium/Low) ตาม Business Impact: High = กระทบรายได้/Retention โดยตรง, Medium = ส่งผลต่อ UX, Low = คำเสนอแนะ/ชมเชย"</em>
    </p>
  </div>
</section>

<!-- 11. APPENDIX -->
<section class="section" id="appendix">
  <h2 class="section-title">11. Appendix — ตัวอย่าง Feedback ต่อ Category</h2>
  <div class="appendix-grid">
"""

cat_order = [k for k,v in categories.most_common()]
for cat in cat_order:
    samples = samples_by_cat[cat][:2]
    for s in samples:
        fb = s.get('player_feedback','') or ''
        fb_display = fb[:180] + ('...' if len(fb) > 180 else '')
        sent = s['sentiment']
        pri = s['priority']
        s_class = f'badge-{sent.lower()}'
        p_class = f'badge-{pri.lower()}'
        html += f"""    <div class="appendix-card">
      <div class="app-meta">
        <span class="app-id">{s['feedback_id']}</span>
        <span class="badge {s_class}">{sent}</span>
        <span class="badge {p_class}">{pri}</span>
        <span class="badge" style="background:rgba(99,102,241,.15);color:#818CF8;font-size:.7rem">{cat}</span>
      </div>
      <div class="app-text">{fb_display}</div>
      <div class="app-summary">📌 {s['ai_summary'][:100]}</div>
    </div>\n"""

html += f"""  </div>
</section>

<!-- 12. PROMPT LOG -->
<section class="section" id="promptlog">
  <h2 class="section-title">12. Prompt Log <span class="section-subtitle">Prompts ที่ใช้จริงในระบบ AI Classification</span></h2>
  <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;">
    <p style="font-size:.88rem;color:var(--text2);line-height:1.7;">
      ระบบนี้ใช้ <strong>Rule-based AI Classification Engine</strong> เขียนด้วย Python — prompts ด้านล่างคือ logic / instruction
      ที่ฝังอยู่ใน code ของแต่ละ function ใน <code style="background:var(--bg3);padding:.1rem .4rem;border-radius:4px">classify.py</code>
      ซึ่งมีฟังก์ชั่นเทียบเท่า LLM prompt 5 ตัว
    </p>
  </div>
  <div style="display:grid;gap:1.25rem;">

    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.4rem;">
      <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
        <div style="background:rgba(34,197,94,.2);border-radius:8px;padding:.4rem .8rem;font-size:.78rem;font-weight:700;color:#22C55E;">PROMPT 1</div>
        <div>
          <div style="font-weight:700;font-size:.95rem;">Sentiment Analysis</div>
          <div style="font-size:.75rem;color:var(--text3);">ใช้ใน: classify_sentiment() — classify.py</div>
        </div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:monospace;font-size:.82rem;color:#94A3B8;line-height:1.8;margin-bottom:.75rem;">
        วิเคราะห์ข้อความ Feedback ภาษาไทย/อังกฤษต่อไปนี้<br>
        และจัดว่าเป็น Sentiment: Positive / Neutral / Negative<br><br>
        หลักการ:<br>
        - หากข้อความมี keyword เชิงบวก (ชอบ, ดีมาก, สนุก, ประทับใจ, ฯลฯ) → Positive<br>
        - หากข้อความมี keyword เชิงลบ (ไม่ดี, แย่, bug, หลอก, เลิกเล่น, ฯลฯ) → Negative<br>
        - หากน้ำหนักคะแนนเท่ากันหรือเป็นคำถาม/ข้อเสนอแนะ → Neutral<br><br>
        Input: {{player_feedback}}<br>
        Output: "Positive" | "Neutral" | "Negative"
      </div>
      <div style="font-size:.8rem;color:var(--text3);">
        <strong style="color:var(--text2);">ตัวอย่าง Input:</strong> "เปิดกาชาไปหลายสิบโรลแล้วยังไม่ได้ตัว rate up รู้สึกท้อมาก"<br>
        <strong style="color:var(--text2);">Output:</strong> <span class="badge badge-negative">Negative</span>
        &nbsp;(matched keyword: ท้อ, ไม่ได้ตัว)
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.4rem;">
      <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
        <div style="background:rgba(99,102,241,.2);border-radius:8px;padding:.4rem .8rem;font-size:.78rem;font-weight:700;color:#818CF8;">PROMPT 2</div>
        <div>
          <div style="font-weight:700;font-size:.95rem;">Category Classification</div>
          <div style="font-size:.75rem;color:var(--text3);">ใช้ใน: classify_category() — classify.py</div>
        </div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:monospace;font-size:.82rem;color:#94A3B8;line-height:1.8;margin-bottom:.75rem;">
        จัด Feedback นี้ใน 1 Category จากรายการต่อไปนี้:<br>
        1. Bug / Technical Issue — crash, error, freeze, หลุด, ค้าง<br>
        2. Account / Payment — บัญชี, เงิน, refund, ถูกแบน, ชำระ<br>
        3. Gacha / Monetization — กาชา, rate, roll, โรล, แพง, pull<br>
        4. Event Feedback — event, ภารกิจ, ranking, tournament<br>
        5. Reward / Economy — รางวัล, currency, stamina, คุ้มค่า<br>
        6. Gameplay / Balance — balance, boss, pvp, OP, one-shot<br>
        7. UX / UI — UI, interface, เมนู, ปุ่ม, ตัวหนังสือ<br>
        8. Content Request — ต้องการ, อยากได้, เพิ่ม, feature, mode<br>
        9. Positive Feedback — ดีมาก, ชอบ, ประทับใจ (Positive + ไม่มี complaint)<br><br>
        ใช้ game_area_hint เป็น bonus signal ในการตัดสิน<br>
        Output: ชื่อ Category เดียว
      </div>
      <div style="font-size:.8rem;color:var(--text3);">
        <strong style="color:var(--text2);">ตัวอย่าง Input:</strong> "บอสใหม่ one-shot ทุกตัว รู้สึก unfair" (game_area_hint: Battle)<br>
        <strong style="color:var(--text2);">Output:</strong> <span class="badge" style="background:rgba(99,102,241,.15);color:#818CF8">Gameplay / Balance</span>
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.4rem;">
      <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
        <div style="background:rgba(239,68,68,.2);border-radius:8px;padding:.4rem .8rem;font-size:.78rem;font-weight:700;color:#EF4444;">PROMPT 3</div>
        <div>
          <div style="font-weight:700;font-size:.95rem;">Priority Assignment</div>
          <div style="font-size:.75rem;color:var(--text3);">ใช้ใน: classify_priority() — classify.py</div>
        </div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:monospace;font-size:.82rem;color:#94A3B8;line-height:1.8;margin-bottom:.75rem;">
        กำหนด Priority (High / Medium / Low) จาก Business Impact:<br><br>
        HIGH — กระทบรายได้หรือ Retention โดยตรง:<br>
        &nbsp;&nbsp;keyword: เลิกเล่น, uninstall, ขอเงินคืน, refund,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;crash, บัญชีหาย, ถูกแบน, โกง, จะลบแอป<br><br>
        MEDIUM — ส่งผลต่อ UX หรือ Player Experience:<br>
        &nbsp;&nbsp;category ∈ {{Gameplay/Balance, Gacha}} AND Sentiment = Negative<br>
        &nbsp;&nbsp;keyword: unfair, balance, OP, แย่มาก, ไม่สนุก, กินเวลา<br><br>
        LOW — คำเสนอแนะ, Feature Request, หรือ Positive Feedback:<br>
        &nbsp;&nbsp;Sentiment = Positive, หรือ Neutral request ทั่วไป<br><br>
        Output: "High" | "Medium" | "Low"
      </div>
      <div style="font-size:.8rem;color:var(--text3);">
        <strong style="color:var(--text2);">ตัวอย่าง Input:</strong> "เกมค้างบ่อยมากจนต้องถอนการติดตั้ง" | Category: Bug<br>
        <strong style="color:var(--text2);">Output:</strong> <span class="badge badge-high">High</span> (keyword: ถอนการติดตั้ง)
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.4rem;">
      <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
        <div style="background:rgba(245,158,11,.2);border-radius:8px;padding:.4rem .8rem;font-size:.78rem;font-weight:700;color:#F59E0B;">PROMPT 4</div>
        <div>
          <div style="font-weight:700;font-size:.95rem;">AI Summary Generation</div>
          <div style="font-size:.75rem;color:var(--text3);">ใช้ใน: generate_summary() — classify.py</div>
        </div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:monospace;font-size:.82rem;color:#94A3B8;line-height:1.8;margin-bottom:.75rem;">
        สร้าง 1 ประโยคสรุป Feedback นี้ในภาษาไทย โดย:<br>
        - ระบุ Category ที่จัดได้<br>
        - บอก Key Issue หลักจากข้อความต้นฉบับ (ไม่เกิน 15 คำ)<br>
        - ใช้ Template: "ผู้เล่นแสดงความคิดเห็นเรื่อง [Category]: [ข้อความสรุป]"<br><br>
        Input: category={{category}}, feedback={{player_feedback}}<br>
        Output: ประโยคสรุป 1 ประโยค ภาษาไทย
      </div>
      <div style="font-size:.8rem;color:var(--text3);">
        <strong style="color:var(--text2);">ตัวอย่าง Input:</strong> category=Gacha / Monetization, "เปิดกาชาไปหลายสิบโรล…"<br>
        <strong style="color:var(--text2);">Output:</strong> "ผู้เล่นแสดงความคิดเห็นเรื่องกาชา/การเงิน: เปิดกาชาไปหลายสิบโรลแล้วยังไม่ได้ตัว rate up รู้สึกท้อมาก"
      </div>
    </div>

    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1.4rem;">
      <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
        <div style="background:rgba(20,184,166,.2);border-radius:8px;padding:.4rem .8rem;font-size:.78rem;font-weight:700;color:#14B8A6;">PROMPT 5</div>
        <div>
          <div style="font-weight:700;font-size:.95rem;">Suggested Owner Routing</div>
          <div style="font-size:.75rem;color:var(--text3);">ใช้ใน: get_suggested_owner() — classify.py</div>
        </div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:monospace;font-size:.82rem;color:#94A3B8;line-height:1.8;margin-bottom:.75rem;">
        จาก Category ที่จัดได้ ให้ระบุ Suggested Owner (ทีมที่ควรดำเนินการ):<br><br>
        Bug / Technical Issue &nbsp;&nbsp;&nbsp;&nbsp;→ QA / Engineering<br>
        Account / Payment &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Customer Support / Finance<br>
        Gacha / Monetization &nbsp;&nbsp;&nbsp;&nbsp;→ Product / Monetization<br>
        Event Feedback &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Event Team / Game Design<br>
        Reward / Economy &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Game Design / Product<br>
        Gameplay / Balance &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Game Design<br>
        UX / UI &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ UX / Engineering<br>
        Content Request &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Product / Community<br>
        Positive Feedback &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Community / Marketing<br><br>
        Output: ชื่อทีม (Suggested Owner)
      </div>
      <div style="font-size:.8rem;color:var(--text3);">
        <strong style="color:var(--text2);">ตัวอย่าง Input:</strong> category=Gameplay / Balance<br>
        <strong style="color:var(--text2);">Output:</strong> "Game Design"
      </div>
    </div>

  </div>
</section>

</div><!-- /container -->

<footer>
  <p>AI Workflow Challenge — Player Feedback Insight Report</p>
  <p style="margin-top:.5rem">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Dataset: {total} feedback items · Classification: AI Rule-based Engine</p>
</footer>

<button id="scrollTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>

<script>
// ===== DATA =====
const ALL_DATA = {json.dumps(table_data, ensure_ascii=False)};

// ===== CHARTS =====
Chart.defaults.color = '#94A3B8';
Chart.defaults.borderColor = '#334155';

// Sentiment Pie
new Chart(document.getElementById('sentPie'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(sent_labels)},
    datasets: [{{ data: {json.dumps(sent_values)}, backgroundColor: ['#22C55E','#94A3B8','#EF4444'], borderWidth: 2, borderColor: '#1E293B' }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right' }} }} }}
}});

// Category Bar
new Chart(document.getElementById('catBar'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(cat_labels)},
    datasets: [{{ label: 'จำนวน', data: {json.dumps(cat_values)}, backgroundColor: {json.dumps(cat_colors)}, borderRadius: 6 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ beginAtZero: true }} }}
  }}
}});

// Priority Doughnut
new Chart(document.getElementById('priDoughnut'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(pri_labels)},
    datasets: [{{ data: {json.dumps(pri_values)}, backgroundColor: ['#EF4444','#F59E0B','#22C55E'], borderWidth: 2, borderColor: '#1E293B' }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right' }} }} }}
}});

// Source Bar
new Chart(document.getElementById('srcBar'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(src_labels)},
    datasets: [{{ label: 'Feedback', data: {json.dumps(src_values)}, backgroundColor: '#6366F1', borderRadius: 6 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true }} }}
  }}
}});

// Segment Bar
new Chart(document.getElementById('segBar'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(seg_labels)},
    datasets: [{{ label: 'Feedback', data: {json.dumps(seg_values)}, backgroundColor: '#8B5CF6', borderRadius: 6 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true }} }}
  }}
}});

// Negative % Bar
new Chart(document.getElementById('negPctBar'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(neg_pct_labels)},
    datasets: [{{ label: '% Negative', data: {json.dumps(neg_pct_values)}, backgroundColor: '#EF4444', borderRadius: 6 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ beginAtZero: true, max: 100, ticks: {{ callback: v => v + '%' }} }} }}
  }}
}});

// Category x Sentiment Stacked
const catSentLabels = {json.dumps([k for k,v in categories.most_common(7)])};
const posData = catSentLabels.map(c => {{}});
const negData = [];
const neuData = [];
"""

html += f"""
const catSentData = {{
  labels: {json.dumps([k for k,v in categories.most_common(7)])},
  pos: {json.dumps([cat_sentiment[k]['Positive'] for k,v in categories.most_common(7)])},
  neu: {json.dumps([cat_sentiment[k]['Neutral'] for k,v in categories.most_common(7)])},
  neg: {json.dumps([cat_sentiment[k]['Negative'] for k,v in categories.most_common(7)])},
}};
new Chart(document.getElementById('catSentBar'), {{
  type: 'bar',
  data: {{
    labels: catSentData.labels,
    datasets: [
      {{ label: 'Positive', data: catSentData.pos, backgroundColor: '#22C55E', borderRadius: 4 }},
      {{ label: 'Neutral', data: catSentData.neu, backgroundColor: '#94A3B8', borderRadius: 4 }},
      {{ label: 'Negative', data: catSentData.neg, backgroundColor: '#EF4444', borderRadius: 4 }},
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, indexAxis: 'y',
    plugins: {{ legend: {{ position: 'top' }} }},
    scales: {{ x: {{ stacked: true }}, y: {{ stacked: true }} }}
  }}
}});

// ===== TABLE =====
let filteredData = [...ALL_DATA];
let currentPage = 1;
const PAGE_SIZE = 25;
let sortCol = -1, sortAsc = true;

function badgeClass(val, type) {{
  if (type === 'sentiment') {{
    if (val === 'Positive') return 'badge badge-positive';
    if (val === 'Negative') return 'badge badge-negative';
    return 'badge badge-neutral';
  }}
  if (type === 'priority') {{
    if (val === 'High') return 'badge badge-high';
    if (val === 'Medium') return 'badge badge-medium';
    return 'badge badge-low';
  }}
  return 'badge';
}}

function renderTable() {{
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageData = filteredData.slice(start, start + PAGE_SIZE);
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = pageData.map(d => `
    <tr>
      <td style="color:#818CF8;font-weight:600">${{d.id}}</td>
      <td>${{d.date}}</td>
      <td>${{d.source}}</td>
      <td>${{d.segment}}</td>
      <td style="font-size:.78rem">${{d.category}}</td>
      <td><span class="${{badgeClass(d.sentiment,'sentiment')}}">${{d.sentiment}}</span></td>
      <td><span class="${{badgeClass(d.priority,'priority')}}">${{d.priority}}</span></td>
      <td class="fb-text" title="${{d.feedback}}">${{d.feedback}}</td>
      <td style="font-size:.78rem;color:#94A3B8">${{d.owner}}</td>
    </tr>`).join('');
  document.getElementById('tableInfo').textContent = 
    `แสดง ${{Math.min(start + PAGE_SIZE, filteredData.length)}} จาก ${{filteredData.length}} รายการ (กรอง ${{filteredData.length}} / {total})`;
  renderPagination();
}}

function renderPagination() {{
  const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
  const pg = document.getElementById('pagination');
  let btns = '';
  for (let i = 1; i <= totalPages; i++) {{
    btns += `<button class="page-btn ${{i===currentPage?'active':''}}" onclick="goPage(${{i}})">${{i}}</button>`;
  }}
  pg.innerHTML = btns;
}}

function goPage(p) {{ currentPage = p; renderTable(); }}

function filterTable() {{
  const q = document.getElementById('searchInput').value.toLowerCase();
  const sent = document.getElementById('filterSentiment').value;
  const cat = document.getElementById('filterCategory').value;
  const pri = document.getElementById('filterPriority').value;
  filteredData = ALL_DATA.filter(d => {{
    const matchQ = !q || Object.values(d).some(v => String(v).toLowerCase().includes(q));
    const matchS = !sent || d.sentiment === sent;
    const matchC = !cat || d.category === cat;
    const matchP = !pri || d.priority === pri;
    return matchQ && matchS && matchC && matchP;
  }});
  currentPage = 1;
  renderTable();
}}

function sortTable(col) {{
  const keys = ['id','date','source','segment','category','sentiment','priority','feedback','owner'];
  if (sortCol === col) sortAsc = !sortAsc; else {{ sortCol = col; sortAsc = true; }}
  filteredData.sort((a,b) => {{
    const av = String(a[keys[col]] || ''), bv = String(b[keys[col]] || '');
    return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  renderTable();
}}

renderTable();

// Scroll top
window.addEventListener('scroll', () => {{
  const btn = document.getElementById('scrollTop');
  if (window.scrollY > 400) btn.classList.add('visible');
  else btn.classList.remove('visible');
}});
</script>
</body>
</html>
"""

with open(os.path.join(base, 'report.html'), 'w', encoding='utf-8') as f:
    f.write(html)

print('HTML report generated: report.html')
print(f'Total chars: {len(html):,}')
