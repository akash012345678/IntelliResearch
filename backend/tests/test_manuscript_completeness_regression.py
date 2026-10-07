import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.project_model import (
    Base,
    ResearchProject,
    ResearchManuscript,
    ResearchManuscriptVersion,
    ResearchExperiment,
    ExperimentRun,
    ExperimentResult
)
from app.schemas.academic_manuscript_schema import ManuscriptSectionItem
from app.services.academic_manuscript_service import AcademicManuscriptService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def create_dummy_project(db, name="Test Project"):
    project = ResearchProject(name=name, description="Test project description")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_case_1_all_sections_missing(db_session):
    """CASE 1: All sections missing => 0% Manuscript Completion & Evidence Completeness."""
    project = create_dummy_project(db_session, "Empty Project")
    sections = [
        ManuscriptSectionItem(
            section_key="TITLE", title="Title", student_label="Title",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        ),
        ManuscriptSectionItem(
            section_key="ABSTRACT", title="Abstract", student_label="Abstract",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        ),
        ManuscriptSectionItem(
            section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        )
    ]
    completeness = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, sections)
    assert completeness.manuscript_completion_percentage == 0
    assert completeness.evidence_completeness_percentage == 0
    assert completeness.manuscript_completion_label == "STARTING"
    assert completeness.evidence_rating_label == "STARTING"


def test_case_2_only_front_matter(db_session):
    """CASE 2: Only title/abstract/keywords populated => low completeness."""
    project = create_dummy_project(db_session, "Front Matter Only Project")
    sections = [
        ManuscriptSectionItem(
            section_key="TITLE", title="Title Page", student_label="Title Page",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Project Title Page Content"
        ),
        ManuscriptSectionItem(
            section_key="ABSTRACT", title="Abstract", student_label="Abstract",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Abstract text for paper"
        ),
        ManuscriptSectionItem(
            section_key="KEYWORDS", title="Keywords", student_label="Keywords",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="AI, ML, Data"
        ),
        # All core and empirical sections missing
        ManuscriptSectionItem(
            section_key="INTRODUCTION", title="Intro", student_label="Intro",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        ),
        ManuscriptSectionItem(
            section_key="METHODOLOGY", title="Methodology", student_label="Methodology",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        ),
        ManuscriptSectionItem(
            section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        ),
        ManuscriptSectionItem(
            section_key="CONCLUSION", title="Conclusion", student_label="Conclusion",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content=""
        )
    ]
    completeness = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, sections)
    assert 0 < completeness.manuscript_completion_percentage < 25
    assert completeness.manuscript_completion_label == "STARTING"


def test_case_3_proposal_no_results(db_session):
    """CASE 3: Literature + methodology + proposal generated, but no experiment results => moderate evidence score, high manuscript completion."""
    project = create_dummy_project(db_session, "Proposal Stage Project")
    sections = [
        ManuscriptSectionItem(
            section_key="TITLE", title="Title Page", student_label="Title Page",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Project Title Content"
        ),
        ManuscriptSectionItem(
            section_key="ABSTRACT", title="Abstract", student_label="Abstract",
            evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Abstract proposal statement text..."
        ),
        ManuscriptSectionItem(
            section_key="INTRODUCTION", title="Intro", student_label="Intro",
            evidence_level="DERIVED", evidence_badge_text="🟡 DERIVED", content="Intro text for domain context..."
        ),
        ManuscriptSectionItem(
            section_key="LITERATURE_REVIEW", title="Lit Review", student_label="Lit Review",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Synthesized literature review content..."
        ),
        ManuscriptSectionItem(
            section_key="METHODOLOGY", title="Methodology", student_label="Methodology",
            evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Proposed methodology pipeline structure..."
        ),
        ManuscriptSectionItem(
            section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results",
            evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content="Experimental results will be reported upon completion of baseline and proposed runs."
        ),
        ManuscriptSectionItem(
            section_key="CONCLUSION", title="Conclusion", student_label="Conclusion",
            evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Proposed conclusion summary statements..."
        )
    ]
    completeness = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, sections)
    assert completeness.manuscript_completion_percentage >= 85
    assert 25 <= completeness.evidence_completeness_percentage <= 65
    assert completeness.manuscript_completion_label in ["HIGHLY COMPLETE", "NEAR COMPLETE", "COMPLETE"]
    assert completeness.evidence_rating_label in ["PARTIAL", "IN PROGRESS"]


def test_manuscript_completion_vs_evidence_completeness_divergence(db_session):
    """
    Test requirement:
    Manuscript Completion may be > 85% while Evidence Completeness is < 60% (e.g. 53%).
    Proves planned methodology, introduction, literature review, objectives, and experimental setup
    count as 100% structurally complete for Manuscript Completion while Evidence Completeness remains strictly grounded.
    """
    project = create_dummy_project(db_session, "Divergence Project")
    # 0 DB result rows!
    sections = [
        ManuscriptSectionItem(section_key="TITLE", title="Title Page", student_label="Title", evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Empirical Study Title"),
        ManuscriptSectionItem(section_key="ABSTRACT", title="Abstract", student_label="Abstract", evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Abstract text explaining proposed framework..."),
        ManuscriptSectionItem(section_key="INTRODUCTION", title="Intro", student_label="Intro", evidence_level="DERIVED", evidence_badge_text="🟡 DERIVED", content="Structured domain introduction..."),
        ManuscriptSectionItem(section_key="LITERATURE_REVIEW", title="Lit", student_label="Lit", evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Literature synthesis..."),
        ManuscriptSectionItem(section_key="METHODOLOGY", title="Method", student_label="Method", evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Proposed methodology pipeline..."),
        ManuscriptSectionItem(section_key="EXPERIMENTAL_SETUP", title="Setup", student_label="Setup", evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Planned PyTorch hardware setup..."),
        ManuscriptSectionItem(section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results", evidence_level="MISSING", evidence_badge_text="🔴 MISSING", content="Experimental results will be reported upon execution."),
        ManuscriptSectionItem(section_key="CONCLUSION", title="Conclusion", student_label="Conclusion", evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Proposed research summary...")
    ]

    score = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, sections)

    assert score.manuscript_completion_percentage >= 85
    assert score.evidence_completeness_percentage < 60
    assert score.manuscript_completion_label in ["HIGHLY COMPLETE", "NEAR COMPLETE", "COMPLETE"]
    assert score.evidence_rating_label in ["PARTIAL", "IN PROGRESS"]


def test_strict_zero_results_forces_zero_empirical_score(db_session):
    """
    STRICT RULE TEST:
    Even if an empirical section contains generated narrative, predicted metrics, or expected outcomes,
    if DB has ZERO empirical result rows, the evidence score MUST be 0.0.
    """
    project = create_dummy_project(db_session, "Zero Result Rows With Generated Narrative")
    exp = ResearchExperiment(project_id=project.id, name="Exp 1", status="COMPLETED")
    db_session.add(exp)
    db_session.commit()

    sections = [
        ManuscriptSectionItem(
            section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results",
            evidence_level="DERIVED", evidence_badge_text="🟡 DERIVED",
            content="The model architecture is predicted to achieve 95% accuracy based on prior literature estimates."
        ),
        ManuscriptSectionItem(
            section_key="COMPARATIVE_RESULTS", title="Comparative", student_label="Comparative",
            evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED",
            content="Planned comparisons compare YOLO vs Baseline CNN."
        ),
        ManuscriptSectionItem(
            section_key="STATISTICAL_ANALYSIS", title="Statistical", student_label="Statistical",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED",
            content="Hypothesis testing framework designed for 5-fold cross validation."
        ),
        ManuscriptSectionItem(
            section_key="ABLATION_STUDY", title="Ablation", student_label="Ablation",
            evidence_level="DERIVED", evidence_badge_text="🟡 DERIVED",
            content="Component ablation removes attention blocks sequentially."
        ),
        ManuscriptSectionItem(
            section_key="ERROR_ANALYSIS", title="Error Analysis", student_label="Error Analysis",
            evidence_level="DERIVED", evidence_badge_text="🟡 DERIVED",
            content="Failure modes are expected under low lighting conditions."
        )
    ]
    completeness = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, sections)
    assert completeness.evidence_completeness_percentage == 0
    assert completeness.evidence_rating_label == "STARTING"
    assert completeness.experimental_result_sections_count == 0


def test_case_5_real_results_recorded(db_session):
    """CASE 5: Real experiment result rows recorded => Evidence Completeness increases."""
    project = create_dummy_project(db_session, "Real Results Project")
    exp = ResearchExperiment(project_id=project.id, name="Exp 1", status="COMPLETED")
    db_session.add(exp)
    db_session.commit()

    run = ExperimentRun(experiment_id=exp.id, run_number=1)
    db_session.add(run)
    db_session.commit()

    res = ExperimentResult(run_id=run.id, metric_name="Accuracy", metric_value="0.94")
    db_session.add(res)
    db_session.commit()

    sections = [
        ManuscriptSectionItem(
            section_key="TITLE", title="Title", student_label="Title",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Title content"
        ),
        ManuscriptSectionItem(
            section_key="LITERATURE_REVIEW", title="Lit", student_label="Lit",
            evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Lit content"
        ),
        ManuscriptSectionItem(
            section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results",
            evidence_level="EXPERIMENTAL_RESULT", evidence_badge_text="📊 RESULT", content="Accuracy: 0.94"
        ),
        ManuscriptSectionItem(
            section_key="COMPARATIVE_RESULTS", title="Comparative", student_label="Comparative",
            evidence_level="EXPERIMENTAL_RESULT", evidence_badge_text="📊 RESULT", content="Proposed vs Baseline"
        )
    ]
    completeness = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, sections)
    assert completeness.evidence_completeness_percentage == 100
    assert completeness.manuscript_completion_percentage == 100
    assert completeness.evidence_rating_label == "COMPLETE"
    assert completeness.experimental_result_sections_count == 2


def test_case_8_version_handling(db_session):
    """CASE 8: Version 1 and Version 2 with different evidence => different completeness scores."""
    project = create_dummy_project(db_session, "Multi-version Project")
    v1_sections = [
        ManuscriptSectionItem(section_key="TITLE", title="Title", student_label="Title", evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Title content"),
        ManuscriptSectionItem(section_key="INTRODUCTION", title="Intro", student_label="Intro", evidence_level="PROPOSED", evidence_badge_text="🔵 PROPOSED", content="Intro draft content")
    ]
    v2_sections = [
        ManuscriptSectionItem(section_key="TITLE", title="Title", student_label="Title", evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Title verified content"),
        ManuscriptSectionItem(section_key="INTRODUCTION", title="Intro", student_label="Intro", evidence_level="RECORDED_EVIDENCE", evidence_badge_text="🟢 RECORDED", content="Intro verified content")
    ]

    c1 = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, v1_sections)
    c2 = AcademicManuscriptService.calculate_manuscript_completeness(db_session, project.id, v2_sections)

    assert c1.evidence_completeness_percentage < c2.evidence_completeness_percentage
    assert c1.evidence_completeness_percentage == 50
    assert c2.evidence_completeness_percentage == 100


def test_case_9_multi_project_generic(db_session):
    """CASE 9: Project A and Project B with different evidence => different scores using same algorithm."""
    proj_a = create_dummy_project(db_session, "Project A")
    proj_b = create_dummy_project(db_session, "Project B")

    exp_b = ResearchExperiment(project_id=proj_b.id, name="Exp B", status="COMPLETED")
    db_session.add(exp_b)
    db_session.commit()
    run_b = ExperimentRun(experiment_id=exp_b.id, run_number=1)
    db_session.add(run_b)
    db_session.commit()
    res_b = ExperimentResult(run_id=run_b.id, metric_name="Accuracy", metric_value="0.88")
    db_session.add(res_b)
    db_session.commit()

    same_sections = [
        ManuscriptSectionItem(section_key="EXPERIMENTAL_RESULTS", title="Results", student_label="Results", evidence_level="EXPERIMENTAL_RESULT", evidence_badge_text="📊 RESULT", content="Results content details")
    ]

    score_a = AcademicManuscriptService.calculate_manuscript_completeness(db_session, proj_a.id, same_sections)
    score_b = AcademicManuscriptService.calculate_manuscript_completeness(db_session, proj_b.id, same_sections)

    assert score_a.evidence_completeness_percentage < score_b.evidence_completeness_percentage
    assert score_a.evidence_completeness_percentage == 0
    assert score_b.evidence_completeness_percentage == 100


def test_case_10_no_hardcoding():
    """CASE 10: Verify no project-specific hardcoded strings exist in completeness logic."""
    import inspect
    code = inspect.getsource(AcademicManuscriptService.calculate_manuscript_completeness)
    code_completion = inspect.getsource(AcademicManuscriptService.calculate_manuscript_completion)
    forbidden_terms = ["dir_1", "dir_2", "dir_3", "yolo", "xai", "plant disease", "project 6"]
    for term in forbidden_terms:
        assert term not in code.lower(), f"Forbidden hardcoded term '{term}' found in completeness calculation!"
        assert term not in code_completion.lower(), f"Forbidden hardcoded term '{term}' found in completion calculation!"
