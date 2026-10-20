import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.services.research_direction_service import ResearchDirectionService
from app.services.saved_direction_service import SavedDirectionService
from app.models.project_model import SavedResearchDirection, ProjectPaper
from app.models.paper_model import ResearchPaper

db = SessionLocal()
try:
    print("==================================================")
    print("1. RUNTIME API RESPONSE FROM ProjectIntelligenceService.analyze_project(6)")
    print("==================================================")
    intel_res = ProjectIntelligenceService.analyze_project(project_id=6, db=db)
    intel_dict = intel_res.model_dump()
    
    cand_dirs = intel_dict.get("candidate_research_directions", [])
    print(f"Total Candidate Directions in Intelligence API: {len(cand_dirs)}")
    
    for idx, d in enumerate(cand_dirs, start=1):
        print(f"\n--- Opportunity #{idx} (From Fresh Intelligence API) ---")
        print(f"Title: {d.get('title')}")
        print(f"Algorithms: {[a.get('name') for a in d.get('candidate_algorithms', [])]}")
        print(f"Datasets: {[ds.get('name') for ds in d.get('candidate_datasets', [])]}")
        print(f"Methodologies: {[m.get('name') for m in d.get('candidate_methodologies', [])]}")
        print(f"Supporting Concepts: {d.get('supporting_concepts', [])}")

    print("\n==================================================")
    print("2. PERSISTED SAVED DIRECTIONS IN DATABASE (saved_directions table)")
    print("==================================================")
    saved_db_records = db.query(SavedResearchDirection).filter(SavedResearchDirection.project_id == 6).all()
    print(f"Total Saved Direction Records in Database for Project 6: {len(saved_db_records)}")
    
    for s in saved_db_records:
        print(f"\nSaved Record ID: {s.id}")
        print(f"Project ID: {s.project_id}")
        print(f"Title: {s.title}")
        print(f"Created At: {s.created_at}")
        d_data = s.direction_data if isinstance(s.direction_data, dict) else {}
        print(f"Algorithms: {[a.get('name') for a in d_data.get('candidate_algorithms', [])] if isinstance(d_data.get('candidate_algorithms'), list) else []}")
        print(f"Datasets: {[ds.get('name') for ds in d_data.get('candidate_datasets', [])] if isinstance(d_data.get('candidate_datasets'), list) else []}")
        print(f"Supporting Concepts: {d_data.get('supporting_concepts', [])}")

    print("\n==================================================")
    print("3. DIRECT CODE GENERATION OUTPUT (ResearchDirectionService.generate_directions)")
    print("==================================================")
    assigned_paper_ids = list(set([pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == 6).all()]))
    papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(assigned_paper_ids)).all()
    
    fresh_gen = ResearchDirectionService.generate_directions(
        db=db,
        top_k=5,
        project_id=6,
        project_name=intel_dict['project']['name'],
        project_papers=papers
    ).model_dump()
    
    print(f"Total Freshly Generated Directions: {len(fresh_gen['directions'])}")
    for idx, d in enumerate(fresh_gen['directions'], start=1):
        print(f"\n--- Code-Generated Direction #{idx} ---")
        print(f"Title: {d.get('title')}")
        print(f"Algorithms: {[a.get('name') for a in d.get('candidate_algorithms', [])]}")
        print(f"Datasets: {[ds.get('name') for ds in d.get('candidate_datasets', [])]}")
        print(f"Methodologies: {[m.get('name') for m in d.get('candidate_methodologies', [])]}")
        print(f"Supporting Concepts: {d.get('supporting_concepts', [])}")

finally:
    db.close()
