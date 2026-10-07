import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.research_gap_service import ResearchGapService
from app.services.research_direction_service import ResearchDirectionService
from app.models.paper_model import ResearchPaper


class TestPairwiseRelationshipValidationRegression(unittest.TestCase):

    def setUp(self):
        self.kg_service = KnowledgeGraphService()
        self.gap_service = ResearchGapService(graph_service=self.kg_service)

    # 1. Underrepresentation alone does NOT create an opportunity
    def test_01_underrepresentation_alone_not_gap(self):
        p1 = ResearchPaper(id=1, title="Paper A", keywords=["Crop Health"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Paper B", keywords=["Crop Health"], algorithms=["CNN", "Axial Transformer"], datasets=[], methodologies=[], application_domains=[])
        p3 = ResearchPaper(id=3, title="Paper C", keywords=["Crop Health"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        
        all_papers = [p1, p2, p3]
        self.kg_service.build_graph(all_papers)

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = all_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=all_papers)
        axial_gaps = [g for g in gaps if g["missing_concept"].lower() == "axial transformer"]
        self.assertEqual(len(axial_gaps), 0, "Underrepresented entity 'Axial Transformer' present in Paper B must NOT be flagged as missing research gap.")

    # 2. High link prediction alone does NOT create an opportunity
    def test_02_high_link_prediction_alone_not_opportunity(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        fake_gaps = [{
            "source_paper_id": 1,
            "target_label": "UnrelatedConcept",
            "target_type": "KEYWORD",
            "evidence_classification": "UNDERREPRESENTATION_ONLY",
            "evidence": {"gap_score": 0.70, "semantic_evidence": 0.02, "link_prediction_score": 0.85, "underrepresentation_score": 0.9},
            "explanation": ["High link prediction score only."]
        }]

        p1 = ResearchPaper(id=1, title="Paper 1", abstract="Abstract", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])

        with patch.object(ResearchGapService, "detect_gaps", return_value=fake_gaps):
            response = ResearchDirectionService.generate_directions(
                db=mock_db, top_k=5, project_id=1, project_name="Test Domain", project_papers=[p1]
            )

        self.assertEqual(len(response.directions), 0, "High link prediction alone with low semantic evidence must be gated out.")

    # 3. Low semantic relationship evidence + high graph score -> rejected or UNDERREPRESENTATION_ONLY
    def test_03_low_semantic_high_graph_gated_out(self):
        p1 = ResearchPaper(id=1, title="Agricultural Productivity", abstract="Text", keywords=["Agriculture"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Quantum Computing Networks", abstract="Text", keywords=["Agriculture"], algorithms=["Quantum Net"], datasets=[], methodologies=[], application_domains=[])
        
        all_papers = [p1, p2]
        self.kg_service.build_graph(all_papers)

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = all_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=all_papers)
        quantum_gaps = [g for g in gaps if g["missing_concept"].lower() == "quantum net"]
        self.assertEqual(len(quantum_gaps), 0, "Quantum Net with zero semantic relationship relevance must be gated out.")

    # 4. Entity A in Paper 1 + Entity B in Paper 2 does NOT automatically mean A+B is a gap
    def test_04_cross_paper_entities_not_automatic_gap(self):
        p1 = ResearchPaper(id=1, title="Paper A", keywords=["Domain"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Paper B", keywords=["Domain"], algorithms=["SVM"], datasets=[], methodologies=[], application_domains=[])
        
        all_papers = [p1, p2]
        self.kg_service.build_graph(all_papers)

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = all_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=all_papers)
        svm_gaps = [g for g in gaps if g["missing_concept"].lower() == "svm"]
        self.assertEqual(len(svm_gaps), 0, "Cross-paper entity SVM is already in collection (Paper 2) and must not be marked as missing concept.")

    # 5. A+B explicitly supported by literature -> valid candidate
    def test_05_explicitly_supported_relationship(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        fake_gaps = [{
            "source_paper_id": 1,
            "target_label": "Diffusion Models",
            "target_type": "ALGORITHM",
            "evidence_classification": "DIRECTLY_SUPPORTED",
            "evidence": {"gap_score": 0.85, "semantic_evidence": 0.75, "link_prediction_score": 0.80, "underrepresentation_score": 1.0},
            "explanation": ["Literature signal in paper suggests future work on Diffusion Models."]
        }]

        p1 = ResearchPaper(id=1, title="Paper 1", abstract="Future work will investigate diffusion models for image augmentation.", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])

        with patch.object(ResearchGapService, "detect_gaps", return_value=fake_gaps):
            response = ResearchDirectionService.generate_directions(
                db=mock_db, top_k=5, project_id=1, project_name="Image Processing", project_papers=[p1]
            )

        self.assertGreaterEqual(len(response.directions), 1)
        self.assertEqual(response.directions[0].confidence, "High")

    # 6. A+B appears together in an indexed paper -> not treated as unexplored
    def test_06_co_occurring_pair_not_unexplored(self):
        p1 = ResearchPaper(id=1, title="Paper A", keywords=[], algorithms=["CNN", "Attention Mechanisms"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Paper B", keywords=[], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        
        all_papers = [p1, p2]
        self.kg_service.build_graph(all_papers)

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = all_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=all_papers)
        att_gaps = [g for g in gaps if g["missing_concept"].lower() == "attention mechanisms"]
        self.assertEqual(len(att_gaps), 0, "CNN and Attention Mechanisms already co-occur in Paper A and must not be marked as unexplored gap.")

    # 7. Symmetric relationship deduplication: A+B == B+A
    def test_07_symmetric_relationship_deduplication(self):
        from app.services.research_direction_service import compute_opportunity_key
        key1 = compute_opportunity_key("CNN", "Attention Mechanisms", "Plant Disease")
        key2 = compute_opportunity_key("Attention Mechanisms", "CNN", "Plant Disease")
        self.assertEqual(key1, key2, "Symmetric relationship keys must be identical.")

    # 8. Multiple concepts from the same Paper A -> Paper B pair do not create redundant opportunities
    def test_08_redundancy_control(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        fake_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Fusion Dataset",
                "target_type": "DATASET",
                "evidence_classification": "STRONGLY_INFERRED",
                "evidence": {"gap_score": 0.80, "semantic_evidence": 0.50, "link_prediction_score": 0.75, "underrepresentation_score": 0.8},
                "explanation": ["Cross evaluation candidate."]
            },
            {
                "source_paper_id": 1,
                "target_label": "Fusion Dataset",
                "target_type": "DATASET",
                "evidence_classification": "STRONGLY_INFERRED",
                "evidence": {"gap_score": 0.75, "semantic_evidence": 0.45, "link_prediction_score": 0.70, "underrepresentation_score": 0.8},
                "explanation": ["Redundant duplicate candidate."]
            }
        ]

        p1 = ResearchPaper(id=1, title="Paper 1", abstract="Abstract text", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])

        with patch.object(ResearchGapService, "detect_gaps", return_value=fake_gaps):
            response = ResearchDirectionService.generate_directions(
                db=mock_db, top_k=5, project_id=1, project_name="Plant Disease", project_papers=[p1]
            )

        self.assertEqual(len(response.directions), 1, "Redundant variations of the same relationship pair must collapse into a single direction.")

    # 9. Confidence cannot be Moderate/High when relationship evidence is insufficient
    def test_09_confidence_qualification(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        fake_gaps = [{
            "source_paper_id": 1,
            "target_label": "WeakTarget",
            "target_type": "KEYWORD",
            "evidence_classification": "UNDERREPRESENTATION_ONLY",
            "evidence": {"gap_score": 0.70, "semantic_evidence": 0.10, "link_prediction_score": 0.80, "underrepresentation_score": 0.9},
            "explanation": ["Weak evidence."]
        }]

        p1 = ResearchPaper(id=1, title="Paper 1", abstract="Abstract", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])

        with patch.object(ResearchGapService, "detect_gaps", return_value=fake_gaps):
            response = ResearchDirectionService.generate_directions(
                db=mock_db, top_k=5, project_id=1, project_name="Plant Disease", project_papers=[p1]
            )

        self.assertEqual(len(response.directions), 0, "Candidates with low relationship evidence must not receive Moderate or High confidence.")

    # 10. Project 6 regression test
    def test_10_project_6_pipeline_regression(self):
        p14 = ResearchPaper(id=14, title="Evaluating YOLO", keywords=["Crop Health"], algorithms=["YOLOv5", "CNN"], datasets=["PlantDoc"], methodologies=[], application_domains=["Plant Disease Detection"])
        p15 = ResearchPaper(id=15, title="Swin-Axial Transformer", keywords=["Crop Health", "Attention Mechanisms"], algorithms=["Transformer", "Axial Transformer", "Swin Transformer"], datasets=["PlantDoc", "Fusion Dataset"], methodologies=["Self-Attention"], application_domains=["Plant Disease Classification"])
        p16 = ResearchPaper(id=16, title="Explainable AI", keywords=["Visual Explanations", "AI"], algorithms=["CNN", "ResNet"], datasets=["PlantVillage"], methodologies=["Explainable AI", "LIME"], application_domains=["Plant Disease Classification"])
        
        project_papers = [p14, p15, p16]
        self.kg_service.build_graph(project_papers)

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = project_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=project_papers, project_name="Plant Disease Detection and Classification Using AI")
        
        # Verify that in-collection entities (e.g. Axial Transformer, PlantDoc, Attention Mechanisms) are not reported as missing gaps
        gap_targets = [g["missing_concept"].lower() for g in gaps]
        self.assertNotIn("axial transformer", gap_targets)
        self.assertNotIn("plantdoc", gap_targets)
        self.assertNotIn("attention mechanisms", gap_targets)

    # 11. Scientific Relationship Plausibility Gate Regression Test (Section 10 Requirements)
    def test_11_scientific_relationship_plausibility_gate(self):
        # Test direct plausibility helper function
        plausible_tf_xai, ev_tf_xai, _ = self.gap_service.is_scientifically_plausible_relationship(
            "Transformer", "ALGORITHM", "Explainable AI", "METHODOLOGY", "Plant Disease Detection"
        )
        self.assertTrue(plausible_tf_xai, "Transformer + XAI must be accepted by the plausibility gate.")
        self.assertGreaterEqual(ev_tf_xai, 0.70)

        plausible_yolo_xai, ev_yolo_xai, _ = self.gap_service.is_scientifically_plausible_relationship(
            "YOLOv8", "ALGORITHM", "Explainable AI", "METHODOLOGY", "Plant Disease Detection"
        )
        self.assertTrue(plausible_yolo_xai, "YOLO + XAI must be accepted by the plausibility gate.")
        self.assertGreaterEqual(ev_yolo_xai, 0.70)

        plausible_dc_rf, ev_dc_rf, _ = self.gap_service.is_scientifically_plausible_relationship(
            "Deep Convolution", "ALGORITHM", "Random Forest", "ALGORITHM", "Plant Disease Detection"
        )
        self.assertFalse(plausible_dc_rf, "Deep Convolution + Random Forest MUST be rejected by the plausibility gate.")

        # Test CNN + XAI rejection when already present in paper 16
        p16 = ResearchPaper(id=16, title="Explainable AI", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=["Explainable AI"], application_domains=["Plant Disease Classification"])
        project_papers = [p16]
        self.kg_service.build_graph(project_papers)
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = project_papers
        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=project_papers, project_name="Plant Disease Detection")
        cnn_xai_gaps = [g for g in gaps if "cnn" in g.get("missing_concept", "").lower() and "explainable" in g.get("missing_concept", "").lower()]
        self.assertEqual(len(cnn_xai_gaps), 0, "CNN + XAI must be rejected as a research gap because it already co-occurs in Paper 16.")

        # Test YOLO + PlantDoc (YOLO in paper 14 already co-occurs with PlantDoc in paper 14)
        p14 = ResearchPaper(id=14, title="Evaluating YOLO", keywords=[], algorithms=["YOLOv5"], datasets=["PlantDoc"], methodologies=[], application_domains=["Plant Disease Detection"])
        self.kg_service.build_graph([p14])
        mock_db.query.return_value.all.return_value = [p14]
        yolo_plantdoc_gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=[p14], project_name="Plant Disease Detection")
        self.assertEqual(len(yolo_plantdoc_gaps), 0, "YOLO + PlantDoc already co-occur in Paper 14 and must not be marked as a missing research gap.")

    # 12. Canonical Gap Deduplication & Relationship Normalization Test (Section 11 Requirements A-G)
    def test_12_canonical_gap_deduplication_regression(self):
        p14 = ResearchPaper(id=14, title="Evaluating YOLO", keywords=[], algorithms=["YOLOv5", "YOLOv8", "YOLOv9"], datasets=["PlantDoc"], methodologies=[], application_domains=["Plant Disease Detection"])
        p15 = ResearchPaper(id=15, title="Swin-Axial Transformer", keywords=[], algorithms=["Transformer", "Axial Transformer", "Swin-Axial Transformer", "Vision Transformer"], datasets=["Fusion Dataset"], methodologies=["Self-Attention"], application_domains=["Plant Disease Classification"])
        p16 = ResearchPaper(id=16, title="Explainable AI", keywords=[], algorithms=["CNN", "ResNet"], datasets=["PlantVillage"], methodologies=["Explainable Artificial Intelligence", "LIME"], application_domains=["Plant Disease Classification"])

        project_papers = [p14, p15, p16]
        self.kg_service.build_graph(project_papers)
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = project_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=project_papers, project_name="Plant Disease Detection and Classification Using AI")
        rel_keys = [g["evidence"].get("canonical_relationship_key") for g in gaps]

        # Requirement A & B: Transformer + XAI / Vision Transformer + XAI / Swin + XAI / LIME -> exactly ONE canonical gap
        tf_xai_gaps = [g for g in gaps if g["evidence"].get("canonical_relationship_key") == "FAMILY_EXPLAINABILITY___FAMILY_TRANSFORMER"]
        self.assertEqual(len(tf_xai_gaps), 1, "Transformer variants and XAI/LIME variants MUST collapse into exactly ONE canonical gap.")
        tf_gap = tf_xai_gaps[0]
        aliases = tf_gap["evidence"].get("evidence_aliases", [])
        self.assertIn("Swin-Axial Transformer", aliases)
        self.assertIn("LIME", aliases)
        self.assertIn("Explainable Artificial Intelligence", aliases)

        # Requirement C: YOLO + XAI remains a separate valid gap
        yolo_xai_gaps = [g for g in gaps if g["evidence"].get("canonical_relationship_key") == "FAMILY_EXPLAINABILITY___FAMILY_YOLO"]
        self.assertEqual(len(yolo_xai_gaps), 1, "YOLO + XAI MUST remain a separate valid canonical gap.")

        # Requirement G: Transformer + YOLO remains a distinct valid relationship
        tf_yolo_gaps = [g for g in gaps if g["evidence"].get("canonical_relationship_key") == "FAMILY_TRANSFORMER___FAMILY_YOLO"]
        self.assertEqual(len(tf_yolo_gaps), 1, "Transformer + YOLO MUST remain a distinct valid canonical gap.")

        # Requirement D: YOLO + PlantDoc (co-occurs in paper 14) is rejected
        yolo_plantdoc_gaps = [g for g in gaps if "yolo" in g["missing_concept"].lower() and "plantdoc" in g["missing_concept"].lower()]
        self.assertEqual(len(yolo_plantdoc_gaps), 0, "YOLO + PlantDoc must be rejected due to same-paper co-occurrence.")

        # Requirement E & F: Deep Convolution + Random Forest and Edge Computing + Random Forest rejected
        plausible_dc_rf, _, _ = self.gap_service.is_scientifically_plausible_relationship(
            "Deep Convolution", "ALGORITHM", "Random Forest", "ALGORITHM", "Plant Disease"
        )
        self.assertFalse(plausible_dc_rf, "Deep Convolution + Random Forest must be rejected.")

        plausible_ec_rf, _, _ = self.gap_service.is_scientifically_plausible_relationship(
            "Edge Computing", "KEYWORD", "Random Forest", "ALGORITHM", "Plant Disease"
        )
        self.assertFalse(plausible_ec_rf, "Edge Computing + Random Forest must be rejected.")

    # 13. Calibration & Score Convergence Regression Tests (Requirements A-L)
    def test_13_scoring_calibration_and_reasoning_regression(self):
        p14 = ResearchPaper(id=14, title="Evaluating YOLO", keywords=[], algorithms=["YOLOv5", "YOLOv8", "YOLOv9"], datasets=["PlantDoc"], methodologies=[], application_domains=["Plant Disease Detection"])
        p15 = ResearchPaper(id=15, title="Swin-Axial Transformer", keywords=[], algorithms=["Transformer", "Axial Transformer", "Swin-Axial Transformer", "Vision Transformer"], datasets=["Fusion Dataset"], methodologies=["Self-Attention"], application_domains=["Plant Disease Classification"])
        p16 = ResearchPaper(id=16, title="Explainable AI", keywords=[], algorithms=["CNN", "ResNet"], datasets=["PlantVillage"], methodologies=["Explainable Artificial Intelligence", "LIME"], application_domains=["Plant Disease Classification"])

        project_papers = [p14, p15, p16]
        self.kg_service.build_graph(project_papers)
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = project_papers

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10, papers=project_papers, project_name="Plant Disease Detection and Classification Using AI")
        
        # Test B: Four different canonical gaps are NOT assigned the exact same fixed score
        scores = [g["gap_score"] for g in gaps]
        self.assertGreater(len(gaps), 1, "Must generate at least 2 canonical gaps for Project 6 papers.")
        self.assertFalse(all(s == scores[0] for s in scores), f"Four different canonical gaps MUST NOT all receive identical score {scores[0]}. Scores: {scores}")

        # Test A: Different evidence produces different scores
        unique_scores = set(scores)
        self.assertGreater(len(unique_scores), 1, "Different canonical gaps with different evidence must produce distinct scores.")

        # Test C: Passing a threshold does not mean final_score == threshold (e.g. 0.72 or 0.70)
        self.assertNotIn(0.72, scores, "Scores must be evidence-calculated continuous values, not stuck on 0.72.")

        # Test D: Canonical merging recalculates the score rather than max(score)
        for g in gaps:
            ev = g["evidence"]
            rel_ev = ev.get("relationship_evidence_score")
            final_sc = g["gap_score"]
            self.assertIsNotNone(rel_ev)
            self.assertIsNotNone(final_sc)
            # Verify internal score components are exposed
            for key in ["role_compatibility", "task_relevance", "methodological_compatibility", "textual_evidence", "cross_paper_support", "semantic_evidence", "future_work_evidence", "underrepresentation", "relationship_evidence_score", "final_gap_score"]:
                self.assertIn(key, ev, f"Internal score component '{key}' must be exposed in evidence dictionary.")

        # Test E: Transformer + XAI aliases merge into exactly one canonical gap
        tf_xai_gaps = [g for g in gaps if g["evidence"].get("canonical_relationship_key") == "FAMILY_EXPLAINABILITY___FAMILY_TRANSFORMER"]
        self.assertEqual(len(tf_xai_gaps), 1, "Transformer + XAI aliases must merge into exactly ONE canonical gap.")

        # Test F: YOLO + XAI remains a separate canonical gap
        yolo_xai_gaps = [g for g in gaps if g["evidence"].get("canonical_relationship_key") == "FAMILY_EXPLAINABILITY___FAMILY_YOLO"]
        self.assertEqual(len(yolo_xai_gaps), 1, "YOLO + XAI must remain a separate canonical gap.")

        # Test G: Transformer + YOLO remains a separate canonical gap
        tf_yolo_gaps = [g for g in gaps if g["evidence"].get("canonical_relationship_key") == "FAMILY_TRANSFORMER___FAMILY_YOLO"]
        self.assertEqual(len(tf_yolo_gaps), 1, "Transformer + YOLO must remain a separate canonical gap.")

        # Test H: Same-paper combinations remain rejected
        yolo_plantdoc = [g for g in gaps if "yolo" in g["missing_concept"].lower() and "plantdoc" in g["missing_concept"].lower()]
        self.assertEqual(len(yolo_plantdoc), 0, "Same-paper combination YOLO + PlantDoc must be rejected.")

        # Test I: Invalid scientific combinations remain rejected
        dc_rf, _, _ = self.gap_service.is_scientifically_plausible_relationship("Deep Convolution", "ALGORITHM", "Random Forest", "ALGORITHM", "Plant Disease")
        self.assertFalse(dc_rf, "Invalid scientific combination Deep Convolution + Random Forest must be rejected.")

        # Test J: Underrepresentation alone cannot create a gap
        for g in gaps:
            self.assertEqual(g["evidence"].get("underrepresentation"), 0.0, "Underrepresentation alone must not create a gap.")

        # Test K: Gap reasoning contains actual supporting evidence
        for g in gaps:
            reasoning = g.get("gap_reasoning", {})
            self.assertIn("component_a_evidence", reasoning)
            self.assertIn("component_b_evidence", reasoning)
            self.assertIn("missing_relationship", reasoning)
            self.assertIn("task_alignment", reasoning)
            self.assertIn("scientific_compatibility", reasoning)
            self.assertIn("evidence_limitation", reasoning)

        # Test L: No global novelty claims are generated
        for g in gaps:
            full_text = f"{g.get('title', '')} {g.get('description', '')} {str(g.get('gap_reasoning', ''))}".lower()
            self.assertNotIn("globally unexplored", full_text)
            self.assertNotIn("novel research gap worldwide", full_text)
            self.assertNotIn("never been studied", full_text)
            self.assertIn("indexed collection", full_text)


if __name__ == "__main__":
    unittest.main()


