import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.research_gap_service import ResearchGapService

def main():
    db = SessionLocal()
    gap_service = ResearchGapService()
    gaps = gap_service.detect_gaps(db_session=db, top_k=10)
    db.close()

    print(f"=== Real Supabase Potential Research Gaps (Top {len(gaps)}) ===")
    for idx, g in enumerate(gaps, 1):
        print(f"\n#{idx}: Source Paper ID {g['source_paper_id']} ('{g['source_paper_title']}')")
        print(f"    Candidate Target: {g['target_label']} ({g['target_type']}) | Rel: {g['relationship_type']}")
        print(f"    Gap Score: {g['gap_score']} | Confidence: {g['confidence']}")
        print("    Evidence Breakdown:")
        print(f"      - Link Prediction Score: {g['evidence']['link_prediction_score']}")
        print(f"      - Cross-Paper Support: {g['evidence']['cross_paper_support']}")
        print(f"      - Semantic Evidence: {g['evidence']['semantic_evidence']}")
        print(f"      - Underrepresentation Score: {g['evidence']['underrepresentation_score']}")
        print("    Explanations:")
        for exp in g['explanation']:
            print(f"      * {exp}")

if __name__ == "__main__":
    main()
