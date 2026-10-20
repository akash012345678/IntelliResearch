import os
import glob
import shutil
from pathlib import Path
from app.database.session import SessionLocal, engine
from app.database.session import Base
from app.models.paper_model import ResearchPaper
from app.models.project_model import (
    ResearchProject,
    ProjectPaper,
    SavedResearchDirection,
    ResearchExperiment,
    ExperimentRun,
    ExperimentResult,
    ResearchManuscript,
    ResearchManuscriptVersion,
)
from app.models.proposal_model import Proposal, ProposalVersion

def wipe_all_data():
    db = SessionLocal()
    try:
        print("Clearing database tables...")
        # Delete dependent versions / results first or delete parent entities with cascade
        db.query(ExperimentResult).delete()
        db.query(ExperimentRun).delete()
        db.query(ResearchExperiment).delete()
        
        db.query(ResearchManuscriptVersion).delete()
        db.query(ResearchManuscript).delete()
        
        db.query(ProposalVersion).delete()
        db.query(Proposal).delete()
        
        db.query(SavedResearchDirection).delete()
        db.query(ProjectPaper).delete()
        db.query(ResearchProject).delete()
        db.query(ResearchPaper).delete()
        
        db.commit()
        print("Database tables wiped successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error wiping database tables: {e}")
    finally:
        db.close()

    base_dir = Path(__file__).resolve().parent.parent
    upload_dirs = [
        base_dir / "app" / "uploads" / "original_papers",
        base_dir / "app" / "uploads" / "extracted_text",
        base_dir / "app" / "uploads" / "embeddings",
        base_dir / "storage" / "cache"
    ]

    print("Cleaning uploaded files and cached data...")
    for udir in upload_dirs:
        if udir.exists():
            for item in udir.iterdir():
                if item.is_file() and item.name != ".gitkeep":
                    try:
                        item.unlink()
                        print(f"Deleted file: {item.name}")
                    except Exception as e:
                        print(f"Failed to delete {item.name}: {e}")
                elif item.is_dir():
                    try:
                        shutil.rmtree(item)
                        print(f"Deleted directory: {item.name}")
                    except Exception as e:
                        print(f"Failed to delete directory {item.name}: {e}")
    print("Files and caches cleaned successfully!")

if __name__ == "__main__":
    wipe_all_data()
