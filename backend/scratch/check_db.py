import sqlite3

conn = sqlite3.connect('intelliresearch.db')
c = conn.cursor()
tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    if not t.startswith('sqlite_'):
        count = c.execute(f"SELECT COUNT(1) FROM {t}").fetchone()[0]
        print(f"{t}: {count} rows")
