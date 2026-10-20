import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.services.metadata_extractor import MetadataExtractor
from app.services.project_intelligence_service import ProjectIntelligenceService

def reindex_project6():
    db = SessionLocal()
    try:
        p6_papers = db.query(ProjectPaper).filter(ProjectPaper.project_id == 6).all()
        paper_ids = [pp.paper_id for pp in p6_papers]
        papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(paper_ids)).all()

        print(f"Reindexing {len(papers)} papers for Project 6...")
        for p in papers:
            meta = MetadataExtractor.extract_all(p.full_text, title=p.title, abstract=p.abstract)
            p.keywords = meta.get("keywords", [])
            p.algorithms = meta.get("algorithms", [])
            p.datasets = meta.get("datasets", [])
            p.methodologies = meta.get("methodologies", [])
            p.application_domains = meta.get("application_domains", [])
            p.metrics = meta.get("metrics", [])
            p.tasks = meta.get("tasks", [])
            p.applications = meta.get("applications", [])

        db.commit()
        print("Reindexing complete. Re-evaluating Project 6 research intelligence...")

        intel = ProjectIntelligenceService.analyze_project(project_id=6, db=db)
        raw_json = intel.model_dump()

        print("\n=================== PROJECT 6 FINAL RUNTIME API STATE ===================")
        print("Indexed Papers Count:", len(papers))
        print("Qualified Automatic Opportunities Count:", len(raw_json.get("candidate_research_directions", [])))
        print("Research Gaps Count:", len(raw_json.get("research_gaps", [])))
        print("Underrepresented Concepts Count:", len(raw_json.get("underrepresented_concepts", [])))
        print("\nCandidate Research Directions array:")
        print(json.dumps(raw_json.get("candidate_research_directions", []), indent=2))
        print("\nResearch Gaps array:")
        print(json.dumps(raw_json.get("research_gaps", []), indent=2))
        print("\nUnderrepresented Concepts array:")
        print(json.dumps([u.get("name") for u in raw_json.get("underrepresented_concepts", [])], indent=2))
        print("=========================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    reindex_project6()
