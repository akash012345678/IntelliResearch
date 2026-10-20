import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection
from app.models.proposal_model import Proposal, ProposalVersion
from app.models.paper_model import ResearchPaper

def inspect_db():
    db = SessionLocal()
    try:
        print("=================== RESEARCH PROJECTS ===================")
        projects = db.query(ResearchProject).all()
        for p in projects:
            print(f"Project ID: {p.id}, Name: {p.name}, Status: {p.status}")
        
        print("\n=================== PROJECT 6 PAPERS ===================")
        p6_papers = db.query(ProjectPaper).filter(ProjectPaper.project_id == 6).all()
        for pp in p6_papers:
            paper = db.query(ResearchPaper).filter(ResearchPaper.id == pp.paper_id).first()
            print(f"\nPaper ID: {pp.paper_id}, Title: {paper.title if paper else 'N/A'}")
            if paper:
                print("   Keywords:", paper.keywords)
                print("   Algorithms:", paper.algorithms)
                print("   Datasets:", paper.datasets)
                print("   Methodologies:", paper.methodologies)
                print("   Domains:", paper.application_domains)

        print("\n=================== PROJECT 6 SAVED DIRECTIONS ===================")
        saved_dirs = db.query(SavedResearchDirection).filter(SavedResearchDirection.project_id == 6).all()
        print(f"Saved Directions Count: {len(saved_dirs)}")
        for sd in saved_dirs:
            print(f"  ID: {sd.id}, Title: {sd.title}, Source Dir ID: {sd.source_direction_id}")
            print(f"  Direction Data: {json.dumps(sd.direction_data, indent=2)}")

        print("\n=================== PROJECT 6 PROPOSALS ===================")
        proposals = db.query(Proposal).filter(Proposal.project_id == 6).all()
        print(f"Proposals Count: {len(proposals)}")
        for prop in proposals:
            print(f"  Proposal ID: {prop.id}, UUID: {prop.proposal_uuid}, Title: {prop.title}, Status: {prop.status}")

        print("=========================================================")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
