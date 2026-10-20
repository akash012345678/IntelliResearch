import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project_model import ResearchProject

client = TestClient(app)


class TestProposalNormalizationAndCrashPrevention:
    """
    Regression Test Suite for Proposal Data Normalization & Crash Prevention (Requirement #13).
    Ensures that proposal list, workspaces, export service, and version management
    never fail or crash when proposal fields are missing, null, legacy, or incomplete.
    """

    def test_case_1_missing_proposal_title(self, db_session: Session):
        """Case 1: proposal.title is missing/undefined."""
        proj = ResearchProject(name="Test Project Case 1", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        post_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "title": "Untitled Draft",
            "proposal_data": {"abstract": "Test abstract", "problem_statement": "Test problem"},
            "generation_mode": "template",
            "status": "DRAFT"
        })
        assert post_res.status_code == 201
        p_id = post_res.json()["id"]

        res = client.get(f"/api/projects/{proj.id}/proposals")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == p_id

    def test_case_2_missing_related_work(self, db_session: Session):
        """Case 2: proposal.relatedWork is missing/undefined."""
        proj = ResearchProject(name="Test Project Case 2", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        post_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "title": "Proposal Without Related Work",
            "proposal_data": {
                "abstract": "Abstract text",
                "problem_statement": "Problem text"
                # related_work_synthesis intentionally omitted
            },
            "generation_mode": "template",
            "status": "DRAFT"
        })
        assert post_res.status_code == 201
        p_id = post_res.json()["id"]

        # Test GET single proposal
        res = client.get(f"/api/proposals/{p_id}")
        assert res.status_code == 200
        p_data = res.json()["current_version"]["proposal_data"]
        assert "related_work_synthesis" not in p_data or p_data.get("related_work_synthesis") is None

        # Test Markdown Export handles missing related work cleanly
        exp_res = client.get(f"/api/proposals/{p_id}/export?format=markdown")
        assert exp_res.status_code == 200
        assert "Related Work Synthesis" in exp_res.text

    def test_case_3_missing_supporting_papers(self, db_session: Session):
        """Case 3: proposal.supportingPapers is missing/undefined/null."""
        proj = ResearchProject(name="Test Project Case 3", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        post_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "title": "Proposal Without Supporting Papers",
            "proposal_data": {
                "title": "Proposal Without Supporting Papers",
                "supporting_papers": None
            },
            "generation_mode": "template",
            "status": "DRAFT"
        })
        assert post_res.status_code == 201
        p_id = post_res.json()["id"]

        res = client.get(f"/api/proposals/{p_id}")
        assert res.status_code == 200

        exp_res = client.get(f"/api/proposals/{p_id}/export?format=pdf")
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 100

    def test_case_4_missing_references(self, db_session: Session):
        """Case 4: proposal.references is missing/undefined/null."""
        proj = ResearchProject(name="Test Project Case 4", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        post_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "title": "Proposal Without References",
            "proposal_data": {
                "title": "Proposal Without References",
                "references": None
            },
            "generation_mode": "template",
            "status": "DRAFT"
        })
        assert post_res.status_code == 201
        p_id = post_res.json()["id"]

        res = client.get(f"/api/proposals/{p_id}")
        assert res.status_code == 200

    def test_case_5_legacy_version_missing_several_fields(self, db_session: Session):
        """Case 5: Legacy proposal version missing several fields."""
        proj = ResearchProject(name="Test Project Case 5", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        post_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "title": "Legacy Minimal Proposal",
            "proposal_data": {"abstract": "Legacy abstract only"},
            "generation_mode": "template",
            "status": "DRAFT"
        })
        assert post_res.status_code == 201
        p_id = post_res.json()["id"]

        # Version history fetch
        res = client.get(f"/api/proposals/{p_id}/versions")
        assert res.status_code == 200
        assert res.json()["total_versions"] == 1

        # Specific version fetch
        ver_res = client.get(f"/api/proposals/{p_id}/versions/1")
        assert ver_res.status_code == 200
        assert ver_res.json()["version_number"] == 1

    def test_case_6_api_returns_null_fields(self, db_session: Session):
        """Case 6: Proposal API returns null values for optional attributes."""
        proj = ResearchProject(name="Test Project Case 6", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        post_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "source_direction_id": None,
            "title": "Null Field Testing Proposal",
            "proposal_data": {
                "title": "Null Field Testing Proposal",
                "objectives": None,
                "candidate_algorithms": None,
                "candidate_datasets": None,
                "evaluation_metrics": None,
                "evidence_summary": None
            },
            "generation_mode": "template",
            "status": "DRAFT"
        })
        assert post_res.status_code == 201
        p_id = post_res.json()["id"]

        res = client.get(f"/api/proposals/{p_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["source_direction_id"] is None
        assert data["current_version"]["proposal_data"]["objectives"] is None

    def test_case_7_zero_proposals(self, db_session: Session):
        """Case 7: Project with zero proposals returns empty list cleanly."""
        proj = ResearchProject(name="Empty Project Case 7", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        res = client.get(f"/api/projects/{proj.id}/proposals")
        assert res.status_code == 200
        assert res.json() == []

    def test_case_8_valid_complete_proposal(self, db_session: Session):
        """Case 8: Valid complete proposal with editing and version comparison."""
        proj = ResearchProject(name="Complete Project Case 8", status="ACTIVE")
        db_session.add(proj)
        db_session.commit()
        db_session.refresh(proj)

        # Create proposal
        create_res = client.post("/api/proposals", json={
            "project_id": proj.id,
            "source_direction_id": "dir_full",
            "title": "Complete Multi-Version Proposal",
            "proposal_data": {
                "title": "Complete Multi-Version Proposal",
                "abstract": "Initial abstract V1",
                "problem_statement": "Initial problem V1",
                "candidate_algorithms": ["YOLOv8", "ResNet50"],
                "candidate_datasets": ["PlantDoc"],
                "evaluation_metrics": ["Precision", "Recall", "F1-Score"]
            },
            "generation_mode": "template"
        })
        assert create_res.status_code == 201
        p_id = create_res.json()["id"]

        # Edit proposal to create V2
        edit_res = client.patch(f"/api/proposals/{p_id}", json={
            "change_summary": "Updated abstract and added XAI",
            "abstract": "Updated abstract V2 with XAI attribution",
            "candidate_algorithms": ["YOLOv8", "Swin-Transformer"]
        })
        assert edit_res.status_code == 200
        assert edit_res.json()["version_number"] == 2

        # Compare V1 vs V2
        comp_res = client.get(f"/api/proposals/{p_id}/compare?version_a=1&version_b=2")
        assert comp_res.status_code == 200
        cmp_data = comp_res.json()
        assert cmp_data["total_changes"] >= 1

        # Restore V1
        rest_res = client.post(f"/api/proposals/{p_id}/restore/1")
        assert rest_res.status_code == 201
        assert rest_res.json()["version_number"] == 3
