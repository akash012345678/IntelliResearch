import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.global_research_intelligence_service import GlobalResearchIntelligenceService
from app.services.research_direction_service import ResearchDirectionService
from app.models.project_model import SavedResearchDirection, ResearchProject

db = SessionLocal()
try:
    print("==================================================")
    print("CHECKING GLOBAL RESEARCH DIRECTIONS ENGINE")
    print("==================================================")
    global_dirs = ResearchDirectionService.generate_directions(db=db, top_k=10).model_dump()
    print(f"Total Global Directions: {len(global_dirs.get('directions', []))}")
    for idx, d in enumerate(global_dirs.get('directions', []), start=1):
        print(f"\n--- Global Opportunity #{idx} ---")
        print(f"Title: {d.get('title')}")
        print(f"Candidate Algorithms: {[a.get('name') for a in d.get('candidate_algorithms', [])]}")
        print(f"Candidate Datasets: {[ds.get('name') for ds in d.get('candidate_datasets', [])]}")
        print(f"Candidate Methodologies: {[m.get('name') for m in d.get('candidate_methodologies', [])]}")
        print(f"Supporting Concepts: {d.get('supporting_concepts', [])}")

    print("\n==================================================")
    print("CHECKING ALL SAVED DIRECTIONS IN DATABASE TABLE: saved_directions")
    print("==================================================")
    all_saved = db.query(SavedResearchDirection).all()
    print(f"Total Saved Directions in DB across all projects: {len(all_saved)}")
    for s in all_saved:
        print(f"ID: {s.id} | Project ID: {s.project_id} | Title: {s.title} | Created At: {s.created_at}")

finally:
    db.close()
