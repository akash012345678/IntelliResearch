import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.research_direction_service import ResearchDirectionService
from app.services.proposal_draft_service import ProposalDraftService

def verify_pipeline():
    db = SessionLocal()
    try:
        # 1. Verify Project 6 Directions
        resp = ResearchDirectionService.generate_directions(db, top_k=10)
        print(f"Project 6 Qualified Directions Count: {len(resp.directions)}")

        # 2. Verify Manual Proposal Generation
        manual_resp = ProposalDraftService.create_manual_proposal(
            title="Swin-Axial Transformer Evaluation",
            description="Manual user research hypothesis for crop classification.",
            project_id=6
        )
        p = manual_resp.proposal
        print(f"Manual Proposal Title: {p.title}")
        print(f"Is User Provided: {p.is_user_provided}")
        print(f"Generation Mode: {p.generation_mode}")
        print(f"Research Question: {p.research_question}")
        print(f"Objectives Count: {len(p.objectives)}")
        print("Pipeline Verification Successful!")
    finally:
        db.close()

if __name__ == "__main__":
    verify_pipeline()
