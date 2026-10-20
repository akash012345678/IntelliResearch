import pytest
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.schemas.research_direction_schema import (
    ResearchDirection,
    SupportingPaper,
    CandidateAlgorithm,
    CandidateDataset,
    ResearchDirectionEvidence
)
from app.services.proposal_draft_service import ProposalDraftService


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_dataset_provenance_does_not_leak(db_session: Session):
    """
    Test 1 & 8: Verify that datasets from unrelated papers (e.g., Paper 15) do NOT leak
    into proposals synthesized for an opportunity supported only by Paper 14 and Paper 16.
    """
    # Create mock papers
    paper14 = ResearchPaper(
        id=14,
        title="Evaluating the Performance YOLO Object Detectors for Plant Disease Detection",
        datasets=["PlantDoc"],
        algorithms=["YOLOv8"],
        methodologies=["Object Detection"],
        application_domains=["Plant Pathology"]
    )
    paper15 = ResearchPaper(
        id=15,
        title="Transformer-Based Architecture for Plant Disease Classification",
        datasets=["Multi-Source Benchmark Dataset"],
        algorithms=["Vision Transformer"],
        methodologies=["Classification"],
        application_domains=["Plant Pathology"]
    )
    paper16 = ResearchPaper(
        id=16,
        title="Improving Plant Disease Classification With Deep-Learning-Based Prediction Model Using Explainable Artificial Intelligence",
        datasets=["PlantVillage"],
        algorithms=["Explainable AI"],
        methodologies=["Saliency Maps"],
        application_domains=["Plant Pathology"]
    )
    project_papers = [paper14, paper15, paper16]

    # Direction supported strictly by Paper 14 and Paper 16
    dir_item = ResearchDirection(
        direction_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        opportunity_family_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        parent_gap_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        gap_relationship_key="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        title="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
        research_problem="Integration of XAI into YOLO object detection pipelines.",
        motivation="Evaluate spatial attribution and detection accuracy.",
        existing_evidence=["Indexed paper evidence."],
        missing_aspect="XAI integration with YOLO object detection.",
        proposed_direction="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
        supporting_papers=[
            SupportingPaper(paper_id=14, title=paper14.title, role="YOLO baseline"),
            SupportingPaper(paper_id=16, title=paper16.title, role="XAI methodology")
        ],
        supporting_concepts=["Explainable AI", "YOLO"],
        candidate_algorithms=[
            CandidateAlgorithm(name="YOLOv8", supporting_paper_count=1, reason="Baseline detector"),
            CandidateAlgorithm(name="Grad-CAM", supporting_paper_count=1, reason="Saliency map")
        ],
        candidate_datasets=[
            CandidateDataset(name="PlantDoc", supporting_paper_count=1, reason="Evidenced in Paper 14"),
            CandidateDataset(name="PlantVillage", supporting_paper_count=1, reason="Evidenced in Paper 16"),
            CandidateDataset(name="Multi-Source Benchmark Dataset", supporting_paper_count=1, reason="Evidenced in Paper 15 (Unrelated)")
        ],
        candidate_methodologies=[],
        evidence=ResearchDirectionEvidence(
            gap_score=0.88,
            opportunity_score=0.88,
            semantic_evidence=0.1,
            link_prediction_score=0.8,
            collection_coverage=66.7,
            underrepresentation_score=0.4,
            evidence_classification="QUALIFIED_POTENTIAL_GAP"
        ),
        direction_score=0.88,
        confidence="High",
        disclaimer="Test disclaimer"
    )

    draft = ProposalDraftService._template_synthesis(dir_item=dir_item, project_papers=project_papers)

    # Candidate datasets MUST NOT contain Multi-Source Benchmark Dataset from Paper 15!
    cand_ds = draft.candidate_datasets
    assert "PlantDoc" in cand_ds, "PlantDoc must be included (evidenced in Paper 14)."
    assert "PlantVillage" in cand_ds, "PlantVillage must be included (evidenced in Paper 16)."
    assert "Multi-Source Benchmark Dataset" not in cand_ds, "Dataset from Paper 15 must NOT leak into proposal supported only by Papers 14 and 16."

    # Verify provenance objects
    prov = draft.datasets_provenance
    assert len(prov) == 2, f"Expected exactly 2 datasets in provenance, found {len(prov)}."
    prov_names = [p["dataset_name"] for p in prov]
    assert "Multi-Source Benchmark Dataset" not in prov_names


def test_status_classifications_and_no_fabricated_numbers():
    """
    Test 2, 3, 4 & 9: Verify evidence status classification rules (RECORDED, DERIVED, PROPOSED, MISSING)
    and ensure zero global novelty terms or fabricated random seed / IoU numerical settings exist.
    """
    dir_item = ResearchDirection(
        direction_id="dir_test_status",
        title="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
        research_problem="Evaluation of XAI with YOLO detectors.",
        motivation="Diagnostic transparency for plant disease localization.",
        existing_evidence=["Literature evidence."],
        missing_aspect="XAI and YOLO integration.",
        proposed_direction="XAI + YOLO",
        supporting_papers=[
            SupportingPaper(paper_id=14, title="Paper 14", role="YOLO baseline"),
            SupportingPaper(paper_id=16, title="Paper 16", role="XAI methodology")
        ],
        supporting_concepts=[],
        candidate_algorithms=[],
        candidate_datasets=[],
        candidate_methodologies=[],
        evidence=ResearchDirectionEvidence(
            gap_score=0.85,
            semantic_evidence=0.05,
            link_prediction_score=0.8,
            collection_coverage=66.7,
            underrepresentation_score=0.3,
            evidence_classification="QUALIFIED_POTENTIAL_GAP"
        ),
        direction_score=0.85,
        confidence="High",
        disclaimer="Test disclaimer"
    )

    draft = ProposalDraftService._template_synthesis(dir_item=dir_item)

    # Check Methodology structure (4 sections: RECORDED, PROPOSED, EXPECTED, MISSING)
    meth = draft.proposed_methodology
    assert "A. RECORDED EVIDENCE:" in meth
    assert "B. PROPOSED METHODOLOGY:" in meth
    assert "C. PROPOSED EXPERIMENTAL ANALYSIS:" in meth
    assert "D. MISSING RESULTS:" in meth

    # Check Experimental Plan
    exp_plan = draft.experimental_plan
    assert "[PROPOSED]" in exp_plan
    assert "[MISSING]" in exp_plan
    assert "[RECORDED_EVIDENCE]" in exp_plan or "[RECORDED]" in exp_plan
    # Verify no fabricated seed numbers (e.g. seed = 42)
    assert "fixed seed = 42" not in exp_plan.lower()
    assert "iou threshold = 0.5" not in exp_plan.lower()

    # Check Metrics
    metrics = draft.evaluation_metrics
    assert "[PROPOSED]" in metrics
    assert "[MISSING]" in metrics

    # Check No Global Novelty claims
    full_text = f"{draft.abstract} {draft.problem_statement} {draft.expected_contribution} {draft.limitations}".lower()
    for forbidden_word in ["first", "unprecedented", "state-of-the-art", "guaranteed improvement"]:
        assert forbidden_word not in full_text, f"Forbidden global novelty word '{forbidden_word}' found in proposal text!"


def test_gap_opportunity_proposal_linkage_and_versioning(db_session: Session):
    """
    Test 5, 6, 7: Verify gap -> opportunity -> proposal linkage and non-ballooning versioning behavior.
    """
    # Create project in DB
    project = ResearchProject(name="Plant Disease Detection and Classification Using AI", description="Test Project")
    db_session.add(project)
    db_session.commit()

    # Synthesize initial proposal (Version 1)
    res1 = ProposalDraftService.synthesize_draft(
        db=db_session,
        direction_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        project_id=project.id,
        opportunity_family_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        payload_title="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
        regenerate=False
    )
    assert res1.version_number == 1
    assert res1.direction_id == "FAMILY_EXPLAINABILITY___FAMILY_YOLO"

    # Viewing / synthesising again without regenerate=True MUST return Version 1 without creating V2
    res2 = ProposalDraftService.synthesize_draft(
        db=db_session,
        direction_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        project_id=project.id,
        opportunity_family_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        payload_title="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
        regenerate=False
    )
    assert res2.version_number == 1, "Viewing/fetching proposal must NOT increment version_number!"

    # Explicit regeneration creates Version 2
    res3 = ProposalDraftService.synthesize_draft(
        db=db_session,
        direction_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        project_id=project.id,
        opportunity_family_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        payload_title="Application of Explainable Artificial Intelligence into YOLO-Family Object Detection",
        regenerate=True
    )
    assert res3.version_number == 2, "Explicit regenerate=True must increment version_number to 2."


def test_paper_role_attribution_and_hypothesis_wording(db_session: Session):
    """
    Test 1, 2, 3, 4, 7 & 10 of Final QA:
    - Paper 16 is NEVER classified as a YOLO or object-detection baseline.
    - Paper 14 is correctly classified as YOLO-family object detection evidence.
    - Paper 16 is correctly classified as XAI evidence.
    - Integrated XAI + YOLO architecture is PROPOSED.
    - Expected contribution uses hypothesis/planned-study wording (no observed results claimed).
    """
    dir_item = ResearchDirection(
        direction_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        opportunity_family_id="FAMILY_EXPLAINABILITY___FAMILY_YOLO",
        title="Integrating Explainable AI into YOLO-Family Object Detection for Plant Disease Analysis",
        research_problem="Integration of XAI into YOLO object detection.",
        motivation="Spatial attribution for plant disease localization.",
        existing_evidence=["Literature evidence."],
        missing_aspect="XAI + YOLO object detection integration.",
        proposed_direction="Integrating Explainable AI into YOLO-Family Object Detection",
        supporting_papers=[
            SupportingPaper(paper_id=14, title="Evaluating Performance YOLO Object Detectors", role="YOLO object detection"),
            SupportingPaper(paper_id=16, title="Improving Plant Disease Classification With XAI", role="Explainable AI methodology")
        ],
        supporting_concepts=[],
        candidate_algorithms=[],
        candidate_datasets=[],
        candidate_methodologies=[],
        evidence=ResearchDirectionEvidence(
            gap_score=0.88,
            semantic_evidence=0.1,
            link_prediction_score=0.8,
            collection_coverage=66.7,
            underrepresentation_score=0.4,
            evidence_classification="QUALIFIED_POTENTIAL_GAP"
        ),
        direction_score=0.88,
        confidence="High",
        disclaimer="Test disclaimer"
    )

    draft = ProposalDraftService._template_synthesis(dir_item=dir_item)

    # 1. Paper 16 must NOT be labeled as an object detection baseline
    exp_plan = draft.experimental_plan
    baseline_line = exp_plan.split("Baseline Architecture:")[1].split("\n")[0]
    assert "Paper ID 16" not in baseline_line, "Paper 16 must NEVER be classified as a YOLO/object detection baseline!"

    # 2. Paper 14 is classified as primary model baseline
    assert "Paper ID 14" in baseline_line, "Paper 14 must be classified as primary baseline evidence."

    # 3. Paper 16 is classified as secondary supporting methodology
    assert "Paper ID 16" in exp_plan.split("Supporting Methodology:")[1], "Paper 16 must be classified as supporting evidence."

    # 4. Integrated architecture is PROPOSED
    assert "Proposed Integration: Integrated pipeline for 'Integrating Explainable AI into YOLO-Family Object Detection for Plant Disease Analysis' [PROPOSED]" in exp_plan

    # 5. Expected Contribution uses hypothesis / planned-study wording
    contrib = draft.expected_contribution
    assert "will evaluate whether" in contrib.lower(), "Expected contribution must use hypothesis wording 'will evaluate whether'."
    assert "[PROPOSED]" in contrib
    assert "[MISSING]" in contrib
    assert "improves accuracy" not in contrib.lower()
    assert "provides enhanced" not in contrib.lower()

