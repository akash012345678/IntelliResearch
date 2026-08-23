import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app as fastapi_app
from app.database.session import SessionLocal, Base, engine
from app.models.paper_model import ResearchPaper
from app.models.project_model import ResearchProject, ProjectPaper
from app.schemas.project_schema import ResearchProjectCreate, BulkAddPapersRequest
from app.services.research_project_service import ResearchProjectService
from app.services.project_intelligence_service import ProjectIntelligenceService
import app.models  # Ensure all models register with Base.metadata


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.session import get_db

TEST_ENGINE = create_engine(
    "sqlite:///./test_fixture.db",
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db
client = TestClient(fastapi_app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestSessionLocal()
    db.query(ProjectPaper).delete()
    db.query(ResearchProject).delete()
    db.query(ResearchPaper).delete()
    db.commit()
    yield db
    db.query(ProjectPaper).delete()
    db.query(ResearchProject).delete()
    db.query(ResearchPaper).delete()
    db.commit()
    db.close()


def create_test_paper(db: Session, title: str, abstract: str = "Abstract text", filename: str = "paper.pdf",
                      keywords=None, algorithms=None, datasets=None, methodologies=None, domains=None):
    paper = ResearchPaper(
        title=title,
        abstract=abstract,
        full_text="Full text content for paper " + title,
        filename=filename,
        keywords=keywords or ["AI", "Driver Safety"],
        algorithms=algorithms or ["CNN", "YOLO"],
        datasets=datasets or ["KITTI"],
        methodologies=methodologies or ["Deep Learning"],
        application_domains=domains or ["Autonomous Driving"]
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


def create_test_project(db: Session, name: str = "Test Project"):
    return ResearchProjectService.create_project(db, ResearchProjectCreate(name=name, description="Desc"))


class TestProjectPaperManagement:

    def test_01_get_project_papers_listing(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Driver Drowsiness Detection with CNN", keywords=["Drowsiness"])
        proj = create_test_project(db, "Safety Project")

        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)

        response = client.get(f"/api/projects/{proj.id}/papers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        paper_item = data[0]
        assert paper_item["paper_id"] == p1.id
        assert paper_item["title"] == "Driver Drowsiness Detection with CNN"
        assert paper_item["abstract"] == "Abstract text"
        assert paper_item["keywords"] == ["Drowsiness"]
        assert paper_item["algorithms"] == ["CNN", "YOLO"]
        assert paper_item["filename"] == "paper.pdf"
        assert "uploaded_at" in paper_item

    def test_02_add_valid_paper_to_project(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Lane Detection Systems")
        proj = create_test_project(db, "Vision Project")

        response = client.post(f"/api/projects/{proj.id}/papers/{p1.id}")
        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == proj.id
        assert data["paper_id"] == p1.id
        assert data["title"] == "Lane Detection Systems"

    def test_03_add_non_existent_paper(self, setup_db):
        db = setup_db
        proj = create_test_project(db)

        response = client.post(f"/api/projects/{proj.id}/papers/99999")
        assert response.status_code == 404
        assert "Paper 99999 not found" in response.json()["detail"]

    def test_04_add_paper_to_non_existent_project(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Traffic Light Classification")

        response = client.post(f"/api/projects/99999/papers/{p1.id}")
        assert response.status_code == 404
        assert "Project 99999 not found" in response.json()["detail"]

    def test_05_duplicate_assignment_rejection(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Object Tracking")
        proj = create_test_project(db)

        client.post(f"/api/projects/{proj.id}/papers/{p1.id}")
        response = client.post(f"/api/projects/{proj.id}/papers/{p1.id}")
        assert response.status_code == 400
        assert "already assigned" in response.json()["detail"]

    def test_06_remove_paper_from_project(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Pedestrian Detection")
        proj = create_test_project(db)

        client.post(f"/api/projects/{proj.id}/papers/{p1.id}")

        del_res = client.delete(f"/api/projects/{proj.id}/papers/{p1.id}")
        assert del_res.status_code == 204

        papers_res = client.get(f"/api/projects/{proj.id}/papers")
        assert len(papers_res.json()) == 0

    def test_07_verify_research_paper_still_exists_after_removal(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Lidar Point Cloud Segmentation")
        proj = create_test_project(db)

        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)
        ResearchProjectService.remove_paper_from_project(db, proj.id, p1.id)

        # Original paper record MUST exist in database
        db_paper = db.query(ResearchPaper).filter(ResearchPaper.id == p1.id).first()
        assert db_paper is not None
        assert db_paper.title == "Lidar Point Cloud Segmentation"

    def test_08_bulk_assignment(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Paper A")
        p2 = create_test_paper(db, "Paper B")
        proj = create_test_project(db)

        payload = {"paper_ids": [p1.id, p2.id]}
        response = client.post(f"/api/projects/{proj.id}/papers/bulk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["added"] == [p1.id, p2.id]
        assert data["already_assigned"] == []
        assert data["not_found"] == []

    def test_09_bulk_duplicate_and_missing_handling(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Paper 1")
        p2 = create_test_paper(db, "Paper 2")
        proj = create_test_project(db)

        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)

        payload = {"paper_ids": [p1.id, p2.id, 9999]}
        response = client.post(f"/api/projects/{proj.id}/papers/bulk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["added"] == [p2.id]
        assert data["already_assigned"] == [p1.id]
        assert data["not_found"] == [9999]

    def test_10_available_papers_excludes_assigned(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Assigned Paper")
        p2 = create_test_paper(db, "Unassigned Paper")
        proj = create_test_project(db)

        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)

        response = client.get(f"/api/projects/{proj.id}/available-papers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == p2.id
        assert data[0]["title"] == "Unassigned Paper"

    def test_11_available_papers_search_and_filtering(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Deep Learning for Drowsiness", keywords=["Fatigue"], algorithms=["ResNet"])
        p2 = create_test_paper(db, "Transformer Traffic Analysis", keywords=["Flow"], algorithms=["BERT"])
        proj = create_test_project(db)

        # Title search
        res1 = client.get(f"/api/projects/{proj.id}/available-papers?search=Drowsiness")
        assert res1.status_code == 200
        assert len(res1.json()) == 1
        assert res1.json()[0]["id"] == p1.id

        # Algorithm filter
        res2 = client.get(f"/api/projects/{proj.id}/available-papers?algorithm=BERT")
        assert res2.status_code == 200
        assert len(res2.json()) == 1
        assert res2.json()[0]["id"] == p2.id

    def test_12_project_intelligence_changes_after_adding_removing_papers(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Paper 1")
        p2 = create_test_paper(db, "Paper 2")
        proj = create_test_project(db)

        # 0 papers initially
        intel0 = ProjectIntelligenceService.analyze_project(proj.id, db)
        assert intel0.collection_summary.total_papers == 0

        # Add paper 1
        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)
        intel1 = ProjectIntelligenceService.analyze_project(proj.id, db)
        assert intel1.collection_summary.total_papers == 1

        # Add paper 2
        ResearchProjectService.add_paper_to_project(db, proj.id, p2.id)
        intel2 = ProjectIntelligenceService.analyze_project(proj.id, db)
        assert intel2.collection_summary.total_papers == 2

        # Remove paper 1
        ResearchProjectService.remove_paper_from_project(db, proj.id, p1.id)
        intel3 = ProjectIntelligenceService.analyze_project(proj.id, db)
        assert intel3.collection_summary.total_papers == 1

    def test_13_project_deletion_does_not_delete_research_papers(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Permanent Paper")
        proj = create_test_project(db)

        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)
        ResearchProjectService.delete_project(db, proj.id)

        # ResearchPaper MUST still exist
        p_check = db.query(ResearchPaper).filter(ResearchPaper.id == p1.id).first()
        assert p_check is not None

    def test_14_global_paper_collection_remains_unchanged(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Global Paper A")
        p2 = create_test_paper(db, "Global Paper B")
        proj = create_test_project(db)

        total_before = db.query(ResearchPaper).count()
        ResearchProjectService.add_paper_to_project(db, proj.id, p1.id)
        ResearchProjectService.remove_paper_from_project(db, proj.id, p1.id)
        total_after = db.query(ResearchPaper).count()

        assert total_before == total_after == 2

    def test_15_database_transaction_rollback(self, setup_db):
        db = setup_db
        proj = create_test_project(db)

        # Attempt to add non-existent paper, verify db remains valid and clean
        with pytest.raises(Exception):
            ResearchProjectService.add_paper_to_project(db, proj.id, 99999)

        # Confirm session is responsive and clean
        assert db.query(ProjectPaper).count() == 0
