import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.models.project_model import ResearchProject

db = SessionLocal()

try:
    proj = db.query(ResearchProject).filter(ResearchProject.id == 6).first()
    if not proj:
        print("Project 6 not found!")
        sys.exit(1)

    print(f"=== TEST 1: FAST READ (refresh=False) ===")
    intel_cached = ProjectIntelligenceService.analyze_project(project_id=6, db=db, refresh=False)
    print(f"Total Gaps Returned: {len(intel_cached.research_gaps)}")
    for g in intel_cached.research_gaps:
        print(f" - {g.title} (Key: {g.evidence.get('canonical_relationship_key')}, Score: {g.gap_score}, RelEv: {g.evidence.get('relationship_evidence_score')})")

    print(f"\n=== TEST 2: FRESH REINDEX (refresh=True) ===")
    intel_fresh = ProjectIntelligenceService.analyze_project(project_id=6, db=db, refresh=True)
    print(f"Total Gaps Returned: {len(intel_fresh.research_gaps)}")
    for g in intel_fresh.research_gaps:
        print(f" - {g.title} (Key: {g.evidence.get('canonical_relationship_key')}, Score: {g.gap_score}, RelEv: {g.evidence.get('relationship_evidence_score')})")

finally:
    db.close()
