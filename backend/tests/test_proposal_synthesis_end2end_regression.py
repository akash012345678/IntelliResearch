import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.proposal_draft_service import ProposalDraftService
from app.schemas.research_direction_schema import ResearchDirection, ResearchDirectionEvidence, SupportingPaper, ResearchDirectionResponse


client = TestClient(app)


def cleanup_test_project(db: Session, proj_id: int):
    """Safely remove test project and all associated proposal versions and papers."""
    try:
        p_ids = [p.id for p in db.query(Proposal).filter(Proposal.project_id == proj_id).all()]
        if p_ids:
            db.query(ProposalVersion).filter(ProposalVersion.proposal_id.in_(p_ids)).delete(synchronize_session=False)
        db.query(Proposal).filter(Proposal.project_id == proj_id).delete(synchronize_session=False)
        db.query(ProjectPaper).filter(ProjectPaper.project_id == proj_id).delete(synchronize_session=False)
        db.query(ResearchProject).filter(ResearchProject.id == proj_id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()


def test_A_new_proposal_starts_at_version_1():
    """Test generating a brand new proposal starts at Version 1."""
    db = SessionLocal()
    proj = None
    try:
        # Create a temp project for isolated testing
        proj = ResearchProject(name="Test Versioning Project 1", description="Test")
        db.add(proj)
        db.commit()
        db.refresh(proj)

        # Attach Paper 14, 15, 16 to proj
        db.add(ProjectPaper(project_id=proj.id, paper_id=14))
        db.add(ProjectPaper(project_id=proj.id, paper_id=15))
        db.add(ProjectPaper(project_id=proj.id, paper_id=16))
        db.commit()

        resp = client.post(
            "/api/research-directions/draft",
            json={
                "direction_id": "dir_1",
                "project_id": proj.id
            }
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["version_number"] == 1, f"New proposal must start at Version 1, got {data['version_number']}"
    finally:
        if proj:
            cleanup_test_project(db, proj.id)
        db.close()


def test_B_C_viewing_and_refresh_does_not_create_new_version():
    """Test GET calls to view proposal or list versions do NOT create a new version."""
    db = SessionLocal()
    proj = None
    try:
        proj = ResearchProject(name="Test Versioning Project 2", description="Test")
        db.add(proj)
        db.commit()
        db.refresh(proj)

        db.add(ProjectPaper(project_id=proj.id, paper_id=14))
        db.add(ProjectPaper(project_id=proj.id, paper_id=15))
        db.add(ProjectPaper(project_id=proj.id, paper_id=16))
        db.commit()

        resp_create = client.post(
            "/api/research-directions/draft",
            json={"direction_id": "dir_1", "project_id": proj.id}
        )
        data = resp_create.json()
        p_id = data["id"]
        v_start = data["version_number"]

        # View call 1
        resp_view1 = client.get(f"/api/proposals/{p_id}")
        assert resp_view1.status_code == 200
        assert resp_view1.json()["current_version"]["version_number"] == v_start

        # View call 2 (refresh simulation)
        resp_view2 = client.get(f"/api/proposals/{p_id}")
        assert resp_view2.status_code == 200
        assert resp_view2.json()["current_version"]["version_number"] == v_start

        # View history call
        resp_hist = client.get(f"/api/proposals/{p_id}/versions")
        assert resp_hist.status_code == 200
        assert resp_hist.json()["total_versions"] == v_start
    finally:
        if proj:
            cleanup_test_project(db, proj.id)
        db.close()


def test_D_E_F_explicit_edit_creates_version_2_and_3():
    """Test explicit edit/patch requests create Version 2 and Version 3 while preserving source_direction_id."""
    db = SessionLocal()
    proj = None
    try:
        proj = ResearchProject(name="Test Versioning Project 3", description="Test")
        db.add(proj)
        db.commit()
        db.refresh(proj)

        db.add(ProjectPaper(project_id=proj.id, paper_id=14))
        db.add(ProjectPaper(project_id=proj.id, paper_id=15))
        db.add(ProjectPaper(project_id=proj.id, paper_id=16))
        db.commit()

        resp_create = client.post(
            "/api/research-directions/draft",
            json={"direction_id": "dir_1", "project_id": proj.id}
        )
        p_id = resp_create.json()["id"]

        # Edit 1 -> Version 2
        resp_edit1 = client.patch(
            f"/api/proposals/{p_id}",
            json={
                "title": "Updated Title Version 2",
                "change_summary": "Added refined methodology notes"
            }
        )
        assert resp_edit1.status_code == 200
        assert resp_edit1.json()["version_number"] == 2

        # Edit 2 -> Version 3
        resp_edit2 = client.patch(
            f"/api/proposals/{p_id}",
            json={
                "title": "Updated Title Version 3",
                "change_summary": "Refined experimental metrics"
            }
        )
        assert resp_edit2.status_code == 200
        assert resp_edit2.json()["version_number"] == 3

        # Verify source_direction_id remains unchanged across versions
        prop_db = db.query(Proposal).filter(Proposal.id == p_id).first()
        assert prop_db.source_direction_id == "dir_1"
        assert len(prop_db.versions) == 3
    finally:
        if proj:
            cleanup_test_project(db, proj.id)
        db.close()


def test_G_H_I_task_type_and_metrics_consistency():
    """Test Project 6 Opportunity #1 produces OBJECT_DETECTION task type and detection metrics."""
    db = SessionLocal()
    try:
        res = ProposalDraftService.synthesize_draft(db=db, direction_id="dir_1", project_id=6)
        p = res.proposal
        
        assert p.task_type == "OBJECT_DETECTION", f"Expected OBJECT_DETECTION, got {p.task_type}"
        assert "mAP" in p.evaluation_metrics, "Evaluation metrics must include mAP for object detection"
        assert "IoU" in p.evaluation_metrics, "Evaluation metrics must include IoU for object detection"
        assert "Precision" in p.evaluation_metrics
        assert "Recall" in p.evaluation_metrics

        # Objectives must focus on object detection / localization
        obj_text = " ".join(p.objectives).lower()
        assert "object detection" in obj_text or "localization" in obj_text
    finally:
        db.close()


def test_J_K_dataset_provenance_evidence_grounded():
    """Test datasets carry provenance and unsupported datasets are never fabricated."""
    db = SessionLocal()
    try:
        res = ProposalDraftService.synthesize_draft(db=db, direction_id="dir_1", project_id=6)
        p = res.proposal

        assert len(p.datasets_provenance) >= 1
        ds_names = [d["dataset_name"] for d in p.datasets_provenance]
        assert "PlantDoc" in ds_names or "PlantVillage" in ds_names, f"Expected PlantDoc or PlantVillage, got {ds_names}"
        
        for ds in p.datasets_provenance:
            assert "source_paper_ids" in ds
            assert len(ds["source_paper_ids"]) >= 1
            assert ds["evidence_status"] == "RECORDED_EVIDENCE"
    finally:
        db.close()


def test_L_M_N_proposed_methodology_and_no_fabricated_numbers():
    """Test methodology is marked PROPOSED and missing results are marked MISSING with zero fabricated numbers."""
    db = SessionLocal()
    try:
        res = ProposalDraftService.synthesize_draft(db=db, direction_id="dir_1", project_id=6)
        p = res.proposal

        assert "RECORDED EVIDENCE" in p.proposed_methodology
        assert "PROPOSED METHODOLOGY" in p.proposed_methodology
        assert "MISSING RESULTS" in p.proposed_methodology

        full_text = f"{p.abstract} {p.proposed_methodology} {p.expected_contribution} {p.limitations}".lower()
        
        # Ensure no unsupported global novelty words
        for bad_word in ["unprecedented", "first globally", "novel globally", "world-first"]:
            assert bad_word not in full_text
            
        # Ensure no fake accuracy percentage predictions
        assert "95%" not in full_text
        assert "99%" not in full_text
    finally:
        db.close()


def test_O_provenance_link_intact():
    """Test Opportunity -> Gap -> Proposal provenance chain is fully intact."""
    db = SessionLocal()
    try:
        res = ProposalDraftService.synthesize_draft(db=db, direction_id="dir_1", project_id=6)
        p = res.proposal

        assert p.source_direction_id == "dir_1"
        assert p.source_gap_id == "gap_1"
        assert len(p.supporting_papers) >= 2
        paper_ids = [sp["paper_id"] for sp in p.supporting_papers]
        assert 14 in paper_ids
        assert 16 in paper_ids
    finally:
        db.close()
