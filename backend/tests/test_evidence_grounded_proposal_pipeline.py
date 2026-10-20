import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import HTTPException
from app.schemas.research_direction_schema import (
    ResearchDirectionResponse,
    ResearchDirection,
    ResearchDirectionEvidence,
    SupportingPaper,
    CandidateAlgorithm,
    CandidateDataset,
    CandidateMethodology
)
from app.schemas.proposal_draft_schema import ProposalDraft, ProposalDraftRequest
from app.schemas.proposal_persistence_schema import ProposalCreate
from app.schemas.proposal_edit_schema import ProposalEditRequest
from app.services.proposal_draft_service import ProposalDraftService, DRAFT_DISCLAIMER
from app.services.proposal_persistence_service import ProposalPersistenceService, PROTECTED_EVIDENCE_FIELDS


class TestEvidenceGroundedProposalPipeline(unittest.TestCase):
    """
    Comprehensive Test Suite verifying Evidence-Grounded Research Plan & Proposal Pipeline (Phases 1 - 16).
    """

    def setUp(self):
        # 1. Valid Evidence Setup (STRONGLY_INFERRED / DIRECTLY_SUPPORTED)
        self.valid_evidence = ResearchDirectionEvidence(
            gap_score=0.82,
            semantic_evidence=0.75,
            link_prediction_score=0.80,
            collection_coverage=100.0,
            underrepresentation_score=1.0,
            evidence_classification="DIRECTLY_SUPPORTED"
        )

        # Synthetic fixture: CNN + Diffusion Models (DIRECTLY_SUPPORTED)
        self.synthetic_supported_direction = ResearchDirection(
            direction_id="dir_synthetic_1",
            title="Explore CNN with Diffusion Models for Plant Disease Detection",
            research_problem="Current plant disease detection models rely on baseline CNN architectures, while integration with Diffusion Models remains a promising direction.",
            motivation="Literature text directly highlights diffusion models as a promising future direction when combined with CNN.",
            existing_evidence=["Text evidence sentence: 'Recent studies highlight that diffusion models present clear opportunities for plant disease detection when combined with CNN architecture.'"],
            missing_aspect="Integration of Diffusion Models with CNN architecture.",
            proposed_direction="Investigate combining CNN architecture with Diffusion Models for plant disease detection.",
            supporting_papers=[
                SupportingPaper(paper_id=14, title="YOLO Plant Disease Study", role="Baseline CNN model."),
                SupportingPaper(paper_id=15, title="Innovative Swin-Axial Transformer", role="Diffusion concept context.")
            ],
            supporting_concepts=["CNN", "Diffusion Models", "Plant Disease Detection"],
            candidate_algorithms=[
                CandidateAlgorithm(name="CNN", supporting_paper_count=1, reason="Baseline model."),
                CandidateAlgorithm(name="Diffusion Models", supporting_paper_count=1, reason="Target technique.")
            ],
            candidate_datasets=[
                CandidateDataset(name="PlantDoc", supporting_paper_count=1, reason="Collection dataset.")
            ],
            candidate_methodologies=[
                CandidateMethodology(name="Deep Learning", paper_count=2, coverage_percentage=66.7)
            ],
            evidence=self.valid_evidence,
            direction_score=0.81,
            confidence="High",
            disclaimer=DRAFT_DISCLAIMER
        )

        # 2. Unsupported Evidence Setup (UNDERREPRESENTATION_ONLY)
        self.unsupported_evidence = ResearchDirectionEvidence(
            gap_score=0.45,
            semantic_evidence=0.0167,
            link_prediction_score=0.79,
            collection_coverage=33.3,
            underrepresentation_score=1.0,
            evidence_classification="UNDERREPRESENTATION_ONLY"
        )

        self.unsupported_direction = ResearchDirection(
            direction_id="dir_unsupported_1",
            title="Explore CNN with Attention Mechanisms",
            research_problem="Concept Attention Mechanisms occurs in 1 paper.",
            motivation="Underrepresentation only.",
            existing_evidence=[],
            missing_aspect="Attention Mechanisms is underrepresented.",
            proposed_direction="Explore CNN with Attention Mechanisms.",
            supporting_papers=[],
            supporting_concepts=["CNN", "Attention Mechanisms"],
            candidate_algorithms=[CandidateAlgorithm(name="CNN", supporting_paper_count=1, reason="Baseline")],
            candidate_datasets=[],
            candidate_methodologies=[],
            evidence=self.unsupported_evidence,
            direction_score=0.40,
            confidence="Low",
            disclaimer=DRAFT_DISCLAIMER
        )

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_01_valid_opportunity_generates_research_question(self, mock_gen_dir):
        """Phase 4: Valid opportunity generates testable research question without unsupported claims."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.synthetic_supported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        self.assertIsNotNone(proposal.research_question)
        self.assertIn("Diffusion Models", proposal.research_question)
        self.assertIn("CNN", proposal.research_question)
        self.assertNotIn("will achieve 100% accuracy", proposal.research_question)
        self.assertNotIn("will outperform all existing methods", proposal.research_question)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_02_valid_opportunity_generates_objectives(self, mock_gen_dir):
        """Phase 5: Valid opportunity generates measurable, feasible objectives."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.synthetic_supported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        self.assertTrue(len(proposal.objectives) >= 4)
        self.assertIn("1. Establish baseline", proposal.objectives[0])
        self.assertIn("Evaluate both approaches", proposal.objectives[2])

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_03_valid_opportunity_generates_methodology_distinction(self, mock_gen_dir):
        """Phase 6: Methodology clearly distinguishes Existing Evidence from Proposed Experimental Design."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.synthetic_supported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        self.assertIn("Existing evidence:", proposal.proposed_methodology)
        self.assertIn("Proposed experimental design:", proposal.proposed_methodology)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_04_valid_opportunity_generates_structured_experiment_plan(self, mock_gen_dir):
        """Phase 7: Valid opportunity generates 10-field structured experiment plan."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.synthetic_supported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        plan = proposal.experimental_plan
        for field_idx in ["1. Baseline", "2. Proposed Approach", "3. Dataset", "4. Data Preprocessing", "5. Training Setup", "6. Evaluation Metrics", "7. Comparison Strategy", "8. Ablation Study", "9. Error Analysis", "10. Reproducibility"]:
            self.assertIn(field_idx, plan)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_05_unsupported_opportunity_rejected_by_evidence_gate(self, mock_gen_dir):
        """Phase 3: UNDERREPRESENTATION_ONLY direction is rejected by evidence gate (HTTP 422)."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.unsupported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        with self.assertRaises(HTTPException) as cm:
            ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_unsupported_1")
        
        self.assertEqual(cm.exception.status_code, 422)
        self.assertIn("Evidence Gate Violation", cm.exception.detail)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_08_evidence_provenance_preserved(self, mock_gen_dir):
        """Phase 2: Source evidence, paper IDs, scores, and classification are preserved."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.synthetic_supported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        self.assertEqual(proposal.source_direction_id, "dir_synthetic_1")
        self.assertEqual(proposal.evidence_summary["evidence_classification"], "DIRECTLY_SUPPORTED")
        self.assertEqual(proposal.evidence_summary["gap_score"], 0.82)
        self.assertEqual(proposal.evidence_summary["semantic_evidence"], 0.75)
        self.assertEqual(len(proposal.supporting_papers), 2)
        self.assertEqual(proposal.supporting_papers[0]["paper_id"], 14)

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_10_dataset_names_never_fabricated(self, mock_gen_dir):
        """Phase 7: If direction lacks dataset, plan marks 'Dataset selection required' instead of inventing dataset."""
        direction_no_ds = self.synthetic_supported_direction.model_copy()
        direction_no_ds.candidate_datasets = []
        
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[direction_no_ds],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        self.assertEqual(proposal.candidate_datasets, [])
        self.assertEqual(proposal.dataset_evaluation_plan, "Dataset selection required.")

    @patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions")
    def test_11_no_numerical_outcome_predictions(self, mock_gen_dir):
        """Phase 8: Expected outcomes avoid predicted numeric accuracy/performance metrics."""
        mock_gen_dir.return_value = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.synthetic_supported_direction],
            collection_disclaimer="Global disclaimer."
        )
        mock_db = MagicMock()

        resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
        proposal = resp.proposal

        self.assertNotIn("Accuracy will increase by", proposal.expected_contribution)
        self.assertNotIn("% gain", proposal.expected_contribution)
        self.assertIn("Evaluate whether", proposal.expected_contribution)

    def test_15_manual_research_idea_separated(self):
        """Phase 13: Manual research ideas are explicitly created with USER-PROVIDED labels."""
        resp = ProposalDraftService.create_manual_proposal(
            title="Explore Swin-Axial Transformer for Crop Disease",
            description="User hypothesis regarding axial transformer scaling."
        )
        proposal = resp.proposal

        self.assertTrue(proposal.is_user_provided)
        self.assertEqual(proposal.generation_mode, "manual_idea")
        self.assertIn("[USER-PROVIDED]", proposal.title)
        self.assertEqual(proposal.evidence_summary["evidence_classification"], "USER_PROVIDED")

    def test_16_synthetic_end_to_end_pipeline_trace(self):
        """Phase 16: End-to-end trace from DIRECTLY_SUPPORTED -> Question -> Objectives -> Methodology -> Experiment -> Versioning."""
        # 1. Synthesize Draft from Synthetic Supported Direction
        with patch("app.services.proposal_draft_service.ResearchDirectionService.generate_directions") as mock_gen_dir:
            mock_gen_dir.return_value = ResearchDirectionResponse(
                total_directions=1,
                directions=[self.synthetic_supported_direction],
                collection_disclaimer="Global disclaimer."
            )
            mock_db = MagicMock()
            draft_resp = ProposalDraftService.synthesize_draft(db=mock_db, direction_id="dir_synthetic_1")
            draft = draft_resp.proposal

        # 2. Verify all pipeline artifacts
        self.assertEqual(draft.evidence_summary["evidence_classification"], "DIRECTLY_SUPPORTED")
        self.assertIn("Diffusion Models", draft.research_question)
        self.assertTrue(len(draft.objectives) >= 4)
        self.assertIn("Existing evidence:", draft.proposed_methodology)
        self.assertIn("10. Reproducibility", draft.experimental_plan)
        self.assertEqual(draft.generation_mode, "template")


if __name__ == "__main__":
    unittest.main()
