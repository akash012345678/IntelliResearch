import sqlite3

conn = sqlite3.connect('intelliresearch.db')
c = conn.cursor()
cols = [info[1] for info in c.execute("PRAGMA table_info(research_papers)").fetchall()]
print("Columns:", cols)
for row in c.execute("SELECT id, title, filename, uploaded_at FROM research_papers").fetchall():
    print(row)
