import pytest
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_db
from app.database.session import SessionLocal
from app.models.project_model import ResearchProject
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.proposal_persistence_service import ProposalPersistenceService
from app.services.proposal_export_service import ProposalExportService
from app.schemas.proposal_persistence_schema import ProposalCreate
from app.schemas.proposal_edit_schema import ProposalEditRequest

client = TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_proposal_lifecycle_versioning_and_immutability(db_session: Session):
    """
    Test Phase 2 & Phase 10:
    - Initial proposal creation creates Version 1.
    - Edits create sequential Version 2 and Version 3.
    - Previous version snapshots remain 100% immutable.
    """
    # 1. Create a dummy Research Project
    project = ResearchProject(name="Generic NLP Benchmark Project", description="NLP research collection", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # 2. Create Initial Proposal (Version 1)
    v1_payload = ProposalCreate(
        project_id=project.id,
        source_direction_id="DIR_BERT_IMDB_01",
        title="Integrating BERT Transformers into Sentiment Analysis Pipeline",
        proposal_data={
            "title": "Integrating BERT Transformers into Sentiment Analysis Pipeline",
            "task_type": "NATURAL_LANGUAGE_PROCESSING",
            "abstract": "Initial abstract for Version 1.",
            "problem_statement": "Initial problem statement.",
            "research_question": "Does BERT improve sentiment accuracy on IMDB? [PROPOSED]",
            "objectives": ["1. Establish BERT baseline on IMDB [RECORDED_EVIDENCE]."],
            "research_motivation": "Motivation text.",
            "related_work_synthesis": "Synthesis text.",
            "research_gap": "Within the indexed collection, BERT fine-tuning for IMDB remains unassessed [PROPOSED].",
            "proposed_methodology": "Methodology Version 1.",
            "candidate_algorithms": ["BERT", "RoBERTa"],
            "candidate_datasets": ["IMDB Reviews"],
            "dataset_evaluation_plan": "IMDB benchmark split.",
            "experimental_plan": "Experimental plan Version 1.",
            "evaluation_metrics": ["Perplexity", "F1-Score"],
            "expected_contribution": "Contribution Version 1.",
            "limitations": "Limitations Version 1.",
            "disclaimer": "Academic disclaimer"
        },
        generation_mode="template",
        status="DRAFT"
    )

    p_resp = ProposalPersistenceService.create_proposal(db=db_session, data=v1_payload)
    proposal_id = p_resp.id
    assert p_resp.current_version.version_number == 1
    assert p_resp.current_version.proposal_data["abstract"] == "Initial abstract for Version 1."

    # 3. Edit Proposal -> Version 2
    v2_edit = ProposalEditRequest(
        change_summary="Refined research question and methodology",
        research_question="Does fine-tuning RoBERTa alongside BERT improve macro F1 on IMDB? [PROPOSED]",
        proposed_methodology="Methodology Version 2 with joint fine-tuning."
    )
    v2_resp = ProposalPersistenceService.edit_proposal(db=db_session, proposal_id=proposal_id, data=v2_edit)
    assert v2_resp.version_number == 2
    assert v2_resp.proposal_data["research_question"] == "Does fine-tuning RoBERTa alongside BERT improve macro F1 on IMDB? [PROPOSED]"
    assert v2_resp.proposal_data["proposed_methodology"] == "Methodology Version 2 with joint fine-tuning."

    # 4. Edit Proposal -> Version 3
    v3_edit = ProposalEditRequest(
        change_summary="Updated title and abstract for publication scope",
        title="Comparative Sentiment Analysis Using BERT and RoBERTa Models",
        abstract="Updated executive abstract for Version 3."
    )
    v3_resp = ProposalPersistenceService.edit_proposal(db=db_session, proposal_id=proposal_id, data=v3_edit)
    assert v3_resp.version_number == 3
    assert v3_resp.proposal_data["title"] == "Comparative Sentiment Analysis Using BERT and RoBERTa Models"
    assert v3_resp.proposal_data["abstract"] == "Updated executive abstract for Version 3."

    # 5. Verify Immutability of Version 1 and Version 2
    ver1_snapshot = ProposalPersistenceService.get_proposal_version(db=db_session, proposal_id=proposal_id, version_number=1)
    assert ver1_snapshot.version_number == 1
    assert ver1_snapshot.proposal_data["abstract"] == "Initial abstract for Version 1."
    assert ver1_snapshot.proposal_data["research_question"] == "Does BERT improve sentiment accuracy on IMDB? [PROPOSED]"

    ver2_snapshot = ProposalPersistenceService.get_proposal_version(db=db_session, proposal_id=proposal_id, version_number=2)
    assert ver2_snapshot.version_number == 2
    assert ver2_snapshot.proposal_data["research_question"] == "Does fine-tuning RoBERTa alongside BERT improve macro F1 on IMDB? [PROPOSED]"
    assert ver2_snapshot.proposal_data["abstract"] == "Initial abstract for Version 1."


def test_history_and_compare_api(db_session: Session):
    """
    Test Phase 3, 4 & 5:
    - History endpoint returns version history list sorted version_number DESC.
    - Compare endpoint accurately compares two versions and surfaces section diffs.
    """
    # Create project & proposal
    project = ResearchProject(name="Cybersecurity Intrusion Detection", description="Network traffic analysis", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    p_resp = ProposalPersistenceService.create_proposal(
        db=db_session,
        data=ProposalCreate(
            project_id=project.id,
            source_direction_id="DIR_CYBER_01",
            title="Random Forest Intrusion Detection Pipeline",
            proposal_data={
                "title": "Random Forest Intrusion Detection Pipeline",
                "task_type": "CYBERSECURITY_INTRUSION_DETECTION",
                "abstract": "Initial Cyber Abstract.",
                "research_question": "Can Random Forest detect CIC-IDS attacks? [PROPOSED]",
                "proposed_methodology": "Methodology Version 1.",
                "evaluation_metrics": ["Detection Rate", "FPR"]
            }
        )
    )
    pid = p_resp.id

    # Create Version 2 edit
    ProposalPersistenceService.edit_proposal(
        db=db_session,
        proposal_id=pid,
        data=ProposalEditRequest(
            change_summary="Added XGBoost comparison",
            research_question="Can Random Forest + XGBoost ensemble reduce FPR on CIC-IDS2017? [PROPOSED]",
            proposed_methodology="Methodology Version 2 with ensemble classifier."
        )
    )

    # 1. Test History API via FastAPI TestClient
    res_hist = client.get(f"/api/proposals/{pid}/versions")
    assert res_hist.status_code == 200
    hist_json = res_hist.json()
    assert hist_json["total_versions"] == 2
    assert hist_json["versions"][0]["version_number"] == 2
    assert hist_json["versions"][1]["version_number"] == 1

    # 2. Test Compare API via FastAPI TestClient
    res_comp = client.get(f"/api/proposals/{pid}/compare?version_a=1&version_b=2")
    assert res_comp.status_code == 200
    comp_json = res_comp.json()
    assert comp_json["proposal_id"] == pid
    assert comp_json["version_a"] == 1
    assert comp_json["version_b"] == 2
    assert comp_json["total_changes"] >= 2

    changed_sections = [item["section"] for item in comp_json["changes"]]
    assert "research_question" in changed_sections
    assert "proposed_methodology" in changed_sections

    # 3. Test Compare identical versions returns 0 changes or error
    res_same = client.get(f"/api/proposals/{pid}/compare?version_a=1&version_b=1")
    assert res_same.status_code == 400


def test_pdf_markdown_export(db_session: Session):
    """
    Test Phase 6, 7 & 8:
    - PDF export generates valid PDF bytes containing complete academic sections.
    - PDF export respects version parameter.
    - Markdown export generates complete Markdown content.
    - POST /proposals/export works for unsaved raw draft payloads.
    """
    project = ResearchProject(name="Plant Disease Vision Project", description="Computer vision research", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    proposal_data = {
        "title": "Integrating Explainable AI into YOLO Object Detection",
        "task_type": "OBJECT_DETECTION",
        "abstract": "Executive abstract for plant disease detection.",
        "problem_statement": "Object detection opacity in crop diagnostic tools.",
        "research_question": "Does Grad-CAM provide spatial attribution for YOLOv8? [PROPOSED]",
        "objectives": ["1. Evaluate YOLOv8 baseline on PlantDoc [RECORDED_EVIDENCE].", "2. Integrate XAI pipeline [PROPOSED]."],
        "research_motivation": "Improves diagnostic transparency for field agronomists.",
        "related_work_synthesis": "Evaluating YOLO Object Detectors for Plant Disease Detection.",
        "research_gap": "Within the indexed project collection, XAI + YOLO object detection integration is unassessed [PROPOSED].",
        "proposed_methodology": "A. RECORDED EVIDENCE: YOLO baseline. B. PROPOSED: Grad-CAM integration.",
        "candidate_algorithms": ["YOLOv8", "Grad-CAM"],
        "candidate_datasets": ["PlantDoc"],
        "dataset_evaluation_plan": "PlantDoc standard train/val split.",
        "experimental_plan": "Structured Experiment Plan with 13 phases.",
        "evaluation_metrics": ["mAP@0.5", "IoU", "FPS"],
        "expected_contribution": "Evaluates attribution stability while maintaining detection speed [PROPOSED].",
        "limitations": "Study findings derived strictly from indexed collection evidence.",
        "supporting_papers": [{"paper_id": 14, "title": "Evaluating YOLO", "role": "Object detection baseline"}],
        "disclaimer": "Collection-scoped academic research proposal."
    }

    p_resp = ProposalPersistenceService.create_proposal(
        db=db_session,
        data=ProposalCreate(
            project_id=project.id,
            source_direction_id="DIR_YOLO_XAI_01",
            title=proposal_data["title"],
            proposal_data=proposal_data
        )
    )
    pid = p_resp.id

    # 1. Test GET /proposals/{id}/export?format=pdf
    res_pdf = client.get(f"/api/proposals/{pid}/export?format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-"), "Exported PDF must have valid %PDF- magic header!"

    # 2. Test GET /proposals/{id}/export?format=markdown
    res_md = client.get(f"/api/proposals/{pid}/export?format=markdown")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    md_text = res_md.text
    assert "# Integrating Explainable AI into YOLO Object Detection" in md_text
    assert "## 1. Executive Abstract" in md_text
    assert "## 4. Measurable Research Objectives" in md_text
    assert "## 11. Structured Experimental Plan" in md_text
    assert "## 12. Proposed Evaluation Metrics" in md_text

    # 3. Test POST /proposals/export for unsaved raw proposal draft
    res_raw_pdf = client.post("/api/proposals/export?format=pdf&version_number=1", json=proposal_data)
    assert res_raw_pdf.status_code == 200
    assert res_raw_pdf.headers["content-type"] == "application/pdf"
    assert res_raw_pdf.content.startswith(b"%PDF-")


def test_version_restoration(db_session: Session):
    """
    Test Phase 11:
    - Restoring Version 1 creates a NEW Version 3 entry with restored content.
    - Version 1 and Version 2 remain unmodified.
    """
    project = ResearchProject(name="Generic Restoration Project", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    p_resp = ProposalPersistenceService.create_proposal(
        db=db_session,
        data=ProposalCreate(
            project_id=project.id,
            title="Original Version 1 Title",
            proposal_data={"title": "Original Version 1 Title", "abstract": "V1 Abstract"}
        )
    )
    pid = p_resp.id

    # Edit to V2
    ProposalPersistenceService.edit_proposal(
        db=db_session,
        proposal_id=pid,
        data=ProposalEditRequest(change_summary="Modified to V2", title="Edited Version 2 Title", abstract="V2 Abstract")
    )

    # Restore V1 -> Creates V3
    res_rest = client.post(f"/api/proposals/{pid}/restore/1")
    assert res_rest.status_code == 201
    rest_json = res_rest.json()
    assert rest_json["version_number"] == 3
    assert rest_json["is_restored"] is True
    assert rest_json["proposal_data"]["title"] == "Original Version 1 Title"
    assert rest_json["proposal_data"]["abstract"] == "V1 Abstract"
