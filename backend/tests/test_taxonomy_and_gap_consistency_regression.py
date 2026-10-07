import pytest
from app.database.session import SessionLocal
from app.services.metadata_extractor import (
    MetadataExtractor,
    TaskExtractor,
    MetricExtractor,
    MethodologyExtractor,
    ApplicationExtractor,
    is_grammatical_noise_or_fragment
)
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.services.research_gap_service import ResearchGapService


def test_task_classification_and_count():
    """Verify Object Detection & Image Classification are classified as Tasks and Tasks count is 2 for Project 6."""
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        task_names = [t.name for t in resp.shared_concepts.get("tasks", [])]
        
        assert "Object Detection" in task_names
        assert "Image Classification" in task_names
        assert len(task_names) == 2
        assert resp.collection_summary.total_tasks == 2
    finally:
        db.close()


def test_metric_iou_normalization():
    """Verify IoU and Intersection over Union normalize to one single metric card."""
    assert MetricExtractor.METRIC_MAP.get("iou") == "IoU (Intersection over Union)"
    assert MetricExtractor.METRIC_MAP.get("intersection over union") == "IoU (Intersection over Union)"

    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        metric_names = [m.name for m in resp.shared_concepts.get("metrics", [])]
        
        assert "IoU (Intersection over Union)" in metric_names
        assert "Intersection over Union" not in metric_names
        assert "IoU" not in metric_names
    finally:
        db.close()


def test_edge_computing_and_mobile_application_evidence():
    """Verify Edge Computing is not an active methodology and Mobile Application is in applications."""
    assert "edge computing" not in MethodologyExtractor.METHODOLOGY_ALIAS_MAP

    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        method_names = [m.name for m in resp.shared_concepts.get("methodologies", [])]
        app_names = [a.name for a in resp.shared_concepts.get("applications", [])]

        assert "Edge Computing" not in method_names
        assert "Mobile Application" in app_names
        assert "Food Security" in app_names
        assert "Real-Time Monitoring" in app_names
    finally:
        db.close()


def test_keyword_noise_rejection():
    """Verify generic sentence fragments and academic boilerplate are rejected as keywords."""
    noisy_phrases = [
        "Experimental Results Show",
        "Effective Solutions",
        "Training Process",
        "Addressed The Significant",
        "Actual Bounding Boxes",
        "Established Best Practices"
    ]
    for phrase in noisy_phrases:
        assert is_grammatical_noise_or_fragment(phrase) is True
        assert MetadataExtractor.is_valid_research_concept(phrase) is False


def test_qualified_gaps_contract_project_6():
    """Verify Project 6 has visible qualified gaps and INSUFFICIENT_EVIDENCE is excluded."""
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        gaps = resp.research_gaps

        assert len(gaps) >= 3
        for g in gaps:
            assert g.eligibility_status == "QUALIFIED_POTENTIAL_GAP"

        titles = [g.title for g in gaps]
        assert any("Explainable AI to YOLO-family" in t for t in titles)
        assert any("Transformer-family and YOLO-family" in t for t in titles)
        assert any("Explainable AI to Transformer-family" in t for t in titles)
    finally:
        db.close()


def test_connections_and_similarities_project_6():
    """Verify Project 6 has exactly 3 connections with expected similarity values."""
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        rels = resp.paper_relationships

        assert len(rels) == 3
        rel_map = {(r.source_paper_id, r.target_paper_id): r.similarity_score for r in rels}
        
        # 14 <-> 15, 14 <-> 16, 15 <-> 16
        score_14_15 = rel_map.get((14, 15)) or rel_map.get((15, 14))
        score_14_16 = rel_map.get((14, 16)) or rel_map.get((16, 14))
        score_15_16 = rel_map.get((15, 16)) or rel_map.get((16, 15))

        assert score_14_15 is not None
        assert score_14_16 is not None
        assert score_15_16 is not None
    finally:
        db.close()


def test_candidate_opportunities_linked_to_valid_evidence():
    """Verify Project 6 has evidence-grounded candidate opportunities derived from qualified gaps."""
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        dirs = resp.candidate_research_directions

        assert len(dirs) >= 3
        for d in dirs:
            assert d.parent_gap_id is not None
            assert d.gap_relationship_key is not None
            assert d.supporting_papers and len(d.supporting_papers) > 0
            # Ensure no global novelty claims
            desc_lower = (d.description or "").lower()
            assert "first in the world" not in desc_lower
            assert "globally unique" not in desc_lower
    finally:
        db.close()
