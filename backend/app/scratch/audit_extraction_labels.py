import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.paper_model import ResearchPaper
from app.models.project_model import ProjectPaper

def audit_labels():
    db = SessionLocal()
    try:
        p6_papers = db.query(ProjectPaper).filter(ProjectPaper.project_id == 6).all()
        paper_ids = [pp.paper_id for pp in p6_papers]
        papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(paper_ids)).all()

        target_phrases = [
            "proposes an explainable",
            "stage detectors",
            "food security",
            "object detectors",
            "yolov9"
        ]

        print("=================== EXTRACTION LABEL AUDIT FOR PROJECT 6 ===================")
        for p in papers:
            print(f"\nPaper ID: {p.id}")
            print(f"Title: {p.title}")
            
            categories = {
                "keywords": p.keywords or [],
                "algorithms": p.algorithms or [],
                "datasets": p.datasets or [],
                "methodologies": p.methodologies or [],
                "domains": p.application_domains or [],
                "metrics": p.metrics or [],
                "tasks": p.tasks or [],
                "applications": p.applications or []
            }

            for cat, items in categories.items():
                matched = [item for item in items if any(tp in str(item).lower() for tp in target_phrases)]
                if matched:
                    print(f"   [{cat.upper()}] Matches: {matched}")

        print("\n=================== FULL CATEGORY VALUES FOR PROJECT 6 ===================")
        for p in papers:
            print(f"\n--- Paper ID {p.id}: {p.title} ---")
            print("Keywords:", p.keywords)
            print("Algorithms:", p.algorithms)
            print("Datasets:", p.datasets)
            print("Methodologies:", p.methodologies)
            print("Domains:", p.application_domains)
            print("Metrics:", p.metrics)
            print("Tasks:", p.tasks)
            print("Applications:", p.applications)

        print("==========================================================================")
    finally:
        db.close()

if __name__ == "__main__":
    audit_labels()
