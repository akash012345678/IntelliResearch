import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection, ResearchExperiment
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal, ProposalVersion

client = TestClient(app)


def test_get_project_traceability_success(db_session: Session):
    # Setup test project
    project = ResearchProject(name="Traceability Test Project", description="Testing dynamic traceability pipeline")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # Setup test paper
    paper = ResearchPaper(
        title="Traceability Test Paper on Neural Networks",
        abstract="Test paper abstract",
        full_text="Complete text of test paper for neural networks",
        filename="test_paper.pdf"
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)

    # Assign paper to project
    pp = ProjectPaper(project_id=project.id, paper_id=paper.id)
    db_session.add(pp)

    # Setup test saved direction / plan
    plan = SavedResearchDirection(
        project_id=project.id,
        source_direction_id="dir_1",
        title="Proposed Neural Architecture Direction",
        confidence="High",
        direction_data={
            "direction_id": "dir_1",
            "baseline_methods": [{"name": "Standard CNN"}],
            "proposed_architecture": "ResNet-Attention Hybrid",
            "candidate_datasets": [{"name": "Benchmark Dataset"}]
        }
    )
    db_session.add(plan)

    # Setup test proposal
    proposal = Proposal(
        proposal_uuid=f"test-prop-uuid-{project.id}",
        project_id=project.id,
        source_direction_id="dir_1",
        title="Proposed Neural Architecture Direction Proposal",
        status="DRAFT"
    )
    db_session.add(proposal)
    db_session.commit()
    db_session.refresh(proposal)

    pv = ProposalVersion(
        proposal_id=proposal.id,
        version_number=1,
        proposal_data={"title": proposal.title},
        generation_mode="template"
    )
    db_session.add(pv)
    db_session.commit()

    # Call API
    response = client.get(f"/api/projects/{project.id}/traceability")
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == project.id
    assert data["project_name"] == "Traceability Test Project"
    assert "summary" in data
    assert data["summary"]["total_papers"] >= 1
    assert "chains" in data
    assert len(data["chains"]) >= 1

    first_chain = data["chains"][0]
    assert first_chain["opportunity"]["direction_id"] is not None
    assert first_chain["plan"]["status"] in ["SAVED", "NOT_CREATED"]
    assert first_chain["results"]["completion_status"] in ["RECORDED", "RESULTS_NOT_RECORDED"]
    assert first_chain["proposal"]["title"] is not None


def test_get_project_traceability_not_found():
    response = client.get("/api/projects/999999/traceability")
    assert response.status_code == 404
