from app.database.session import SessionLocal
from app.services.academic_manuscript_service import AcademicManuscriptService

def check():
    db = SessionLocal()
    try:
        manuscript = AcademicManuscriptService.get_or_generate_manuscript(db, 1)
        print("--- PROJECT 1 DUAL SCORE DIAGNOSTICS ---")
        print(f"Title: {manuscript.title}")
        print(f"Status: {manuscript.status}")
        print(f"MANUSCRIPT COMPLETION: {manuscript.completeness.manuscript_completion_percentage}% ({manuscript.completeness.manuscript_completion_label})")
        print(f"EVIDENCE COMPLETENESS: {manuscript.completeness.evidence_completeness_percentage}% ({manuscript.completeness.evidence_rating_label})")
        print(f"Recorded Sections: {manuscript.completeness.recorded_sections_count}")
        print(f"Derived Sections: {manuscript.completeness.derived_sections_count}")
        print(f"Proposed Sections: {manuscript.completeness.proposed_sections_count}")
        print(f"Experimental Result Sections: {manuscript.completeness.experimental_result_sections_count}")
        print(f"Missing Sections: {manuscript.completeness.missing_sections_count}")
        print("----------------------------------------")
    finally:
        db.close()

if __name__ == "__main__":
    check()
