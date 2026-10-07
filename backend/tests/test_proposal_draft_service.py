import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.research_direction_schema import (
    ResearchDirectionResponse,
    ResearchDirection,
    ResearchDirectionEvidence,
    SupportingPaper,
    CandidateAlgorithm,
    CandidateDataset,
    CandidateMethodology
)
from app.schemas.proposal_draft_schema import ProposalDraft
from app.services.proposal_draft_service import ProposalDraftService, LLMProvider, DRAFT_DISCLAIMER


class MockSuccessProvider(LLMProvider):
    def generate_proposal(self, direction: ResearchDirection) -> ProposalDraft:
        return ProposalDraft(
            proposal_id="mock_prop_99",
            source_direction_id=direction.direction_id,
            title=f"LLM Generated: {direction.title}",
            abstract="LLM synthesized abstract.",
            problem_statement="LLM problem statement.",
            research_motivation="LLM motivation.",
            research_question="How does YOLOv8 affect accuracy?",
            objectives=["1. Evaluate baseline.", "2. Compare metrics."],
            related_work_synthesis="LLM related work.",
            research_gap="LLM research gap.",
            proposed_methodology="LLM methodology.",
            candidate_algorithms=["YOLOv8"],
            candidate_datasets=["COCO"],
            dataset_evaluation_plan="LLM evaluation plan.",
            experimental_plan="LLM experimental plan.",
            evaluation_metrics="Accuracy, Precision",
            expected_contribution="LLM expected contribution.",
            limitations="LLM limitations.",
            supporting_papers=[],
            evidence_summary={},
            generation_mode="llm",
            generation_timestamp="2026-08-23T00:00:00Z",
            disclaimer=DRAFT_DISCLAIMER
        )


class MockFailingProvider(LLMProvider):
    def generate_proposal(self, direction: ResearchDirection) -> ProposalDraft:
        raise RuntimeError("LLM API Timeout or Quota Exceeded")


class TestProposalDraftService(unittest.TestCase):
    """
    Unit tests for ProposalDraftService template synthesis, LLM mode, and fallback handling.
    """

    def setUp(self):
        self.sample_evidence = ResearchDirectionEvidence(
            gap_score=0.85,
            semantic_evidence=0.78,
            link_prediction_score=0.92,
            collection_coverage=25.0,
            underrepresentation_score=0.65
        )

        self.sample_direction = ResearchDirection(
            direction_id="dir_1",
            title="Explore YOLOv8 + Transformer for Autonomous Driving",
            research_problem="Current papers investigate Autonomous Driving using YOLOv8, while integration with Transformer remains underrepresented.",
            motivation="Indexed collection contains papers referencing related concepts with a gap score of 0.85.",
            existing_evidence=["Strong link prediction."],
            missing_aspect="Integration of Transformer is underrepresented.",
            proposed_direction="Investigate whether combining YOLOv8 with Transformer could explore methodology enhancements.",
            supporting_papers=[
                SupportingPaper(paper_id=10, title="Driver Behavior Study", role="Provides domain context.")
            ],
            supporting_concepts=["Autonomous Driving", "YOLOv8", "Transformer"],
            candidate_algorithms=[CandidateAlgorithm(name="YOLOv8", supporting_paper_count=1, reason="Baseline algorithm.")],
            candidate_datasets=[CandidateDataset(name="COCO", supporting_paper_count=1, reason="Benchmark dataset.")],
            candidate_methodologies=[CandidateMethodology(name="Deep Learning", paper_count=1, coverage_percentage=25.0)],
            evidence=self.sample_evidence,
            direction_score=0.80,
            confidence="High",
            disclaimer=DRAFT_DISCLAIMER
        )

        self.mock_resp = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.sample_direction],
            collection_disclaimer="Global disclaimer."
        )

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_01_template_mode_synthesis(self, mock_gen_dir):
        """Verify template-guided fallback synthesis generates valid ProposalDraft."""
        mock_gen_dir.return_value = self.mock_resp
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_1")
        proposal = resp.proposal

        self.assertEqual(proposal.generation_mode, "template")
        self.assertEqual(proposal.source_direction_id, "dir_1")
        self.assertEqual(proposal.title, "Explore YOLOv8 + Transformer for Autonomous Driving")
        self.assertIn("Autonomous Driving", proposal.abstract)
        self.assertIn(DRAFT_DISCLAIMER, proposal.disclaimer)
        self.assertEqual(proposal.candidate_algorithms, ["YOLOv8"])
        self.assertEqual(proposal.candidate_datasets, ["COCO"])

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_02_evidence_preservation(self, mock_gen_dir):
        """Verify scores and supporting papers are preserved in ProposalDraft."""
        mock_gen_dir.return_value = self.mock_resp
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_1")
        proposal = resp.proposal

        self.assertEqual(proposal.evidence_summary["gap_score"], 0.85)
        self.assertEqual(proposal.evidence_summary["direction_score"], 0.80)
        self.assertEqual(len(proposal.supporting_papers), 1)
        self.assertEqual(proposal.supporting_papers[0]["paper_id"], 10)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_03_custom_llm_provider_success(self, mock_gen_dir):
        """Verify custom/mock LLM provider returns LLM generation mode."""
        mock_gen_dir.return_value = self.mock_resp
        mock_db = MagicMock()
        success_provider = MockSuccessProvider()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_1", custom_provider=success_provider)
        proposal = resp.proposal

        self.assertEqual(proposal.generation_mode, "llm")
        self.assertIn("LLM Generated", proposal.title)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_04_llm_provider_failure_fallback(self, mock_gen_dir):
        """Verify LLM failure or exception falls back seamlessly to template mode."""
        mock_gen_dir.return_value = self.mock_resp
        mock_db = MagicMock()
        failing_provider = MockFailingProvider()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_1", custom_provider=failing_provider)
        proposal = resp.proposal

        self.assertEqual(proposal.generation_mode, "template")
        self.assertEqual(proposal.source_direction_id, "dir_1")

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_05_missing_direction_404(self, mock_gen_dir):
        """Verify non-existent direction_id raises 404 Not Found exception."""
        mock_gen_dir.return_value = self.mock_resp
        mock_db = MagicMock()

        with self.assertRaises(Exception) as cm:
            ProposalDraftService.synthesize_draft(db=mock_db, direction_id="non_existent_dir_999")
        self.assertEqual(cm.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
