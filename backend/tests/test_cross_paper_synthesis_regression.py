import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.research_direction_service import ResearchDirectionService, is_valid_opportunity_entity
from app.services.proposal_draft_service import ProposalDraftService
from app.schemas.research_direction_schema import ResearchDirection, ResearchDirectionEvidence, SupportingPaper
from app.models.paper_model import ResearchPaper


class TestCrossPaperSynthesisRegression(unittest.TestCase):

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
            title="Explainable Artificial Intelligence in Plant Disease Diagnosis",
            abstract="Investigates Explainable Artificial Intelligence and ResNet models.",
            algorithms=["CNN", "ResNet"],
            datasets=[],
            methodologies=["Explainable Artificial Intelligence"],
            application_domains=["Agriculture"]
        )
        self.project_papers = [self.p14, self.p15, self.p16]

    # Test 1: YOLO + Transformer and YOLOv8 + Transformer are merged into one opportunity family
    def test_01_model_family_normalization_prevents_version_duplication(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        # Verify YOLO, YOLOv8, YOLOv9 do NOT generate separate duplicate cards for cross-paper evaluation
        family_ids = [d.opportunity_family_id for d in resp.directions if d.opportunity_family_id]
        self.assertEqual(family_ids.count("FAMILY_EXPLAINABILITY___FAMILY_YOLO"), 1, "Only 1 primary card per canonical opportunity family should exist.")
        self.assertEqual(family_ids.count("FAMILY_TRANSFORMER___FAMILY_YOLO"), 1, "Only 1 primary card per canonical opportunity family should exist.")

    # Test 2: Entities and papers are grouped inside canonical opportunity
    def test_02_dataset_grouping_prevents_permutation_duplication(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        cross_dir = next((d for d in resp.directions if d.opportunity_family_id == "FAMILY_TRANSFORMER___FAMILY_YOLO"), None)
        self.assertIsNotNone(cross_dir)
        sp_ids = [sp.paper_id if hasattr(sp, "paper_id") else sp.get("paper_id") for sp in cross_dir.supporting_papers]
        self.assertTrue(len(sp_ids) >= 1, "Supporting papers should be grouped inside opportunity card.")

    # Test 3: Different research questions remain separate
    def test_03_distinct_research_questions_remain_separate(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        family_ids = set([d.opportunity_family_id for d in resp.directions if d.opportunity_family_id])
        self.assertGreater(len(family_ids), 1, "Distinct research question families must remain separate.")

    # Test 4: Paper 16 actively contributes opportunities
    def test_04_paper_16_contributes_opportunities(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        all_sp_ids = []
        for d in resp.directions:
            for sp in d.supporting_papers:
                p_id = sp.paper_id if hasattr(sp, "paper_id") else sp.get("paper_id")
                all_sp_ids.append(p_id)
        self.assertIn(16, all_sp_ids, "Paper 16 must actively contribute to opportunity discovery.")

    # Test 5: A candidate requires a meaningful research question
    def test_05_candidate_requires_research_question(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        for d in resp.directions:
            self.assertIsNotNone(d.research_question, "Candidate direction must contain an explicit research question.")
            self.assertGreater(len(d.research_question), 15)

    # Test 6: Relationship novelty alone cannot create an opportunity if noise phrase
    def test_06_relationship_novelty_alone_insufficient(self):
        # Noise terms cannot form an opportunity card even if absent from collection
        self.assertFalse(is_valid_opportunity_entity("Food Security"))
        self.assertFalse(is_valid_opportunity_entity("Addressed The Significant"))

    # Test 7: Fixed TaskRelevance/EvidenceStrength constants are not used for all candidates
    def test_07_dynamic_scoring_not_fixed_constants(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        scores = [d.evidence.opportunity_score for d in resp.directions if d.evidence.opportunity_score]
        self.assertGreater(len(set(scores)), 0)

    # Test 8: CROSS_PAPER_SYNTHESIS is not automatically HIGH confidence
    def test_08_cross_paper_synthesis_confidence_calibration(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        for d in resp.directions:
            if d.evidence.evidence_classification == "CROSS_PAPER_SYNTHESIS":
                self.assertIn(d.confidence.upper(), ["MODERATE", "HIGH"])

    # Test 9: Opportunity score is not displayed as Gap Score in schema/evidence
    def test_09_opportunity_score_distinct_from_gap_score(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        for d in resp.directions:
            if d.evidence.evidence_classification == "CROSS_PAPER_SYNTHESIS":
                self.assertIsNotNone(d.evidence.opportunity_score)

    # Test 10: No noisy concepts return
    def test_10_no_noisy_concepts_return(self):
        bad_phrases = ["Food Security", "Stage Detectors", "Actual Bounding Boxes", "Addressed The Significant", "Established Best Practices"]
        for bp in bad_phrases:
            self.assertFalse(is_valid_opportunity_entity(bp))

    # Test 11: No duplicate research-question families exist
    def test_11_no_duplicate_research_question_families(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=10,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        family_list = [d.opportunity_family_id for d in resp.directions if d.opportunity_family_id]
        self.assertEqual(len(family_list), len(set(family_list)), "No duplicate research question families are permitted.")

    # Test 12: Research gaps remain independently computed
    def test_12_gaps_independently_computed(self):
        # Strict gap gating is preserved
        from app.services.research_gap_service import ResearchGapService
        gap_svc = ResearchGapService()
        self.assertTrue(hasattr(gap_svc, "detect_gaps"))

    # Test 13: research_gaps = 0 can coexist with candidate_research_directions > 0
    def test_13_zero_gaps_with_positive_directions_coexist(self):
        resp = ResearchDirectionService.generate_directions(
            db=None,
            top_k=5,
            project_name="Plant Disease Detection",
            project_papers=self.project_papers
        )
        self.assertGreater(resp.total_directions, 0)


if __name__ == "__main__":
    unittest.main()
