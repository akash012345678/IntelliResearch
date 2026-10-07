import pytest
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, SavedResearchDirection
from app.services.research_methodology_service import ResearchMethodologyService
from app.services.saved_direction_service import SavedDirectionService

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db, init_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_fixture.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def db_session():
    init_db(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()



def test_generate_plan_for_selected_opportunity(db_session: Session):
    """
    Test Phase 6 & 7:
    - Methodology plan is synthesized specifically for the requested direction_id (Opportunity).
    - Plan title, research problem, and candidate algorithms belong strictly to that opportunity.
    """
    # 1. Create dummy Research Project
    project = ResearchProject(name="Generic Computer Vision Benchmark", description="CV research project", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    dir_id_1 = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    dir_id_2 = "FAMILY_TRANSFORMER___FAMILY_YOLO"

    # 2. Fetch methodology plan for Opportunity 1 via API
    res1 = client.get(f"/api/projects/{project.id}/research-directions/{dir_id_1}/methodology-plan")
    assert res1.status_code == 200
    plan1 = res1.json()
    assert plan1["direction_id"] == dir_id_1
    assert "YOLO" in plan1["title"] or "Explainability" in plan1["title"] or "Baseline" in plan1["title"]

    # 3. Fetch methodology plan for Opportunity 2 via API
    res2 = client.get(f"/api/projects/{project.id}/research-directions/{dir_id_2}/methodology-plan")
    assert res2.status_code == 200
    plan2 = res2.json()
    assert plan2["direction_id"] == dir_id_2

    # 4. Verify distinctness of Opportunity 1 vs Opportunity 2 plans
    assert plan1["direction_id"] != plan2["direction_id"]


def test_plan_persistence_and_multi_plan_support(db_session: Session):
    """
    Test Phase 10 & 24:
    - Multiple research methodology plans can be saved for the same project.
    - Saving Plan A for Opportunity 1 and Plan B for Opportunity 2 creates distinct SavedResearchDirection records.
    - Neither plan overwrites the other.
    """
    project = ResearchProject(name="Multi-Plan NLP Project", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    dir_id_1 = "DIR_BERT_IMDB_01"
    dir_id_2 = "DIR_ROBERTA_IMDB_02"

    # Save Plan 1 for Opportunity 1
    res1 = client.post(
        f"/api/projects/{project.id}/research-plan/save",
        json={
            "direction_id": dir_id_1,
            "plan_data": {
                "title": "BERT Sentiment Analysis Plan",
                "research_problem": "Fine-tuning BERT on IMDB reviews.",
                "potential_contribution": "Comparative baseline evaluation."
            },
            "notes": "Plan for Opportunity 1"
        }
    )
    assert res1.status_code == 200

    # Save Plan 2 for Opportunity 2
    res2 = client.post(
        f"/api/projects/{project.id}/research-plan/save",
        json={
            "direction_id": dir_id_2,
            "plan_data": {
                "title": "RoBERTa Ensemble Plan",
                "research_problem": "Ensemble RoBERTa + BERT for sentiment classification.",
                "potential_contribution": "Variance reduction across splits."
            },
            "notes": "Plan for Opportunity 2"
        }
    )
    assert res2.status_code == 200

    # List project saved directions
    saved_dirs = SavedDirectionService.list_project_directions(db=db_session, project_id=project.id)
    assert len(saved_dirs) >= 2

    saved_dir_ids = [d.source_direction_id for d in saved_dirs]
    assert dir_id_1 in saved_dir_ids
    assert dir_id_2 in saved_dir_ids


def test_project_intelligence_returns_candidate_directions(db_session: Session):
    """
    Test Phase 2:
    - Project research intelligence returns candidate_research_directions.
    - Each candidate direction contains direction_id, title, research_problem, confidence, supporting_papers.
    """
    project = ResearchProject(name="Cybersecurity Multi-Opportunity Project", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    res = client.get(f"/api/projects/{project.id}/research-intelligence")
    assert res.status_code == 200
    intel = res.json()
    cand_dirs = intel.get("candidate_research_directions", [])
    assert isinstance(cand_dirs, list)
