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
from app.services.project_intelligence_service import ProjectIntelligenceService


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_multidomain_generalization_and_cross_contamination(db: Session):
    """
    SECTION 19, 20 & 21: Multi-Domain Generalization & Cross-Project Contamination Test.
    Evaluates:
    - Project A: Computer Vision (YOLOv8 + PlantDoc)
    - Project B: NLP (BERT + IMDB)
    - Project C: Cybersecurity (Random Forest + CIC-IDS2017)
    Proves 100% project isolation and zero cross-domain leakage.
    """
    # -------------------------------------------------------------
    # 1. SETUP PROJECT A (CV / Plant Pathology)
    # -------------------------------------------------------------
    proj_a = ResearchProject(name="Project A - Plant Disease CV", description="Computer Vision domain test")
    db.add(proj_a)
    db.commit()

    paper_a1 = ResearchPaper(
        title="Evaluating YOLOv8 for Object Detection",
        abstract="Abstract A1",
        full_text="Full text A1",
        filename="paper_a1.pdf",
        datasets=["PlantDoc"],
        algorithms=["YOLOv8"],
        methodologies=["Object Detection"],
        application_domains=["Plant Pathology"]
    )
    paper_a2 = ResearchPaper(
        title="XAI Feature Attribution for Disease Classification",
        abstract="Abstract A2",
        full_text="Full text A2",
        filename="paper_a2.pdf",
        datasets=["PlantVillage"],
        algorithms=["Explainable AI"],
        methodologies=["Saliency Maps"],
        application_domains=["Plant Pathology"]
    )
    db.add_all([paper_a1, paper_a2])
    db.commit()

    db.add_all([
        ProjectPaper(project_id=proj_a.id, paper_id=paper_a1.id),
        ProjectPaper(project_id=proj_a.id, paper_id=paper_a2.id)
    ])
    db.commit()

    # -------------------------------------------------------------
    # 2. SETUP PROJECT B (NLP / Sentiment Analysis)
    # -------------------------------------------------------------
    proj_b = ResearchProject(name="Project B - NLP Sentiment Analysis", description="NLP domain test")
    db.add(proj_b)
    db.commit()

    paper_b1 = ResearchPaper(
        title="BERT Models for Fine-Grained Sentiment Analysis",
        abstract="Abstract B1",
        full_text="Full text B1",
        filename="paper_b1.pdf",
        datasets=["IMDB Reviews Dataset"],
        algorithms=["BERT"],
        methodologies=["Transformer Encoder"],
        application_domains=["Natural Language Processing"]
    )
    paper_b2 = ResearchPaper(
        title="RoBERTa Optimization for Text Classification",
        abstract="Abstract B2",
        full_text="Full text B2",
        filename="paper_b2.pdf",
        datasets=["Twitter Sentiment Benchmark"],
        algorithms=["RoBERTa"],
        methodologies=["Sequence Classification"],
        application_domains=["Natural Language Processing"]
    )
    db.add_all([paper_b1, paper_b2])
    db.commit()

    db.add_all([
        ProjectPaper(project_id=proj_b.id, paper_id=paper_b1.id),
        ProjectPaper(project_id=proj_b.id, paper_id=paper_b2.id)
    ])
    db.commit()

    # -------------------------------------------------------------
    # 3. SETUP PROJECT C (Cybersecurity / Intrusion Detection)
    # -------------------------------------------------------------
    proj_c = ResearchProject(name="Project C - Cybersecurity Intrusion Detection", description="Cybersecurity domain test")
    db.add(proj_c)
    db.commit()

    paper_c1 = ResearchPaper(
        title="Random Forest Ensembles for Network Traffic Anomaly Detection",
        abstract="Abstract C1",
        full_text="Full text C1",
        filename="paper_c1.pdf",
        datasets=["CIC-IDS2017 Dataset"],
        algorithms=["Random Forest"],
        methodologies=["Anomaly Detection"],
        application_domains=["Cybersecurity"]
    )
    paper_c2 = ResearchPaper(
        title="XGBoost Gradient Boosting for Intrusion Prevention",
        abstract="Abstract C2",
        full_text="Full text C2",
        filename="paper_c2.pdf",
        datasets=["NSL-KDD Dataset"],
        algorithms=["XGBoost"],
        methodologies=["Feature Importance"],
        application_domains=["Cybersecurity"]
    )
    db.add_all([paper_c1, paper_c2])
    db.commit()

    db.add_all([
        ProjectPaper(project_id=proj_c.id, paper_id=paper_c1.id),
        ProjectPaper(project_id=proj_c.id, paper_id=paper_c2.id)
    ])
    db.commit()

    # -------------------------------------------------------------
    # 4. SYNTHESIZE PROPOSALS & TEST ISOLATION FOR PROJECT A
    # -------------------------------------------------------------
    dir_a = ResearchDirection(
        direction_id="dir_a_cv",
        title="Integrating Explainable AI into YOLOv8 Object Detection",
        research_problem="XAI integration with YOLO detectors.",
        motivation="Spatial attribution for plant pathology.",
        existing_evidence=["CV Literature."],
        missing_aspect="XAI + YOLOv8 synthesis.",
        proposed_direction="YOLOv8 + XAI",
        supporting_papers=[
            SupportingPaper(paper_id=paper_a1.id, title=paper_a1.title, role="YOLOv8 baseline detector"),
            SupportingPaper(paper_id=paper_a2.id, title=paper_a2.title, role="Explainable AI methodology")
        ],
        supporting_concepts=[],
        candidate_algorithms=[CandidateAlgorithm(name="YOLOv8", supporting_paper_count=1, reason="Detector")],
        candidate_datasets=[CandidateDataset(name="PlantDoc", supporting_paper_count=1, reason="Evidenced")],
        candidate_methodologies=[],
        evidence=ResearchDirectionEvidence(
            gap_score=0.85, semantic_evidence=0.05, link_prediction_score=0.8, collection_coverage=50.0, underrepresentation_score=0.3
        ),
        direction_score=0.85, confidence="High", disclaimer="Test disclaimer"
    )

    draft_a = ProposalDraftService._template_synthesis(dir_item=dir_a, project_papers=[paper_a1, paper_a2])
    assert draft_a.task_type == "OBJECT_DETECTION"
    assert "PlantDoc" in draft_a.candidate_datasets
    assert "PlantVillage" in draft_a.candidate_datasets
    # Isolation assertion: Project A MUST NOT contain NLP or Cybersecurity concepts
    full_text_a = f"{draft_a.abstract} {draft_a.proposed_methodology} {draft_a.experimental_plan}".lower()
    for forbidden in ["bert", "roberta", "imdb", "random forest", "xgboost", "cic-ids2017"]:
        assert forbidden not in full_text_a, f"Project A contaminated with foreign concept '{forbidden}'!"

    # -------------------------------------------------------------
    # 5. SYNTHESIZE PROPOSALS & TEST ISOLATION FOR PROJECT B (NLP)
    # -------------------------------------------------------------
    dir_b = ResearchDirection(
        direction_id="dir_b_nlp",
        title="Comparative Evaluation of BERT and RoBERTa for Sentiment Classification",
        research_problem="Comparative analysis of transformer encoders for sentiment analysis.",
        motivation="Evaluate sentiment classification accuracy and perplexity.",
        existing_evidence=["NLP Literature."],
        missing_aspect="Unified comparative benchmark of BERT and RoBERTa.",
        proposed_direction="BERT + RoBERTa Sentiment Analysis",
        supporting_papers=[
            SupportingPaper(paper_id=paper_b1.id, title=paper_b1.title, role="BERT encoder baseline"),
            SupportingPaper(paper_id=paper_b2.id, title=paper_b2.title, role="RoBERTa optimization")
        ],
        supporting_concepts=[],
        candidate_algorithms=[CandidateAlgorithm(name="BERT", supporting_paper_count=1, reason="Transformer")],
        candidate_datasets=[CandidateDataset(name="IMDB Reviews Dataset", supporting_paper_count=1, reason="Evidenced")],
        candidate_methodologies=[],
        evidence=ResearchDirectionEvidence(
            gap_score=0.82, semantic_evidence=0.05, link_prediction_score=0.8, collection_coverage=50.0, underrepresentation_score=0.3
        ),
        direction_score=0.82, confidence="High", disclaimer="Test disclaimer"
    )

    draft_b = ProposalDraftService._template_synthesis(dir_item=dir_b, project_papers=[paper_b1, paper_b2])
    assert draft_b.task_type == "NATURAL_LANGUAGE_PROCESSING"
    assert "IMDB Reviews Dataset" in draft_b.candidate_datasets
    assert "Twitter Sentiment Benchmark" in draft_b.candidate_datasets
    # Isolation assertion: Project B MUST NOT contain CV or Cybersecurity concepts
    full_text_b = f"{draft_b.abstract} {draft_b.proposed_methodology} {draft_b.experimental_plan}".lower()
    for forbidden in ["yolo", "plantdoc", "plantvillage", "random forest", "xgboost", "cic-ids2017"]:
        assert forbidden not in full_text_b, f"Project B contaminated with foreign concept '{forbidden}'!"

    # -------------------------------------------------------------
    # 6. SYNTHESIZE PROPOSALS & TEST ISOLATION FOR PROJECT C (Cybersecurity)
    # -------------------------------------------------------------
    dir_c = ResearchDirection(
        direction_id="dir_c_cyber",
        title="Hybrid Random Forest and XGBoost Architecture for Network Intrusion Detection",
        research_problem="Combining ensemble tree classifiers for network anomaly detection.",
        motivation="Reduce false positive rates in high-throughput network environments.",
        existing_evidence=["Cybersecurity Literature."],
        missing_aspect="Hybrid RF and XGBoost integration for packet filtering.",
        proposed_direction="Random Forest + XGBoost Intrusion Detection",
        supporting_papers=[
            SupportingPaper(paper_id=paper_c1.id, title=paper_c1.title, role="Random Forest baseline"),
            SupportingPaper(paper_id=paper_c2.id, title=paper_c2.title, role="XGBoost optimization")
        ],
        supporting_concepts=[],
        candidate_algorithms=[CandidateAlgorithm(name="Random Forest", supporting_paper_count=1, reason="Classifier")],
        candidate_datasets=[CandidateDataset(name="CIC-IDS2017 Dataset", supporting_paper_count=1, reason="Evidenced")],
        candidate_methodologies=[],
        evidence=ResearchDirectionEvidence(
            gap_score=0.90, semantic_evidence=0.05, link_prediction_score=0.8, collection_coverage=50.0, underrepresentation_score=0.3
        ),
        direction_score=0.90, confidence="High", disclaimer="Test disclaimer"
    )

    draft_c = ProposalDraftService._template_synthesis(dir_item=dir_c, project_papers=[paper_c1, paper_c2])
    assert draft_c.task_type == "CYBERSECURITY_INTRUSION_DETECTION"
    assert "CIC-IDS2017 Dataset" in draft_c.candidate_datasets
    assert "NSL-KDD Dataset" in draft_c.candidate_datasets
    # Isolation assertion: Project C MUST NOT contain CV or NLP concepts
    full_text_c = f"{draft_c.abstract} {draft_c.proposed_methodology} {draft_c.experimental_plan}".lower()
    for forbidden in ["yolo", "plantdoc", "plantvillage", "bert", "roberta", "imdb"]:
        assert forbidden not in full_text_c, f"Project C contaminated with foreign concept '{forbidden}'!"

    print("\n=== MULTI-DOMAIN ISOLATION & ZERO CROSS-CONTAMINATION TEST PASSED PERFECTLY ===")
