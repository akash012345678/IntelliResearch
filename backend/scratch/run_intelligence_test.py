import sys
import traceback
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.global_research_intelligence_service import GlobalResearchIntelligenceService

def main():
    db = SessionLocal()
    try:
        print("Testing GlobalResearchIntelligenceService().analyze_collection(db)...")
        service = GlobalResearchIntelligenceService()
        res = service.analyze_collection(db_session=db)
        print("SUCCESS! Keys in response:", list(res.keys()))
        print("Collection Summary:", res.get("collection_summary"))
    except Exception as e:
        print("\n=== EXACT BACKEND ERROR TRACEBACK ===")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
