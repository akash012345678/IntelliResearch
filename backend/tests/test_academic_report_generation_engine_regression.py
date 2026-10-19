import pytest
from sqlalchemy.orm import Session
import fitz

from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection, ResearchExperiment, ExperimentRun, ExperimentResult
from app.models.paper_model import ResearchPaper
from app.services.academic_report_content_builder import AcademicReportContentBuilder
from app.services.academic_report_validator import AcademicReportValidator
from app.services.academic_report_pdf_engine import AcademicReportPdfEngine
from app.services.project_research_report_service import ProjectResearchReportService


def test_academic_report_content_builder_generic(db_session: Session):
    # 1. Setup synthetic generic project (Project B - NLP Sentiment Domain)
    proj = ResearchProject(
        name="NLP Financial Sentiment Transformer Analysis",
        description="Transformer architectures for financial sentiment classification",
        status="ACTIVE"
    )
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)

    paper = ResearchPaper(
        title="FinBERT: Financial Sentiment Analysis with Pre-trained Language Models",
        filename="finbert_2020.pdf",
        full_text="Financial sentiment analysis using FinBERT pretrained transformer models on Financial PhraseBank.",
        algorithms=["BERT", "FinBERT"],
        datasets=["Financial PhraseBank"],
        tasks=["Sentiment Classification"],
        application_domains=["Finance", "NLP"],
        keywords=["Transformer", "Sentiment Analysis", "Financial NLP"]
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)

    pp = ProjectPaper(project_id=proj.id, paper_id=paper.id)
    db_session.add(pp)

    sd = SavedResearchDirection(
        project_id=proj.id,
        source_direction_id="dir_fin_1",
        title="Domain-Adapted FinBERT Attention Scaling",
        direction_data={
            "direction_id": "dir_fin_1",
            "title": "Domain-Adapted FinBERT Attention Scaling",
            "summary": "Attention head scaling for financial sentiment text"
        }
    )
    db_session.add(sd)
    db_session.commit()

    # 2. Build Content
    content = AcademicReportContentBuilder.build_report_content(db=db_session, project_id=proj.id, direction_id="dir_fin_1")

    assert content["meta"]["project_id"] == proj.id
    assert content["meta"]["active_direction_title"] == "Domain-Adapted FinBERT Attention Scaling"
    assert content["meta"]["has_empirical_results"] is False

    # 3. Validate zero-fabrication
    validation = AcademicReportValidator.validate_report_content(content, db=db_session)
    assert validation["is_valid_for_export"] is True

    # 4. Render PDF
    engine = AcademicReportPdfEngine(report_content=content, db=db_session)
    pdf_bytes = engine.generate_pdf()

    assert pdf_bytes.startswith(b"%PDF-")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) >= 5  # Must render front matter + chapters


def test_direction_isolation_in_report_builder(db_session: Session):
    proj = ResearchProject(name="Multi-Direction Research Project", description="Computer Vision Models", status="ACTIVE")
    db_session.add(proj)
    db_session.commit()

    sd1 = SavedResearchDirection(
        project_id=proj.id,
        source_direction_id="dir_1",
        title="YOLOv8 Edge Lightweight Pruning",
        direction_data={"direction_id": "dir_1", "title": "YOLOv8 Edge Lightweight Pruning"}
    )
    sd2 = SavedResearchDirection(
        project_id=proj.id,
        source_direction_id="dir_2",
        title="Vision Transformer Cross-Attention Enhancement",
        direction_data={"direction_id": "dir_2", "title": "Vision Transformer Cross-Attention Enhancement"}
    )
    db_session.add_all([sd1, sd2])
    db_session.commit()

    content1 = AcademicReportContentBuilder.build_report_content(db=db_session, project_id=proj.id, direction_id="dir_1")
    content2 = AcademicReportContentBuilder.build_report_content(db=db_session, project_id=proj.id, direction_id="dir_2")

    assert "YOLOv8" in content1["meta"]["active_direction_title"]
    assert "Vision Transformer" in content2["meta"]["active_direction_title"]
    assert content1["meta"]["active_direction_title"] != content2["meta"]["active_direction_title"]


def test_zero_results_and_empirical_results_rendering(db_session: Session):
    proj = ResearchProject(name="Empirical Results Verification Project", description="Testing Results Table", status="ACTIVE")
    db_session.add(proj)
    db_session.commit()

    exp = ResearchExperiment(
        project_id=proj.id,
        direction_id="dir_exp_1",
        name="Accuracy Benchmark Experiment",
        status="COMPLETED"
    )
    db_session.add(exp)
    db_session.commit()

    # Case A: 0 results
    content_no_res = AcademicReportContentBuilder.build_report_content(db=db_session, project_id=proj.id, direction_id="dir_exp_1")
    assert content_no_res["meta"]["has_empirical_results"] is False
    assert len(content_no_res["ch6"]["res_table_rows"]) == 0

    # Case B: Add actual empirical result row to DB
    run = ExperimentRun(experiment_id=exp.id, run_number=1)
    db_session.add(run)
    db_session.commit()

    res = ExperimentResult(
        run_id=run.id,
        metric_name="F1-Score",
        metric_value="0.942",
        unit="Ratio",
        method_type="proposed"
    )
    db_session.add(res)
    db_session.commit()

    content_with_res = AcademicReportContentBuilder.build_report_content(db=db_session, project_id=proj.id, direction_id="dir_exp_1")
    assert content_with_res["meta"]["has_empirical_results"] is True
    assert len(content_with_res["ch6"]["res_table_rows"]) == 1
    assert "0.942" in content_with_res["ch6"]["res_table_rows"][0][4]
