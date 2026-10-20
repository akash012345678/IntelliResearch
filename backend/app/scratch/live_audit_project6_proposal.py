import json
from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.services.proposal_draft_service import ProposalDraftService


def audit_project6_proposal():
    db = SessionLocal()
    try:
        project_id = 6
        p = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        print(f"=== PROJECT AUDIT: ID={project_id}, Name='{p.name if p else 'N/A'}' ===")

        res = ProposalDraftService.synthesize_draft(
            db=db,
            project_id=project_id,
            direction_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
            opportunity_family_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
            payload_title="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
            regenerate=False
        )

        proposal = res.proposal
        print("\n--- LIVE PROPOSAL AUDIT RESULTS ---")
        print(f"Proposal ID: {res.proposal_id}")
        print(f"Version Number: {res.version_number}")
        print(f"Source Gap / Direction ID: {proposal.source_direction_id}")
        print(f"Source Gap ID: {proposal.source_gap_id}")

        sp_ids = [sp.get('paper_id') if isinstance(sp, dict) else sp.paper_id for sp in proposal.supporting_papers]
        print(f"Supporting Papers: {sp_ids}")

        print(f"Candidate Algorithms: {proposal.candidate_algorithms}")
        print(f"Candidate Datasets: {proposal.candidate_datasets}")
        print("Datasets Provenance:")
        for dp in proposal.datasets_provenance:
            print(f"  - Dataset: '{dp.get('dataset_name')}', Source Papers: {dp.get('source_paper_ids')}, Status: {dp.get('evidence_status')}")

        print("\nMethodology Excerpt:")
        print(proposal.proposed_methodology[:300] + "...")

        print("\nExperimental Plan Excerpt:")
        print(proposal.experimental_plan[:300] + "...")

        print("\nEvaluation Metrics Excerpt:")
        print(proposal.evaluation_metrics)

        # Confirmations
        assert proposal.source_direction_id in ("FAMILY_EXPLAINABILITY___FAMILY_YOLO", "dir_1"), f"Unexpected source_direction_id '{proposal.source_direction_id}'"
        assert set(sp_ids) == {14, 16}, f"Expected supporting papers {{14, 16}}, got {sp_ids}"
        assert "Multi-Source Benchmark Dataset" not in proposal.candidate_datasets, "Leakage detected! Multi-Source Benchmark Dataset from Paper 15 must NOT appear in Opportunity 1."
        assert "PlantDoc" in proposal.candidate_datasets, "PlantDoc must be included from Paper 14."
        assert "PlantVillage" in proposal.candidate_datasets, "PlantVillage must be included from Paper 16."

        full_text = f"{proposal.abstract} {proposal.problem_statement} {proposal.expected_contribution} {proposal.limitations}".lower()
        for forbidden in ["first", "unprecedented", "state-of-the-art", "guaranteed improvement"]:
            assert forbidden not in full_text, f"Forbidden global novelty claim '{forbidden}' found!"

        print("\n=== ALL LIVE PROPOSAL AUDIT ASSERTIONS PASSED PERFECTLY ===")

    finally:
        db.close()


if __name__ == "__main__":
    audit_project6_proposal()
