import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import SessionLocal
from app.services.academic_manuscript_service import AcademicManuscriptService

def check():
    db = SessionLocal()
    try:
        manuscript = AcademicManuscriptService.get_or_generate_manuscript(db, 6)
        print("--- PROJECT 6 MANUSCRIPT COMPLETENESS DIAGNOSTICS ---")
        print(f"Title: {manuscript.title}")
        print(f"Status: {manuscript.status}")
        print(f"Overall Percentage: {manuscript.completeness.overall_percentage}%")
        print(f"Rating Label: {manuscript.completeness.rating_label}")
        print(f"Recorded Sections: {manuscript.completeness.recorded_sections_count}")
        print(f"Derived Sections: {manuscript.completeness.derived_sections_count}")
        print(f"Proposed Sections: {manuscript.completeness.proposed_sections_count}")
        print(f"Experimental Result Sections: {manuscript.completeness.experimental_result_sections_count}")
        print(f"Missing Sections: {manuscript.completeness.missing_sections_count}")
        print("-----------------------------------------------------")
    finally:
        db.close()

if __name__ == "__main__":
    check()
