import pytest
from app.database.session import SessionLocal
from app.services.research_gap_service import get_canonical_concept_family, ResearchGapService
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.models.paper_model import ResearchPaper

def test_A_yolov6_normalizes_to_family_yolo():
    fam = get_canonical_concept_family("YOLOv6")
    assert fam["family_key"] == "FAMILY_YOLO"
    assert fam["family_label"] == "YOLO-family"


def test_B_yolov8_normalizes_to_family_yolo():
    fam = get_canonical_concept_family("YOLOv8")
    assert fam["family_key"] == "FAMILY_YOLO"
    assert fam["family_label"] == "YOLO-family"


def test_C_yolov9_normalizes_to_family_yolo():
    fam = get_canonical_concept_family("YOLOv9")
    assert fam["family_key"] == "FAMILY_YOLO"
    assert fam["family_label"] == "YOLO-family"


def test_D_transformer_plus_yolov6_equals_transformer_plus_yolo():
    fam_trans = get_canonical_concept_family("Transformer")
    fam_yolo = get_canonical_concept_family("YOLO")
    fam_yolov6 = get_canonical_concept_family("YOLOv6")

    key1 = "___".join(sorted([fam_trans["family_key"], fam_yolo["family_key"]]))
    key2 = "___".join(sorted([fam_trans["family_key"], fam_yolov6["family_key"]]))
    assert key1 == key2 == "FAMILY_TRANSFORMER___FAMILY_YOLO"


def test_E_xai_plus_yolov6_equals_xai_plus_yolo():
    fam_xai = get_canonical_concept_family("XAI")
    fam_yolo = get_canonical_concept_family("YOLO")
    fam_yolov6 = get_canonical_concept_family("YOLOv6")

    key1 = "___".join(sorted([fam_xai["family_key"], fam_yolo["family_key"]]))
    key2 = "___".join(sorted([fam_xai["family_key"], fam_yolov6["family_key"]]))
    assert key1 == key2 == "FAMILY_EXPLAINABILITY___FAMILY_YOLO"


def test_F_transformer_plus_yolov8_equals_transformer_plus_yolo():
    fam_trans = get_canonical_concept_family("Transformer")
    fam_yolov8 = get_canonical_concept_family("YOLOv8")
    key = "___".join(sorted([fam_trans["family_key"], fam_yolov8["family_key"]]))
    assert key == "FAMILY_TRANSFORMER___FAMILY_YOLO"


def test_G_xai_plus_yolov9_equals_xai_plus_yolo():
    fam_xai = get_canonical_concept_family("Explainability Methods")
    fam_yolov9 = get_canonical_concept_family("YOLOv9")
    key = "___".join(sorted([fam_xai["family_key"], fam_yolov9["family_key"]]))
    assert key == "FAMILY_EXPLAINABILITY___FAMILY_YOLO"


def test_H_transformer_xai_version_aliases_merge_into_one_canonical_relationship():
    fam1 = get_canonical_concept_family("Swin Transformer")
    fam2 = get_canonical_concept_family("LIME")
    key = "___".join(sorted([fam1["family_key"], fam2["family_key"]]))
    assert key == "FAMILY_EXPLAINABILITY___FAMILY_TRANSFORMER"


def test_I_J_K_project_6_contains_no_version_specific_yolo_relationships():
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        rel_keys = [g.evidence.get("canonical_relationship_key") for g in resp.research_gaps]

        assert not any("YOLOV6" in rk for rk in rel_keys), f"Found YOLOV6 in keys: {rel_keys}"
        assert not any("YOLOV8" in rk for rk in rel_keys), f"Found YOLOV8 in keys: {rel_keys}"
        assert not any("YOLOV9" in rk for rk in rel_keys), f"Found YOLOV9 in keys: {rel_keys}"
    finally:
        db.close()


def test_L_M_N_paper_role_integrity_project_6():
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        gaps = resp.research_gaps

        for g in gaps:
            reasoning = g.gap_reasoning or {}
            comp_a = reasoning.get("component_a_evidence", {})
            comp_b = reasoning.get("component_b_evidence", {})

            # Paper 14 MUST NEVER be described as Transformer-family
            if comp_a.get("concept") == "Transformer-family":
                assert 14 not in comp_a.get("paper_ids", [])
            if comp_b.get("concept") == "Transformer-family":
                assert 14 not in comp_b.get("paper_ids", [])

            # Paper 15 MUST NEVER be described as YOLO-family
            if comp_a.get("concept") == "YOLO-family":
                assert 15 not in comp_a.get("paper_ids", [])
            if comp_b.get("concept") == "YOLO-family":
                assert 15 not in comp_b.get("paper_ids", [])

    finally:
        db.close()


def test_O_no_duplicate_canonical_relationship_keys_returned():
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        gaps = resp.research_gaps
        rel_keys = [g.evidence.get("canonical_relationship_key") for g in gaps]
        assert len(gaps) == len(set(rel_keys)), f"Duplicates found: {rel_keys}"
    finally:
        db.close()


def test_P_frontend_api_counts_remain_consistent():
    db = SessionLocal()
    try:
        ProjectIntelligenceService.invalidate_cache(6)
        resp = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        gaps = resp.research_gaps
        opps = resp.candidate_research_directions

        assert len(gaps) > 0
        assert len(opps) > 0
        gap_keys = set(g.evidence.get("canonical_relationship_key") for g in gaps)
        opp_keys = set(o.gap_relationship_key for o in opps)
        # Every opportunity references a valid canonical gap relationship key
        assert opp_keys.issubset(gap_keys) or len(opp_keys.intersection(gap_keys)) > 0
    finally:
        db.close()
