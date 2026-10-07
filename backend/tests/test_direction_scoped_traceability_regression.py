import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project_model import (
    ResearchProject,
    ProjectPaper,
    SavedResearchDirection,
    ResearchExperiment,
    ExperimentRun,
    ExperimentResult
)
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.project_traceability_service import ProjectTraceabilityService

client = TestClient(app)


def test_direction_scoped_traceability_chain_isolation(db_session: Session):
    """
    Regression Test for Direction-Scoped Traceability Isolation:
    Proves that for a project with multiple directions (dir_1, dir_2, dir_3):
    - dir_1 has Plan = NOT_CREATED, Experiments = 0, Proposal = NOT_CREATED
    - dir_3 has Plan = SAVED, Experiments = 3, Proposal = DRAFT
    - dir_3 chain displays dir_3's plan, experiments, and proposal, and NEVER displays dir_1's data or defaults.
    - dir_1 chain displays dir_1's own status without inheriting dir_3 data.
    """
    # 1. Create project
    project = ResearchProject(name="Multi-Direction Scoping Test Project", description="Testing dir_1 vs dir_3 traceability isolation")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # 2. Add paper to project
    paper = ResearchPaper(
        title="Multi-Direction Evidence Paper",
        abstract="Test abstract for multi-direction scoping",
        full_text="Complete text covering plant disease prediction models",
        filename="plant_test.pdf"
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)

    pp = ProjectPaper(project_id=project.id, paper_id=paper.id)
    db_session.add(pp)
    db_session.commit()

    # 3. Create saved plan strictly for dir_3
    plan_dir3 = SavedResearchDirection(
        project_id=project.id,
        source_direction_id="dir_3",
        title="Saved Plan for Direction 3",
        confidence="High",
        direction_data={
            "direction_id": "dir_3",
            "methodology_plan": {
                "direction_id": "dir_3",
                "title": "Saved Plan for Direction 3",
                "baseline_methods": [{"name": "YOLOv5 Baseline"}],
                "proposed_architecture": "Swin-Axial Transformer Hybrid",
                "candidate_datasets": [{"name": "PlantVillage Dataset"}]
            }
        }
    )
    db_session.add(plan_dir3)
    db_session.commit()

    # 4. Create 3 experiments strictly for dir_3
    for i in range(1, 4):
        exp = ResearchExperiment(
            project_id=project.id,
            direction_id="dir_3",
            name=f"Dir3 Experiment #{i}",
            purpose=f"Testing dir_3 hypothesis #{i}",
            experiment_type="ABLATION",
            status="PLANNED" if i < 3 else "COMPLETED",
            baseline_config={"algorithm": "YOLOv5"},
            proposed_config={"architecture": "Swin-Axial Transformer"}
        )
        db_session.add(exp)
    db_session.commit()

    # 5. Create proposal draft strictly for dir_3
    prop_dir3 = Proposal(
        proposal_uuid=f"uuid-dir3-prop-{project.id}",
        project_id=project.id,
        source_direction_id="dir_3",
        title="Proposal for Direction 3",
        status="DRAFT"
    )
    db_session.add(prop_dir3)
    db_session.commit()
    db_session.refresh(prop_dir3)

    pv_dir3 = ProposalVersion(
        proposal_id=prop_dir3.id,
        version_number=1,
        proposal_data={"title": prop_dir3.title},
        generation_mode="auto_synthesis"
    )
    db_session.add(pv_dir3)
    db_session.commit()

    # 6. Call Traceability API
    response = client.get(f"/api/projects/{project.id}/traceability")
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == project.id
    chains = data["chains"]
    assert len(chains) >= 1

    # Find dir_3 chain and dir_1 chain
    chain_dir3 = next((c for c in chains if c["opportunity"]["direction_id"] == "dir_3"), None)
    chain_dir1 = next((c for c in chains if c["opportunity"]["direction_id"] == "dir_1"), None)

    # 7. Verify dir_3 chain contains dir_3 data ONLY
    assert chain_dir3 is not None, "dir_3 chain must be present in traceability response"
    assert chain_dir3["opportunity"]["direction_id"] == "dir_3"
    assert chain_dir3["plan"]["status"] == "SAVED"
    assert chain_dir3["plan"]["methodology_title"] == "Saved Plan for Direction 3"
    assert len(chain_dir3["experiments"]) == 3
    assert chain_dir3["proposal"]["is_created"] is True
    assert chain_dir3["proposal"]["proposal_id"] == prop_dir3.id
    assert chain_dir3["proposal"]["title"] == "Proposal for Direction 3"
    assert len(chain_dir3["versions"]) >= 1

    # 8. Verify dir_1 chain (if generated) does NOT leak dir_3 data
    if chain_dir1:
        assert chain_dir1["opportunity"]["direction_id"] == "dir_1"
        assert chain_dir1["plan"]["status"] == "NOT_CREATED"
        assert len(chain_dir1["experiments"]) == 0
        assert chain_dir1["proposal"]["is_created"] is False
        assert chain_dir1["proposal"]["title"] == "Proposal Not Created Yet"
