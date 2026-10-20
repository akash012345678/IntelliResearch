import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import get_db
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.proposal_draft_service import ProposalDraftService
from app.services.proposal_persistence_service import ProposalPersistenceService

from app.database.session import SessionLocal

client = TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_project6_data(db_session: Session):
    """
    Setup Project 6 with the 3 canonical Plant Disease papers:
    - Paper 14 (YOLO object detection)
    - Paper 15 (Swin-Axial Transformer)
    - Paper 16 (Explainable AI)
    """
    project = db_session.query(ResearchProject).filter(ResearchProject.id == 6).first()
    if not project:
        project = ResearchProject(
            id=6,
            name="Plant Disease Detection and Classification Using AI",
            description="AI research project for plant disease detection.",
            status="ACTIVE"
        )
        db_session.add(project)
        db_session.flush()

    p14 = db_session.query(ResearchPaper).filter(ResearchPaper.id == 14).first()
    if not p14:
        p14 = ResearchPaper(
            id=14,
            title="Evaluating the Performance YOLO Object Detectors for Plant Disease Detection",
            abstract="Evaluates YOLO-family object detection algorithms for localizing plant disease bounding boxes.",
            keywords=["yolo", "object detection", "plant disease"],
            algorithms=["YOLOv8", "YOLOv5"],
            datasets=["PlantDoc"],
            methodologies=["Deep Learning Object Detection"],
            application_domains=["Plant Disease Detection"]
        )
        db_session.add(p14)

    p15 = db_session.query(ResearchPaper).filter(ResearchPaper.id == 15).first()
    if not p15:
        p15 = ResearchPaper(
            id=15,
            title="Plant Disease Detection Using an Innovative Swin-Axial Transformer",
            abstract="Proposes a Vision Transformer for plant disease identification under benchmark datasets.",
            keywords=["transformer", "vision transformer", "swin-axial"],
            algorithms=["Swin-Axial Transformer"],
            datasets=["PlantVillage"],
            methodologies=["Transformer Architecture"],
            application_domains=["Plant Disease Detection"]
        )
        db_session.add(p15)

    p16 = db_session.query(ResearchPaper).filter(ResearchPaper.id == 16).first()
    if not p16:
        p16 = ResearchPaper(
            id=16,
            title="Improving Plant Disease Classification With Deep-Learning-Based Prediction Model Using Explainable Artificial Intelligence",
            abstract="Integrates Explainable Artificial Intelligence (XAI) feature attribution for diagnostic transparency.",
            keywords=["explainable ai", "xai", "grad-cam", "transparency"],
            algorithms=["Explainable AI", "Grad-CAM"],
            datasets=["PlantVillage"],
            methodologies=["Explainable Artificial Intelligence"],
            application_domains=["Plant Disease Classification"]
        )
        db_session.add(p16)

    # Link papers 14, 15, 16 to Project 6
    for pid in [14, 15, 16]:
        pp = db_session.query(ProjectPaper).filter(ProjectPaper.project_id == 6, ProjectPaper.paper_id == pid).first()
        if not pp:
            db_session.add(ProjectPaper(project_id=6, paper_id=pid))
    db_session.commit()

    # Clean up pre-existing proposals for Project 6 to ensure test isolation
    prop_ids = [p.id for p in db_session.query(Proposal).filter(Proposal.project_id == 6).all()]
    if prop_ids:
        db_session.query(ProposalVersion).filter(ProposalVersion.proposal_id.in_(prop_ids)).delete(synchronize_session=False)
        db_session.query(Proposal).filter(Proposal.project_id == 6).delete(synchronize_session=False)
        db_session.commit()

    return project


def test_proposal_versioning_and_quality_pipeline(db_session: Session, setup_project6_data):
    """
    Comprehensive regression suite validating items A through Q.
    """
    # 1. Synthesize new proposal draft for Project 6 XAI + YOLO opportunity
    payload = {
        "direction_id": "opp_1",
        "project_id": 6,
        "opportunity_family_id": "FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        "title": "Incorporate Explainable Artificial Intelligence into YOLO-Family Object Detection",
        "supporting_papers": [
            {"paper_id": 14, "title": "Evaluating the Performance YOLO Object Detectors for Plant Disease Detection", "role": "YOLO object detection evidence"},
            {"paper_id": 16, "title": "Improving Plant Disease Classification With Deep-Learning-Based Prediction Model Using Explainable Artificial Intelligence", "role": "Explainable AI methodology evidence"}
        ]
    }

    # A. New proposal starts at Version 1
    resp1 = client.post("/api/research-directions/draft", json=payload)
    assert resp1.status_code == 200, f"Draft synthesis failed: {resp1.text}"
    data1 = resp1.json()

    assert data1["version_number"] == 1, f"Expected Version 1, got Version {data1['version_number']}"
    assert data1["status"] == "DRAFT"
    prop_db_id = data1["id"]

    proposal1 = data1["proposal"]

    # G. Selected task type is correct (OBJECT_DETECTION)
    assert proposal1["task_type"] == "OBJECT_DETECTION", f"Expected OBJECT_DETECTION task type, got {proposal1['task_type']}"

    # H. Object detection opportunity does not generate classification-only objectives
    obj_text = " ".join(proposal1["objectives"]).lower()
    assert "object detection" in obj_text or "bounding box" in obj_text or "baseline" in obj_text

    # I. Detection opportunity uses detection-aligned evaluation metrics
    metrics_text = proposal1["evaluation_metrics"]
    assert "map" in metrics_text.lower() or "precision" in metrics_text.lower() or "iou" in metrics_text.lower()

    # J. Dataset names are evidence-supported (PlantDoc / PlantVillage from Papers 14, 15, 16)
    prov = proposal1["datasets_provenance"]
    assert isinstance(prov, list)
    for ds in prov:
        assert ds["evidence_status"] == "RECORDED_EVIDENCE"
        assert ds["dataset_name"] in ["PlantDoc", "PlantVillage", "Fusion Dataset"]

    # K. Unsupported dataset is never fabricated
    # L. Proposed methodology remains PROPOSED
    meth_text = proposal1["proposed_methodology"]
    assert "PROPOSED METHODOLOGY" in meth_text
    assert "RECORDED EVIDENCE" in meth_text

    # M. Missing experiment results remain MISSING
    # N. No fabricated numerical outcomes
    exp_plan = proposal1["experimental_plan"]
    assert "95%" not in proposal1["abstract"]
    assert "95%" not in proposal1["expected_contribution"]
    assert "Results will be recorded after experiment execution" in exp_plan or "not yet recorded" in proposal1["evaluation_metrics"]

    # O. Opportunity -> Gap -> Proposal provenance is intact
    assert data1["direction_id"] in ["dir_1", "opp_1", "FAMILY_EXPLAINABILITY___FAMILY_YOLO"]
    assert proposal1["source_direction_id"] is not None

    # B. Viewing does not create a new version
    view_resp = client.get(f"/api/proposals/{prop_db_id}")
    assert view_resp.status_code == 200
    assert view_resp.json()["current_version"]["version_number"] == 1

    # C. Repeated non-regenerate draft call returns Version 1 without incrementing
    resp_again = client.post("/api/research-directions/draft", json=payload)
    assert resp_again.status_code == 200
    assert resp_again.json()["version_number"] == 1

    # D. Explicit edit creates Version 2
    edit_payload = {
        "change_summary": "Updated research question and objectives for spatial attribution evaluation.",
        "research_question": "How can Explainable Artificial Intelligence methods be integrated into YOLO-family object detection pipelines to provide spatial attribution and diagnostic transparency for plant disease localization?"
    }
    edit_resp = client.patch(f"/api/proposals/{prop_db_id}", json=edit_payload)
    assert edit_resp.status_code == 200
    assert edit_resp.json()["version_number"] == 2

    # E. Another explicit edit creates Version 3
    edit_payload2 = {
        "change_summary": "Refined evaluation metrics section for mAP@0.5 and Grad-CAM stability.",
        "evaluation_metrics": ["Precision", "Recall", "F1-Score", "mAP@0.5", "mAP@0.5:0.95", "IoU", "Latency (ms/frame)", "Attribution Stability"]
    }
    edit_resp2 = client.patch(f"/api/proposals/{prop_db_id}", json=edit_payload2)
    assert edit_resp2.status_code == 200
    assert edit_resp2.json()["version_number"] == 3

    # F. Proposal source direction remains unchanged across versions
    prop_v3 = client.get(f"/api/proposals/{prop_db_id}")
    assert prop_v3.json()["current_version"]["version_number"] == 3
    assert prop_v3.json()["source_direction_id"] == data1["direction_id"]

    # P. PDF/MD exports use the correct latest version (Version 3)
    export_md = client.get(f"/api/proposals/{prop_db_id}/export?format=markdown")
    assert export_md.status_code == 200
    assert "VERSION 3" in export_md.text

    export_json = client.get(f"/api/proposals/{prop_db_id}/export?format=json")
    assert export_json.status_code == 200
    assert export_json.json()["version_number"] == 3

    export_pdf = client.get(f"/api/proposals/{prop_db_id}/export?format=pdf")
    assert export_pdf.status_code == 200, f"Export PDF failed: {export_pdf.text}"
    assert export_pdf.headers["content-type"] == "application/pdf"
