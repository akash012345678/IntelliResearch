import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from sqlalchemy import inspect, text

db = SessionLocal()
try:
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    print("Database Tables:", tables)
    
    for table in tables:
        count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"Table '{table}': {count} rows")
        if count > 0 and table not in ["research_papers", "project_papers", "research_projects"]:
            rows = db.execute(text(f"SELECT * FROM {table}")).fetchall()
            print(f"  Sample rows from {table}:", rows[:2])
finally:
    db.close()
