import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.project_intelligence_service import ProjectIntelligenceService

def capture_response():
    db = SessionLocal()
    try:
        intel = ProjectIntelligenceService.analyze_project(project_id=6, db=db)
        raw_json = intel.model_dump()
        
        print("=================== RAW API RESPONSE FOR PROJECT 6 ===================")
        print("Candidate Research Directions count:", len(raw_json.get("candidate_research_directions", [])))
        print("Research Gaps count:", len(raw_json.get("research_gaps", [])))
        print("Underrepresented Concepts count:", len(raw_json.get("underrepresented_concepts", [])))
        print("\nCandidate Research Directions array:")
        print(json.dumps(raw_json.get("candidate_research_directions", []), indent=2))
        print("\nResearch Gaps array:")
        print(json.dumps(raw_json.get("research_gaps", []), indent=2))
        print("\nUnderrepresented Concepts array:")
        print(json.dumps(raw_json.get("underrepresented_concepts", []), indent=2))
        print("=====================================================================")
    finally:
        db.close()

if __name__ == "__main__":
    capture_response()
