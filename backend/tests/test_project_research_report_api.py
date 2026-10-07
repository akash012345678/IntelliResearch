import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app as fastapi_app
from app.models.paper_model import ResearchPaper
from app.models.project_model import ResearchProject, ProjectPaper

client = TestClient(fastapi_app)


def create_test_paper(db: Session, title: str):
    p = ResearchPaper(
        title=title,
        abstract=f"Abstract for {title}",
        full_text=f"Full text for {title}",
        filename=f"{title.lower().replace(' ', '_')}.pdf",
        keywords=["AI", "Vision"],
        algorithms=["CNN"],
        datasets=["MNIST"],
        methodologies=["Supervised"],
        application_domains=["Image Processing"]
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def create_test_project(db: Session, name="API Test Project"):
    proj = ResearchProject(name=name, description="API Test Description", status="ACTIVE")
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def assign_paper(db: Session, project_id: int, paper_id: int):
    pp = ProjectPaper(project_id=project_id, paper_id=paper_id)
    db.add(pp)
    db.commit()
    db.refresh(pp)
    return pp


class TestProjectResearchReportAPI:

    def test_01_get_report_success(self, db_session: Session):
        p1 = create_test_paper(db_session, "API Paper 1")
        proj = create_test_project(db_session, "Report API Project")
        assign_paper(db_session, proj.id, p1.id)

        response = client.get(f"/api/projects/{proj.id}/research-report")
        assert response.status_code == 200
        data = response.json()
        assert data["project"]["project_id"] == proj.id
        assert data["collection_summary"]["total_papers"] == 1
        assert "research_problem_summary" in data
        assert "evidence_traceability" in data

    def test_02_get_report_non_existent_project(self, db_session: Session):
        response = client.get("/api/projects/999999/research-report")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_03_get_report_with_query_filters(self, db_session: Session):
        p1 = create_test_paper(db_session, "Filtered Paper")
        proj = create_test_project(db_session)
        assign_paper(db_session, proj.id, p1.id)

        response = client.get(
            f"/api/projects/{proj.id}/research-report?include_proposals=false&include_relationships=false&include_gaps=false&include_directions=false"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["proposal_summary"] == []
        assert data["paper_relationships"] == []
        assert data["research_gaps"] == []
        assert data["candidate_research_directions"] == []

    def test_04_export_markdown(self, db_session: Session):
        p1 = create_test_paper(db_session, "Export MD Paper")
        proj = create_test_project(db_session)
        assign_paper(db_session, proj.id, p1.id)

        response = client.get(f"/api/projects/{proj.id}/research-report/export?format=markdown")
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert "# Project Research Report" in response.text

    def test_05_export_json(self, db_session: Session):
        p1 = create_test_paper(db_session, "Export JSON Paper")
        proj = create_test_project(db_session)
        assign_paper(db_session, proj.id, p1.id)

        response = client.get(f"/api/projects/{proj.id}/research-report/export?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert data["project"]["project_id"] == proj.id

    def test_06_export_pdf(self, db_session: Session):
        p1 = create_test_paper(db_session, "Export PDF Paper")
        proj = create_test_project(db_session)
        assign_paper(db_session, proj.id, p1.id)

        response = client.get(f"/api/projects/{proj.id}/research-report/export?format=pdf")
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert response.content.startswith(b"%PDF")

    def test_07_export_invalid_format(self, db_session: Session):
        proj = create_test_project(db_session)

        response = client.get(f"/api/projects/{proj.id}/research-report/export?format=invalid_fmt")
        assert response.status_code == 422
        assert "unsupported export format" in response.json()["detail"].lower()
