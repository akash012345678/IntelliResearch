import sqlite3
import re

conn = sqlite3.connect('intelliresearch.db')
cursor = conn.cursor()
cursor.execute('SELECT p.id, p.title, p.abstract, p.full_text FROM research_papers p JOIN project_papers pp ON p.id = pp.paper_id WHERE pp.project_id = 6')
rows = cursor.fetchall()

cands = [
    'Axial Compression',
    'Computational Efficiency',
    'Attention Mechanisms',
    'Semantic Features',
    'Deep Convolution',
    'Large Parameter',
    'Axial Direction',
    'Image Features',
    'Fusion Dataset',
    'Visual Explanations'
]

for c in cands:
    print(f"=== CANDIDATE: {c} ===")
    pattern = re.compile(rf'.{{0,60}}{re.escape(c)}.{{0,60}}', re.IGNORECASE)
    found = False
    for pid, title, abstract, full_text in rows:
        text = f"{title} {abstract or ''} {full_text or ''}"
        matches = pattern.findall(text)
        for m in matches:
            clean_m = " ".join(m.split()).encode('ascii', errors='ignore').decode('ascii')
            print(f"  Paper {pid}: \"...{clean_m}...\"")
            found = True
    if not found:
        print("  (No direct exact match in full text)")
