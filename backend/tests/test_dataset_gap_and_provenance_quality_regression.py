import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.research_gap_service import ResearchGapService, is_valid_dataset_gap, paper_supports_family, PROJECT_PAPER_ROLES
from app.models.paper_model import ResearchPaper


class TestDatasetGapAndProvenanceQualityRegression(unittest.TestCase):

    def setUp(self):
        self.p14 = ResearchPaper(
            id=14,
            title="Evaluating the Performance of YOLO Object Detectors for Plant Disease Detection",
            abstract="Evaluates YOLO, YOLOv8, YOLOv9 for object detection in agriculture using PlantDoc dataset.",
            algorithms=["YOLO", "YOLOv8", "YOLOv9"],
            datasets=["PlantDoc"],
            methodologies=["Object Detection"],
            application_domains=["Agriculture"]
        )
        self.p15 = ResearchPaper(
            id=15,
            title="Plant Disease Detection Using an Innovative Swin-Axial Transformer",
            abstract="Proposes Swin-Axial Transformer evaluated on PlantDoc and PlantVillage datasets.",
            algorithms=["Transformer", "Axial Transformer", "Swin-Axial Transformer"],
            datasets=["PlantDoc", "PlantVillage", "Fusion Dataset"],
            methodologies=["Feature Extraction"],
            application_domains=["Agriculture"]
        )
        self.p16 = ResearchPaper(
            id=16,
            title="Improving Plant Disease Classification With Deep-Learning-Based Prediction Model Using Explainable Artificial Intelligence",
            abstract="Investigates Explainable Artificial Intelligence and ResNet models using LIME.",
            algorithms=["CNN", "ResNet"],
            datasets=["PlantVillage"],
            methodologies=["Explainable Artificial Intelligence", "LIME"],
            application_domains=["Agriculture"]
        )
        self.project_papers = [self.p14, self.p15, self.p16]
        self.gap_service = ResearchGapService()

    # Test A: Different-paper model + dataset alone does NOT guarantee a gap.
    def test_A_different_paper_model_dataset_not_automatic_gap(self):
        is_valid, status, _ = is_valid_dataset_gap(
            model_family_key="FAMILY_YOLO",
            dataset_family_key="FAMILY_DS_PLANTVILLAGE",
            supporting_paper_ids=[14, 15],
            paper_map={14: self.p14, 15: self.p15},
            proj_context="Plant Disease Detection",
            fw_matches=[]
        )
        self.assertFalse(is_valid)
        self.assertEqual(status, "INSUFFICIENT_EVIDENCE")

    # Test B: CNN/ResNet + Multi-Source Dataset is rejected when task/evidence support is insufficient.
    def test_B_cnn_resnet_multisource_rejected(self):
        is_valid, status, _ = is_valid_dataset_gap(
            model_family_key="FAMILY_CNN_RESNET",
            dataset_family_key="FAMILY_DS_MULTISOURCE",
            supporting_paper_ids=[16, 15],
            paper_map={16: self.p16, 15: self.p15},
            proj_context="Plant Disease Detection",
            fw_matches=[]
        )
        self.assertFalse(is_valid)
        self.assertEqual(status, "INSUFFICIENT_EVIDENCE")

    # Test C: YOLO + PlantVillage and YOLO + Multi-Source Dataset are filtered out when lacking explicit future-work signals.
    def test_C_yolo_dataset_gaps_filtered(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        rel_keys = [g["evidence"]["canonical_relationship_key"] for g in gaps]
        self.assertNotIn("FAMILY_DS_PLANTVILLAGE___FAMILY_YOLO", rel_keys)
        self.assertNotIn("FAMILY_DS_MULTISOURCE___FAMILY_YOLO", rel_keys)
        self.assertNotIn("FAMILY_CNN_RESNET___FAMILY_DS_MULTISOURCE", rel_keys)

    # Test D: YOLO + Explainability remains valid when evidence supports it.
    def test_D_yolo_explainability_valid(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        rel_keys = [g["evidence"]["canonical_relationship_key"] for g in gaps]
        self.assertIn("FAMILY_EXPLAINABILITY___FAMILY_YOLO", rel_keys)

    # Test E: Transformer + Explainability remains valid.
    def test_E_transformer_explainability_valid(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        rel_keys = [g["evidence"]["canonical_relationship_key"] for g in gaps]
        self.assertIn("FAMILY_EXPLAINABILITY___FAMILY_TRANSFORMER", rel_keys)

    # Test F: Transformer + YOLO remains valid.
    def test_F_transformer_yolo_valid(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        rel_keys = [g["evidence"]["canonical_relationship_key"] for g in gaps]
        self.assertIn("FAMILY_TRANSFORMER___FAMILY_YOLO", rel_keys)

    # Test G: Same-paper co-occurrence still rejects a relationship.
    def test_G_same_paper_co_occurrence_rejected(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        rel_keys = [g["evidence"]["canonical_relationship_key"] for g in gaps]
        # Swin-Axial Transformer & Feature Extraction co-occur in Paper 15
        self.assertNotIn("FAMILY_TRANSFORMER___FAMILY_FEATURE_EXTRACTION", rel_keys)

    # Test H: Paper-role provenance remains correct.
    def test_H_paper_role_provenance_correct(self):
        self.assertTrue(paper_supports_family(self.p14, "FAMILY_YOLO"))
        self.assertFalse(paper_supports_family(self.p14, "FAMILY_TRANSFORMER"))
        self.assertFalse(paper_supports_family(self.p14, "FAMILY_EXPLAINABILITY"))

        self.assertTrue(paper_supports_family(self.p15, "FAMILY_TRANSFORMER"))
        self.assertFalse(paper_supports_family(self.p15, "FAMILY_YOLO"))
        self.assertFalse(paper_supports_family(self.p15, "FAMILY_EXPLAINABILITY"))

        self.assertTrue(paper_supports_family(self.p16, "FAMILY_EXPLAINABILITY"))
        self.assertTrue(paper_supports_family(self.p16, "FAMILY_CNN_RESNET"))
        self.assertFalse(paper_supports_family(self.p16, "FAMILY_YOLO"))
        self.assertFalse(paper_supports_family(self.p16, "FAMILY_TRANSFORMER"))

    # Test I: No global novelty language appears.
    def test_I_no_global_novelty_language(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        for g in gaps:
            text = f"{g['title']} {g['description']} {str(g['gap_reasoning'])}".lower()
            self.assertNotIn("this has never been studied", text)
            self.assertNotIn("this is novel globally", text)
            self.assertNotIn("no researcher has done this", text)
            self.assertNotIn("first-ever", text)
            self.assertNotIn("unprecedented", text)

    # Test J: Every visible gap contains valid gap_reasoning.
    def test_J_every_gap_contains_valid_reasoning(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        for g in gaps:
            reasoning = g["gap_reasoning"]
            self.assertIn("component_a", reasoning)
            self.assertIn("component_a_papers", reasoning)
            self.assertIn("component_b", reasoning)
            self.assertIn("component_b_papers", reasoning)
            self.assertIn("relationship_not_found", reasoning)
            self.assertIn("task_alignment", reasoning)
            self.assertIn("scientific_compatibility", reasoning)
            self.assertIn("evidence_limitation", reasoning)

    # Test K: Canonical relationship keys remain unique.
    def test_K_canonical_keys_unique(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        rel_keys = [g["evidence"]["canonical_relationship_key"] for g in gaps]
        self.assertEqual(len(rel_keys), len(set(rel_keys)))

    # Test L: No version-level Cartesian permutations reappear.
    def test_L_no_version_cartesian_permutations(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        for g in gaps:
            rel_key = g["evidence"]["canonical_relationship_key"]
            self.assertNotIn("YOLOV6", rel_key)
            self.assertNotIn("YOLOV8", rel_key)
            self.assertNotIn("YOLOV9", rel_key)

    # Test M: Support count equals unique supporting paper IDs & duplicate paper IDs do not increase count
    def test_M_support_count_equals_unique_paper_ids(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        for g in gaps:
            src_pids = [p["paper_id"] for p in g["source_papers"]]
            unique_pids = sorted(list(set(src_pids)))
            self.assertEqual(len(src_pids), len(unique_pids), "Duplicate paper IDs must not appear in source_papers.")
            self.assertEqual(g["supported_paper_count"], len(unique_pids), "supported_paper_count must equal unique supporting paper IDs.")
            self.assertEqual(g["evidence"]["supported_paper_count"], len(unique_pids))

    # Test N: Project 6 gaps each report exactly 2 supporting papers
    def test_N_project_6_gaps_report_2_supporting_papers(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection and Classification Using AI")
        self.assertGreaterEqual(len(gaps), 3, "Project 6 papers must produce at least 3 qualified research gaps.")
        for g in gaps:
            self.assertEqual(g["supported_paper_count"], 2, f"Gap '{g['title']}' must report supported_paper_count == 2.")
            self.assertEqual(len(g["source_papers"]), 2)

    # Test O: Reasoning paper IDs match supporting paper IDs
    def test_O_reasoning_paper_ids_match_supporting_paper_ids(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = self.project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=self.project_papers, project_name="Plant Disease Detection")
        for g in gaps:
            r = g["gap_reasoning"]
            comp_a_pids = r["component_a_papers"]
            comp_b_pids = r["component_b_papers"]
            combined_reasoning_pids = sorted(list(set(comp_a_pids + comp_b_pids)))
            src_pids = sorted([p["paper_id"] for p in g["source_papers"]])
            self.assertEqual(combined_reasoning_pids, src_pids, "Reasoning paper IDs must match source_papers/supporting_paper_ids.")

    # Test P: No unrelated project paper is counted merely because it belongs to the project
    def test_P_no_unrelated_project_paper_counted(self):
        unrelated_paper = ResearchPaper(
            id=99,
            title="Quantum Computing in Cryptography",
            abstract="Quantum cryptography analysis.",
            algorithms=["Quantum Net"],
            datasets=[],
            methodologies=[],
            application_domains=["Cryptography"]
        )
        papers_with_unrelated = self.project_papers + [unrelated_paper]
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = papers_with_unrelated
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=papers_with_unrelated, project_name="Plant Disease Detection")
        for g in gaps:
            src_pids = [p["paper_id"] for p in g["source_papers"]]
            self.assertNotIn(99, src_pids, "Unrelated paper ID 99 must NOT be counted in gap supporting papers.")
            self.assertEqual(g["supported_paper_count"], 2)


if __name__ == "__main__":
    unittest.main()
