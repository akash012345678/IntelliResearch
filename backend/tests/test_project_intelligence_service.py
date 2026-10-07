import sys
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import Base
import app.models  # noqa: F401
from app.models.paper_model import ResearchPaper
from app.schemas.project_schema import ResearchProjectCreate
from app.schemas.proposal_persistence_schema import ProposalCreate
from app.services.research_project_service import ResearchProjectService
from app.services.proposal_persistence_service import ProposalPersistenceService
from app.services.project_intelligence_service import ProjectIntelligenceService


class TestProjectIntelligenceService(unittest.TestCase):
    """
    Unit tests for project-scoped research intelligence calculation.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

        # Add 3 test papers
        self.p1 = ResearchPaper(
            title="Driver Drowsiness Detection using CNN",
            abstract="CNN based visual driver drowsiness monitoring.",
            full_text="Sample full text for paper 1",
            filename="paper1.pdf",
            keywords=["drowsiness", "vision"],
            algorithms=["CNN"],
            datasets=["NTHU-DDD"],
            methodologies=["Deep Learning"],
            application_domains=["Autonomous Driving"]
        )
        self.p2 = ResearchPaper(
            title="Temporal Modeling for Fatigue with LSTM",
            abstract="Recurrent neural network monitoring for driver fatigue.",
            full_text="Sample full text for paper 2",
            filename="paper2.pdf",
            keywords=["drowsiness", "recurrent"],
            algorithms=["LSTM"],
            datasets=["NTHU-DDD"],
            methodologies=["Deep Learning"],
            application_domains=["Autonomous Driving"]
        )
        self.p3 = ResearchPaper(
            title="Unrelated Paper on Quantum Computing",
            abstract="Quantum algorithms and Qubit error correction.",
            full_text="Sample full text for paper 3",
            filename="paper3.pdf",
            keywords=["quantum", "qubit"],
            algorithms=["Shor Algorithm"],
            datasets=["Qiskit-Bench"],
            methodologies=["Quantum Circuit"],
            application_domains=["Physics"]
        )

        self.db.add_all([self.p1, self.p2, self.p3])
        self.db.commit()

        # Create Project & assign ONLY p1 and p2 (NOT p3)
        self.project = ResearchProjectService.create_project(self.db, ResearchProjectCreate(
            name="Driver Safety Intelligence Project"
        ))
        ResearchProjectService.add_paper_to_project(self.db, self.project.id, self.p1.id)
        ResearchProjectService.add_paper_to_project(self.db, self.project.id, self.p2.id)


    def tearDown(self):
        self.db.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()

    def test_01_analyze_project_scoped_isolation(self):
        """Verify project analysis analyzes ONLY assigned papers (2 papers, NOT 3)."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        self.assertEqual(res.collection_summary.total_papers, 2)
        self.assertEqual(len(res.paper_landscape), 2)

        paper_ids = [p.id for p in res.paper_landscape]
        self.assertIn(self.p1.id, paper_ids)
        self.assertIn(self.p2.id, paper_ids)
        self.assertNotIn(self.p3.id, paper_ids)

    def test_02_shared_concepts_and_coverage(self):
        """Verify shared concept classification and coverage percentage calculation."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        algos = res.shared_concepts["algorithms"]
        algo_names = [a.name for a in algos]
        self.assertIn("CNN", algo_names)
        self.assertIn("LSTM", algo_names)

        # CNN appears in 1/2 papers -> UNDERREPRESENTED
        cnn_item = next(a for a in algos if a.name == "CNN")
        self.assertEqual(cnn_item.paper_count, 1)
        self.assertEqual(cnn_item.coverage_percentage, 50.0)
        self.assertEqual(cnn_item.classification, "UNDERREPRESENTED")

        # NTHU-DDD dataset appears in 2/2 papers -> COMMON
        datasets = res.shared_concepts["datasets"]
        nthu_item = next(d for d in datasets if d.name == "NTHU-DDD")
        self.assertEqual(nthu_item.paper_count, 2)
        self.assertEqual(nthu_item.coverage_percentage, 100.0)
        self.assertEqual(nthu_item.classification, "COMMON")

    def test_03_empty_project_state(self):
        """Verify empty project with 0 papers returns clean empty collection summary."""
        empty_proj = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Empty Project"))
        res = ProjectIntelligenceService.analyze_project(empty_proj.id, self.db)
        self.assertEqual(res.collection_summary.total_papers, 0)
        self.assertEqual(len(res.paper_landscape), 0)

    def test_04_proposal_traceability(self):
        """Verify saved proposal is connected in Proposal Traceability."""
        prop = ProposalPersistenceService.create_proposal(self.db, ProposalCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Drowsiness Proposal V1",
            proposal_data={
                "title": "Drowsiness Proposal V1",
                "candidate_algorithms": ["CNN", "LSTM"],
                "supporting_papers": [{"paper_id": self.p1.id, "title": self.p1.title}]
            }
        ))

        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        self.assertEqual(len(res.proposal_traceability), 1)
        tr = res.proposal_traceability[0]
        self.assertEqual(tr.proposal_id, prop.id)
        self.assertEqual(tr.title, "Drowsiness Proposal V1")
        self.assertEqual(tr.current_version_number, 1)

    def test_05_gap_uses_actual_entity_name(self):
        """Verify gaps use real extracted entity names and never generic 'Concept' string."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        for g in res.research_gaps:
            self.assertNotEqual(g.missing_concept.lower(), "concept")
            self.assertNotEqual(g.missing_concept.lower(), "algorithm")
            self.assertNotEqual(g.missing_concept.lower(), "dataset")
            self.assertNotEqual(g.missing_concept.lower(), "methodology")
            self.assertTrue(len(g.missing_concept) >= 2)

    def test_06_generic_concept_label_is_not_used(self):
        """Verify generic placeholder labels are strictly rejected by canonicalize_concept_name."""
        from app.services.research_gap_service import canonicalize_concept_name
        self.assertEqual(canonicalize_concept_name("Concept"), "")
        self.assertEqual(canonicalize_concept_name("algorithm"), "")
        self.assertEqual(canonicalize_concept_name("Dataset"), "")
        self.assertEqual(canonicalize_concept_name("methodology"), "")
        self.assertEqual(canonicalize_concept_name("Model"), "")
        self.assertEqual(canonicalize_concept_name("LSTM"), "LSTM")
        self.assertEqual(canonicalize_concept_name("lstm"), "LSTM")
        self.assertEqual(canonicalize_concept_name("Vision Transformer"), "Vision Transformer")

    def test_07_duplicate_gaps_are_merged(self):
        """Verify duplicate gaps for the same concept across multiple papers are aggregated into 1 gap."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        gap_concepts = [g.missing_concept.lower() for g in res.research_gaps]
        # All gap concepts must be unique (no duplicate gaps for the same concept)
        self.assertEqual(len(gap_concepts), len(set(gap_concepts)))

    def test_08_duplicate_source_papers_are_removed(self):
        """Verify source papers inside each aggregated gap are unique."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        for g in res.research_gaps:
            p_ids = [sp["paper_id"] for sp in g.source_papers]
            self.assertEqual(len(p_ids), len(set(p_ids)))

    def test_09_gap_evidence_is_target_specific(self):
        """Verify explanations and evidence inside each gap are target-specific."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        for g in res.research_gaps:
            self.assertIn(g.missing_concept, g.explanation)
            self.assertIn("gap_score", g.model_dump())
            self.assertGreaterEqual(g.gap_score, 0.0)

    def test_10_project_scoping_is_preserved(self):
        """Verify gaps only come from assigned project papers (p1, p2) and ignore unassigned p3."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        for g in res.research_gaps:
            for sp in g.source_papers:
                self.assertNotEqual(sp["paper_id"], self.p3.id)
                self.assertIn(sp["paper_id"], [self.p1.id, self.p2.id])

    def test_11_stored_intelligence_caching_and_refresh(self):
        """Verify normal page navigation uses fast-read cache while refresh=True or paper list changes recomputes."""
        ProjectIntelligenceService.invalidate_cache()
        # Initial analysis (stores cache)
        res1 = ProjectIntelligenceService.analyze_project(self.project.id, self.db, refresh=False)
        self.assertEqual(res1.collection_summary.total_papers, 2)
        self.assertIn(self.project.id, ProjectIntelligenceService._stored_intelligence_cache)

        # Normal navigation call (uses cache)
        res2 = ProjectIntelligenceService.analyze_project(self.project.id, self.db, refresh=False)
        self.assertIs(res1, res2)

        # Explicit refresh (recomputes and returns fresh object)
        res3 = ProjectIntelligenceService.analyze_project(self.project.id, self.db, refresh=True)
        self.assertEqual(res3.collection_summary.total_papers, 2)

        # Paper addition invalidates/updates cache on next read
        ResearchProjectService.add_paper_to_project(self.db, self.project.id, self.p3.id)
        res4 = ProjectIntelligenceService.analyze_project(self.project.id, self.db, refresh=False)
        self.assertEqual(res4.collection_summary.total_papers, 3)

    def test_13_paper_count_and_coverage_denominator_consistency(self):
        """Verify that total_papers in collection_summary, paper_landscape length, and coverage denominator match the exact assigned project papers."""
        proj = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="3-Paper Consistency Project"))
        ResearchProjectService.add_paper_to_project(self.db, proj.id, self.p1.id)
        ResearchProjectService.add_paper_to_project(self.db, proj.id, self.p2.id)
        ResearchProjectService.add_paper_to_project(self.db, proj.id, self.p3.id)

        res = ProjectIntelligenceService.analyze_project(proj.id, self.db, refresh=True)
        self.assertEqual(res.collection_summary.total_papers, 3)
        self.assertEqual(len(res.paper_landscape), 3)

        landscape_ids = [p.id for p in res.paper_landscape]
        self.assertEqual(set(landscape_ids), {self.p1.id, self.p2.id, self.p3.id})

        # Shor Algorithm is in 1 of 3 papers -> coverage_percentage = 33.3%
        algos = res.shared_concepts["algorithms"]
        shor_item = next((a for a in algos if a.name == "Shor Algorithm"), None)
        if shor_item:
            self.assertEqual(shor_item.paper_count, 1)
            self.assertEqual(shor_item.coverage_percentage, 33.3)


if __name__ == "__main__":
    unittest.main()
