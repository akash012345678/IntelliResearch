import pytest
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.services.research_methodology_service import ResearchMethodologyService

client = TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_xai_yolo_opportunity_generates_xai_yolo_plan(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    assert plan.direction_id == direction_id
    plan_str = str(plan.model_dump()).lower()
    
    assert "yolo" in plan_str
    assert ("explainab" in plan_str or "attribution" in plan_str or "xai" in plan_str)


def test_transformer_yolo_opportunity_generates_comparative_plan(db_session: Session):
    direction_id = "FAMILY_TRANSFORMER___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    assert plan.direction_id == direction_id
    plan_str = str(plan.model_dump()).lower()

    assert "transformer" in plan_str
    assert "yolo" in plan_str
    assert "compar" in plan_str or "evaluat" in plan_str


def test_transformer_xai_opportunity_generates_transformer_xai_plan(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_TRANSFORMER"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    assert plan.direction_id == direction_id
    plan_str = str(plan.model_dump()).lower()

    assert "transformer" in plan_str
    assert ("explainab" in plan_str or "attribution" in plan_str or "xai" in plan_str)


def test_no_temporal_content_for_non_temporal_opportunity(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    plan_str = str(plan.model_dump()).lower()
    assert "temporal" not in plan_str


def test_no_sequence_window_for_non_temporal_opportunity(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    plan_str = str(plan.model_dump()).lower()
    assert "sequence window" not in plan_str
    assert "sequence modeling" not in plan_str


def test_no_target_component_placeholder_when_real_component_exists(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    plan_str = str(plan.model_dump()).lower()
    assert "target component" not in plan_str


def test_dataset_provenance_matches_selected_opportunity(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    assert len(plan.dataset_plan) > 0
    for ds in plan.dataset_plan:
        assert ds.name != ""
        assert ds.name != "Standard Benchmark Dataset"
        assert ds.suitability != ""


def test_metrics_match_task(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    all_metrics = [m for cat in plan.metrics for m in cat.metrics]
    metric_str = " ".join(all_metrics).lower()

    # Object detection metrics
    assert "map" in metric_str or "iou" in metric_str or "precision" in metric_str or "f1" in metric_str


def test_ablation_matches_proposed_components(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    ablation_str = str([a.model_dump() for a in plan.ablation_plan]).lower()
    print("DEBUG ABLATION STR:", ablation_str)
    assert "no temporal layer" not in ablation_str
    assert ("explainability" in ablation_str or "attribution" in ablation_str or "detector" in ablation_str or "xai" in ablation_str or "standalone" in ablation_str or "module" in ablation_str or "layer" in ablation_str)


def test_plan_uses_selected_opportunity_id(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)
    assert plan.direction_id == direction_id


def test_plan_has_no_project6_hardcoding(db_session: Session):
    # Create a test project for Cybersecurity Intrusion Detection
    project = ResearchProject(name="Cybersecurity Intrusion Detection AI", description="Network anomaly detection using GNN", status="ACTIVE")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    paper = ResearchPaper(
        title="Graph Neural Networks for Cybersecurity Intrusion Detection on NSL-KDD",
        abstract="We present a Graph Neural Network approach for Network Intrusion Detection on the NSL-KDD dataset.",
        full_text="Graph Neural Networks for Cybersecurity Intrusion Detection on NSL-KDD",
        filename="cyber_gnn.pdf",
        algorithms=["Graph Neural Network"],
        datasets=["NSL-KDD"]
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)

    project_paper = ProjectPaper(project_id=project.id, paper_id=paper.id)
    db_session.add(project_paper)
    db_session.commit()

    direction_id = "CYBER_GNN_INTRUSION_01"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=project.id)

    plan_str = str(plan.model_dump()).lower()

    # Must NOT mention Plant Disease or YOLO
    assert "plant disease" not in plan_str
    assert "yolo" not in plan_str
    assert plan.direction_id == direction_id


def test_xai_yolo_hypotheses_correction(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    h0 = plan.hypotheses.null_hypothesis
    h1 = plan.hypotheses.alternative_hypothesis

    assert "interpretability or attribution stability" in h0
    assert "interpretability and attribution stability" in h1
    assert "comparable detection performance" in h0 or "comparable" in h0
    assert "comparable detection performance" in h1 or "comparable" in h1


def test_explicit_datasets_plantdoc_plantvillage(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    plan_str = str(plan.model_dump()).lower()
    assert "standard benchmark dataset" not in plan_str
    assert ("plantdoc" in plan_str or "plantvillage" in plan_str)


def test_train_val_test_split_and_data_leakage_note(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    prep_str = " ".join(plan.data_preparation)
    assert "70/15/15" in prep_str
    assert "proposed" in prep_str.lower()
    assert "prevent data leakage" in prep_str.lower() or "data leakage" in prep_str.lower()


def test_detection_plan_validates_dataset_task_suitability(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    assert len(plan.dataset_plan) >= 2
    ds_map = {ds.name.lower(): ds for ds in plan.dataset_plan}
    
    assert "plantdoc" in ds_map
    assert ds_map["plantdoc"].suitability_class == "DIRECTLY_SUITABLE"
    assert "object detection" in ds_map["plantdoc"].suitability.lower()

    assert "plantvillage" in ds_map
    assert ds_map["plantvillage"].suitability_class == "REQUIRES_VERIFICATION"
    assert "verification" in ds_map["plantvillage"].suitability.lower() or "adaptation" in ds_map["plantvillage"].suitability.lower()


def test_classification_dataset_not_marked_detection_ready(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    pv_item = next((ds for ds in plan.dataset_plan if "plantvillage" in ds.name.lower()), None)
    assert pv_item is not None
    assert pv_item.suitability_class != "DIRECTLY_SUITABLE"
    assert "ready for yolo training" not in pv_item.suitability.lower()
    assert "ready for yolo training" not in pv_item.limitations.lower()


def test_unsupported_bbox_claim_rejected(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    pv_item = next((ds for ds in plan.dataset_plan if "plantvillage" in ds.name.lower()), None)
    assert pv_item is not None
    assert "bounding-box annotations are already available" not in pv_item.suitability.lower()
    assert "not established" in pv_item.limitations.lower() or "requires verification" in pv_item.suitability.lower()


def test_proposed_split_marked_proposed(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    prep_str = " ".join(plan.data_preparation)
    assert "70/15/15" in prep_str
    assert "proposed train/validation/test split: 70/15/15" in prep_str.lower() or "[proposed]" in prep_str.lower()


def test_recorded_split_only_when_source_supports_it(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    split_params = [p for p in plan.experiment_parameters if p.category == "SPLIT"]
    assert len(split_params) > 0
    for p in split_params:
        assert p.provenance_status == "PROPOSED"


def test_experiment_parameters_not_marked_recorded_without_evidence(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    param_map = {p.parameter: p for p in plan.experiment_parameters}
    
    assert "Train / Validation / Test Split" in param_map
    assert param_map["Train / Validation / Test Split"].provenance_status == "PROPOSED"

    assert "Random Seed Configuration" in param_map
    assert param_map["Random Seed Configuration"].provenance_status == "PROPOSED"

    assert "Hyperparameter Settings (Learning rate, Batch size, Augmentation)" in param_map
    assert param_map["Hyperparameter Settings (Learning rate, Batch size, Augmentation)"].provenance_status == "PROPOSED"

    assert "Baseline Model Architecture" in param_map
    assert param_map["Baseline Model Architecture"].provenance_status == "RECORDED_EVIDENCE"

    assert "Empirical Experimental Results" in param_map
    assert param_map["Empirical Experimental Results"].provenance_status == "MISSING"


def test_ablation_matches_actual_components(db_session: Session):
    direction_id = "FAMILY_EXPLAINABILITY___FAMILY_YOLO"
    plan = ResearchMethodologyService.get_methodology_plan(db_session, direction_id=direction_id, project_id=6)

    proposed_comps = [c.lower() for c in plan.proposed_method.get("components", [])]
    for abl in plan.ablation_plan:
        rem = abl.component_removed.lower()
        if rem != "none (complete pipeline)" and "none" not in rem:
            matched = any(c in rem or rem in c for c in proposed_comps) or "augmentation" in rem
            assert matched, f"Ablation component '{rem}' not found in proposed components '{proposed_comps}'"


