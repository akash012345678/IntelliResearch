import pytest
from app.services.metadata_extractor import (
    MetadataExtractor,
    AlgorithmExtractor,
    MethodologyExtractor,
    KeywordExtractor,
    MetricExtractor,
    DatasetExtractor,
    ApplicationDomainExtractor,
)
from app.services.research_gap_service import ResearchGapService, GENERIC_CONCEPT_NAMES

def test_category_separation_rules():
    sample_text = (
        "We evaluate YOLOv9, YOLOv5, and CNN models using Deep Learning and Transfer Learning. "
        "Experiments conducted on PlantDoc dataset in Agriculture. F1 score and mAP@0.5 reported in IEEE Access."
    )
    meta = MetadataExtractor.extract_rich_metadata(
        title="Evaluating YOLOv9 for Plant Disease Detection",
        abstract="Deep Learning approach for plant disease classification.",
        full_text=sample_text
    )
    keywords = meta["keywords"]
    algorithms = meta["algorithms"]
    methodologies = meta["methodologies"]
    datasets = meta["datasets"]
    domains = meta["application_domains"]
    metrics = meta["metrics"]

    # 1. Algorithms MUST NOT leak into Keywords
    assert "YOLOv9" in algorithms
    assert "YOLOv5" in algorithms
    assert "CNN" in algorithms
    assert "YOLOv9" not in keywords
    assert "YOLOv5" not in keywords
    assert "CNN" not in keywords

    # 2. Methodologies MUST NOT leak into Keywords
    assert "Deep Learning" in methodologies
    assert "Transfer Learning" in methodologies
    assert "Deep Learning" not in keywords
    assert "Transfer Learning" not in keywords

    # 3. Datasets MUST NOT leak into Keywords
    assert "PlantDoc" in datasets
    assert "PlantDoc" not in keywords

    # 4. Domains MUST NOT leak into Keywords
    assert "Agriculture" in domains
    assert "Agriculture" not in keywords

    # 5. Metrics MUST NOT leak into Keywords
    assert "F1" in metrics or "F1-Score" in metrics
    assert "mAP@0.5" in metrics or "mAP" in metrics
    assert "F1" not in keywords
    assert "mAP" not in keywords
    assert "mAP@0.5" not in keywords

    # 6. Metadata MUST NOT leak into Keywords
    assert "IEEE" not in keywords
    assert "IEEE Access" not in keywords

def test_alias_normalization_rules():
    extractor = MethodologyExtractor()
    sample_text = "Our model uses Explainable AI, XAI, and Explainable Artificial Intelligence."
    methodologies = extractor.extract_with_roles(sample_text)
    meth_names = [m["name"] for m in methodologies]

    # Explainable AI & XAI canonicalized to single entity
    assert "Explainable Artificial Intelligence" in meth_names
    assert "Explainable AI" not in meth_names
    assert "XAI" not in meth_names

def test_sentence_fragment_rejection():
    sample_text = (
        "Prior To Final analysis. Disease Detection Tasks. Number Of Tokens. Plant Diseases Across regions. "
        "Performance YOLO Object Detectors For Plant."
    )
    meta = MetadataExtractor.extract_rich_metadata(
        title="Evaluating Plant Disease Classification",
        abstract="Disease detection in agriculture.",
        full_text=sample_text
    )
    keywords = meta["keywords"]

    # Reject sentence fragments
    assert "Prior To Final" not in keywords
    assert "Disease Detection Tasks" not in keywords
    assert "Number Of Tokens" not in keywords
    assert "Plant Diseases Across" not in keywords
    assert "Performance YOLO Object" not in keywords
    assert "Detectors For Plant" not in keywords

def test_metric_filter_and_exclusion():
    sample_text = "Precision 0.94, Recall 0.92, F1 0.93, IoU 0.85, FPS 60, Latency 15ms."
    meta = MetadataExtractor.extract_rich_metadata(
        title="Performance Metrics Evaluation",
        abstract="Measuring model accuracy and latency.",
        full_text=sample_text
    )
    metrics = meta["metrics"]
    keywords = meta["keywords"]

    assert "Precision" in metrics
    assert "Recall" in metrics
    assert "F1" in metrics
    assert "IoU" in metrics
    assert "FPS" in metrics

    # None of these metrics can be keywords
    for m in ["Precision", "Recall", "F1", "IoU", "FPS", "Latency"]:
        assert m not in keywords

def test_gap_validation_generic_exclusion():
    gap_service = ResearchGapService()
    
    # Generic stopwords, metrics, publisher noise, and fragments MUST return True (is generic)
    assert gap_service._is_generic_concept("IEEE")
    assert gap_service._is_generic_concept("F1")
    assert gap_service._is_generic_concept("mAP 50")
    assert gap_service._is_generic_concept("Prior To Final")
    assert gap_service._is_generic_concept("Creative Commons")
    assert gap_service._is_generic_concept("Accuracy")

    # Real technical concepts MUST return False (not generic)
    assert not gap_service._is_generic_concept("Swin-Axial Transformer")
    assert not gap_service._is_generic_concept("PlantDoc")

def test_task_extraction_and_classification():
    sample_text = (
        "We propose YOLOv9 for Plant Disease Classification and Object Detection tasks in Agriculture."
    )
    meta = MetadataExtractor.extract_rich_metadata(
        title="Evaluating YOLOv9 for Plant Disease Classification",
        abstract="Novel approach for crop disease detection.",
        full_text=sample_text
    )
    tasks = meta["tasks"]
    task_roles = meta["task_roles"]

    assert "Plant Disease Classification" in tasks
    primary_tasks = [t["name"] for t in task_roles if t["role"] == "PRIMARY_TASK"]
    assert "Plant Disease Classification" in primary_tasks


def test_user_reported_noisy_phrase_rejection():
    noisy_phrases = [
        "Addressed The Significant",
        "Validating The Decisions",
        "Established Best Practices",
        "Proposes An Explainable",
        "Actual Bounding Boxes",
        "Training Process",
        "Local Detail Information",
        "Lowering Computational Costs",
        "Box Approaches Raises",
        "Revolutionizing Disease",
        "Fully Edited",
        "Led To Substantial",
        "Across Different Thresholds",
        "Laboratory Of Electrical",
        "Security And Minimizing",
        "Ensuring Food Security"
    ]
    for p in noisy_phrases:
        assert MetadataExtractor.is_valid_research_concept(p) is False, f"Failed: '{p}' was expected to be rejected as noise"


def test_multi_domain_project_isolation():
    # Test 3 different domain project contexts
    # Project 1: Cybersecurity Threat Detection
    cyber_meta = MetadataExtractor.extract_rich_metadata(
        title="Cybersecurity Threat Detection Using Swin Transformer",
        abstract="Quantum Key Distribution and Fraud Detection in Network Security.",
        full_text="Evaluation of Quantum Cryptography and Random Forest."
    )
    assert "Cybersecurity Threat Detection" in cyber_meta["tasks"]
    assert "Agriculture" not in cyber_meta["application_domains"]

    # Project 2: Driver Drowsiness Detection
    driver_meta = MetadataExtractor.extract_rich_metadata(
        title="Driver Drowsiness Detection with Real-Time System",
        abstract="Computer Vision framework for Driver Assistance System.",
        full_text="CNN model evaluating FPS and Latency."
    )
    assert "Driver Drowsiness Detection" in driver_meta["tasks"]
    assert "PlantDoc" not in driver_meta["datasets"]

    # Project 3: Medical Image Classification
    med_meta = MetadataExtractor.extract_rich_metadata(
        title="Medical Image Classification using Vision Transformer",
        abstract="Deep Learning analysis of medical imaging data.",
        full_text="Evaluated on Accuracy and ROC-AUC."
    )
    assert "Medical Image Classification" in med_meta["tasks"]
    assert "Agriculture" not in med_meta["application_domains"]


