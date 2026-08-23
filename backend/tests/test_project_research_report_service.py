import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, Base, engine
from app.models.paper_model import ResearchPaper
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.project_research_report_service import ProjectResearchReportService
from app.schemas.project_report_schema import ProjectResearchReportResponse
import app.models  # Ensure all models register with Base.metadata


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_ENGINE = create_engine(
    "sqlite:///./test_fixture.db",
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestSessionLocal()
    db.query(ProposalVersion).delete()
    db.query(Proposal).delete()
    db.query(ProjectPaper).delete()
    db.query(ResearchProject).delete()
    db.query(ResearchPaper).delete()
    db.commit()
    yield db
    db.close()



def create_test_paper(db: Session, title: str, algorithms=None, datasets=None, methodologies=None, domains=None, keywords=None):
    p = ResearchPaper(
        title=title,
        abstract=f"Abstract for {title}",
        full_text=f"Full text for {title}",
        filename=f"{title.lower().replace(' ', '_')}.pdf",
        keywords=keywords or ["AI", "Safety"],
        algorithms=algorithms or ["CNN"],
        datasets=datasets or ["KITTI"],
        methodologies=methodologies or ["Deep Learning"],
        application_domains=domains or ["Automotive"]
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def create_test_project(db: Session, name="Test Project"):
    proj = ResearchProject(name=name, description="Test Description", status="ACTIVE")
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


class TestProjectResearchReportService:

    def test_01_empty_project_report(self, setup_db):
        db = setup_db
        proj = create_test_project(db, "Empty Report Project")

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        assert isinstance(report, ProjectResearchReportResponse)
        assert report.project.project_id == proj.id
        assert report.collection_summary["total_papers"] == 0
        assert "Insufficient evidence" in report.research_problem_summary.summary_text
        assert len(report.paper_landscape) == 0
        assert len(report.evidence_traceability) == 0

    def test_02_single_paper_project_report(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Single Paper Alpha", algorithms=["Transformer"], domains=["NLP"])
        proj = create_test_project(db, "Single Paper Project")
        assign_paper(db, proj.id, p1.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        assert report.collection_summary["total_papers"] == 1
        assert len(report.paper_landscape) == 1
        assert report.paper_landscape[0]["id"] == p1.id
        assert len(report.evidence_traceability) == 1
        assert report.evidence_traceability[0].paper_id == p1.id

    def test_03_multi_paper_project_report(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Paper A", algorithms=["CNN"])
        p2 = create_test_paper(db, "Paper B", algorithms=["CNN", "LSTM"])
        p3 = create_test_paper(db, "Paper C", algorithms=["GNN"])
        proj = create_test_project(db, "Multi Paper Project")
        assign_paper(db, proj.id, p1.id)
        assign_paper(db, proj.id, p2.id)
        assign_paper(db, proj.id, p3.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        assert report.collection_summary["total_papers"] == 3
        assert len(report.paper_landscape) == 3

    def test_04_project_scope_isolation(self, setup_db):
        db = setup_db
        p_assigned = create_test_paper(db, "Assigned Paper")
        p_unassigned = create_test_paper(db, "Global Unassigned Paper")

        proj = create_test_project(db, "Scoped Project")
        assign_paper(db, proj.id, p_assigned.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        assert report.collection_summary["total_papers"] == 1
        paper_ids = [pl["id"] for pl in report.paper_landscape]
        assert p_assigned.id in paper_ids
        assert p_unassigned.id not in paper_ids

    def test_05_shared_concept_aggregation(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "P1", algorithms=["ResNet"], datasets=["ImageNet"])
        p2 = create_test_paper(db, "P2", algorithms=["ResNet"], datasets=["COCO"])
        proj = create_test_project(db)
        assign_paper(db, proj.id, p1.id)
        assign_paper(db, proj.id, p2.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        alg_names = [it["name"] if isinstance(it, dict) else str(it) for it in report.shared_concepts.get("algorithms", [])]
        assert "ResNet" in alg_names

    def test_06_proposal_traceability(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Trace Paper", algorithms=["YOLO"])
        proj = create_test_project(db)
        assign_paper(db, proj.id, p1.id)

        prop = Proposal(
            proposal_uuid="prop_123",
            project_id=proj.id,
            title="YOLO Safety Proposal"
        )
        db.add(prop)
        db.commit()

        v1 = ProposalVersion(
            proposal_id=prop.id,
            version_number=1,
            proposal_data={"supporting_papers": [{"paper_id": p1.id}]}
        )
        db.add(v1)
        db.commit()

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        assert len(report.proposal_summary) == 1
        assert report.proposal_summary[0].proposal_id == "prop_123"


        tr_item = [t for t in report.evidence_traceability if t.paper_id == p1.id][0]
        assert tr_item.proposal is not None
        assert tr_item.proposal.proposal_id == "prop_123"

    def test_07_export_markdown_generation(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "MD Paper")
        proj = create_test_project(db)
        assign_paper(db, proj.id, p1.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        md_text = ProjectResearchReportService.export_report_to_markdown(report)
        assert "# Project Research Report" in md_text
        assert "MD Paper" in md_text
        assert "Executive Collection Summary" in md_text

    def test_08_export_json_generation(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "JSON Paper")
        proj = create_test_project(db)
        assign_paper(db, proj.id, p1.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        json_str = ProjectResearchReportService.export_report_to_json(report)
        assert '"project_id":' in json_str
        assert "JSON Paper" in json_str

    def test_09_export_pdf_generation(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "PDF Paper")
        proj = create_test_project(db)
        assign_paper(db, proj.id, p1.id)

        report = ProjectResearchReportService.generate_project_report(proj.id, db)
        pdf_bytes = ProjectResearchReportService.export_report_to_pdf(report)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_10_database_immutability(self, setup_db):
        db = setup_db
        p1 = create_test_paper(db, "Immutability Paper")
        proj = create_test_project(db)
        assign_paper(db, proj.id, p1.id)

        paper_count_before = db.query(ResearchPaper).count()
        proj_count_before = db.query(ResearchProject).count()
        assoc_count_before = db.query(ProjectPaper).count()

        _ = ProjectResearchReportService.generate_project_report(proj.id, db)

        assert db.query(ResearchPaper).count() == paper_count_before
        assert db.query(ResearchProject).count() == proj_count_before
        assert db.query(ProjectPaper).count() == assoc_count_before
