import os
import sys

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database.session import SessionLocal
from app.services.academic_manuscript_service import AcademicManuscriptService

def test_run():
    db = SessionLocal()
    try:
        print("=== REGENERATING MANUSCRIPT FOR PROJECT 6 ===")
        res = AcademicManuscriptService.generate_fresh_manuscript(db, 6)
        print(f"Generated Manuscript Version: {res.current_version_number}")
        print(f"Completeness Score: {res.completeness.overall_percentage}% ({res.completeness.rating_label})")
        print(f"Status: {res.status}")
        print(f"Total Sections: {len(res.sections)}")

        print("\n=== RUNNING DIAGNOSTICS FOR PROJECT 6 ===")
        diag = AcademicManuscriptService.get_manuscript_diagnostics(db, 6)
        print(f"Version in DB: {diag['version']}")
        print(f"Manuscript ID: {diag['manuscript_id']}")
        print(f"Populated Sections: {diag['populated_sections']} / {diag['total_sections']}")
        print(f"Missing Sections Count: {len(diag['missing_sections'])}")
        print(f"Missing Sections List: {diag['missing_sections']}")
        print(f"Evidence Completeness %: {diag['completeness']}%")
        print(f"Sources Used: {diag['sources_used']}")

    finally:
        db.close()

if __name__ == "__main__":
    test_run()
