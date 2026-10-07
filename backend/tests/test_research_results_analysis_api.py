import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db, init_db
from app.main import app
from app.models.project_model import ResearchProject, SavedResearchDirection, ResearchExperiment

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_fixture.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestResearchResultsAnalysisAPI(unittest.TestCase):

    def setUp(self):
        init_db(engine)
        self.db = TestingSessionLocal()
        self.proj = ResearchProject(name="IntelliResearch Project Test", description="Results analysis test", status="ACTIVE")
        self.db.add(self.proj)
        self.db.commit()
        self.db.refresh(self.proj)

    def tearDown(self):
        self.db.close()

    def test_01_results_analysis_opportunity_scoping_and_empty_state(self):
        """Test results analysis correctly scopes to selected opportunity and handles unrecorded empty state."""
        dir_id_1 = "dir_opp_xai_01"
        saved_dir = SavedResearchDirection(
            project_id=self.proj.id,
            source_direction_id=dir_id_1,
            title="Incorporate Explainable AI into YOLO-Family Object Detection",
            description="Opportunity 1 description",
            confidence="High",
            direction_data={"title": "Incorporate Explainable AI into YOLO-Family Object Detection"}
        )
        self.db.add(saved_dir)

        exp1 = ResearchExperiment(
            project_id=self.proj.id,
            direction_id=dir_id_1,
            name="Standalone YOLO Baseline",
            purpose="Evaluate baseline",
            experiment_type="BASELINE_COMPARISON",
            status="NOT_STARTED",
            execution_config={"origin": "PLANNED", "experiment_number": 1, "metrics": ["mAP@0.5", "FPS"]}
        )
        self.db.add(exp1)
        self.db.commit()

        # GET Results Analysis scoped to dir_id_1
        response = client.get(f"/api/projects/{self.proj.id}/results-analysis?direction_id={dir_id_1}")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["project_id"], self.proj.id)
        self.assertEqual(data["opportunity_id"], dir_id_1)
        self.assertIn("YOLO", data["opportunity_title"])
        self.assertEqual(data["total_experiments"], 1)
        self.assertFalse(data["has_recorded_results"])
        self.assertIn("no experimental results have been recorded", data["notice"].lower())

    def test_02_results_analysis_multi_run_and_comparison_matrix(self):
        """Test empirical result recording, baseline vs proposed comparison, and multi-run statistics calculation."""
        dir_id_1 = "dir_opp_xai_01"
        exp = ResearchExperiment(
            project_id=self.proj.id,
            direction_id=dir_id_1,
            name="Exp 1: Baseline vs Proposed XAI",
            purpose="Benchmark detection performance",
            experiment_type="BASELINE_COMPARISON",
            status="COMPLETED",
            research_question="RQ1: Does XAI improve performance?",
            hypothesis_h0="H0: No difference",
            hypothesis_h1="H1: XAI improves performance",
            dataset_config={"dataset_name": "VOC_2012"},
            baseline_config={"algorithm": "YOLOv8-Baseline"},
            proposed_config={"architecture": "YOLOv8 + GradCAM"},
            execution_config={"origin": "PLANNED", "metrics": ["mAP@0.5", "Latency (ms)"]}
        )
        self.db.add(exp)
        self.db.commit()
        self.db.refresh(exp)

        # Record Run 1
        run1 = client.post(f"/api/projects/{self.proj.id}/experiments/{exp.id}/runs", json={"seed": 42}).json()
        client.post(f"/api/projects/{self.proj.id}/experiments/runs/{run1['id']}/results", json=[
            {"metric_name": "mAP@0.5", "metric_value": "0.82", "unit": "0-1", "method_type": "baseline"},
            {"metric_name": "mAP@0.5", "metric_value": "0.86", "unit": "0-1", "method_type": "proposed"},
            {"metric_name": "Latency (ms)", "metric_value": "30", "unit": "ms", "method_type": "baseline"},
            {"metric_name": "Latency (ms)", "metric_value": "36", "unit": "ms", "method_type": "proposed"}
        ])

        # Record Run 2 (Multi-run)
        run2 = client.post(f"/api/projects/{self.proj.id}/experiments/{exp.id}/runs", json={"seed": 43}).json()
        client.post(f"/api/projects/{self.proj.id}/experiments/runs/{run2['id']}/results", json=[
            {"metric_name": "mAP@0.5", "metric_value": "0.82", "unit": "0-1", "method_type": "baseline"},
            {"metric_name": "mAP@0.5", "metric_value": "0.88", "unit": "0-1", "method_type": "proposed"},
            {"metric_name": "Latency (ms)", "metric_value": "30", "unit": "ms", "method_type": "baseline"},
            {"metric_name": "Latency (ms)", "metric_value": "34", "unit": "ms", "method_type": "proposed"}
        ])

        response = client.get(f"/api/projects/{self.proj.id}/results-analysis?direction_id={dir_id_1}")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["has_recorded_results"])
        self.assertEqual(data["results_recorded_count"], 1)
        self.assertEqual(data["multi_run_experiments_count"], 1)

        exp_analysis = data["experiments_analysis"][0]
        self.assertEqual(exp_analysis["run_count"], 2)
        self.assertGreater(len(exp_analysis["metrics_analysis"]), 0)

        # Verify multi-run stats calculation (Mean, Std Dev, Min, Max)
        multi_stats = exp_analysis["multi_run_stats"]
        self.assertGreater(len(multi_stats), 0)
        map_stats = next(s for s in multi_stats if s["metric_name"] == "mAP@0.5")
        self.assertEqual(map_stats["run_count"], 2)
        self.assertEqual(map_stats["mean"], 0.87)  # (0.86 + 0.88)/2
        self.assertEqual(map_stats["min_val"], 0.86)
        self.assertEqual(map_stats["max_val"], 0.88)

    def test_03_opportunity_isolation_in_results_analysis(self):
        """Test that experiments for Opportunity 1 do not leak into Opportunity 2 results analysis."""
        dir_1 = "dir_opp_1"
        dir_2 = "dir_opp_2"

        exp_opp1 = ResearchExperiment(
            project_id=self.proj.id,
            direction_id=dir_1,
            name="Opp 1 Exp",
            experiment_type="BASELINE_COMPARISON",
            status="NOT_STARTED"
        )
        exp_opp2 = ResearchExperiment(
            project_id=self.proj.id,
            direction_id=dir_2,
            name="Opp 2 Exp",
            experiment_type="BASELINE_COMPARISON",
            status="NOT_STARTED"
        )
        self.db.add(exp_opp1)
        self.db.add(exp_opp2)
        self.db.commit()

        # Analysis for Opp 1 only includes Opp 1 Exp
        res1 = client.get(f"/api/projects/{self.proj.id}/results-analysis?direction_id={dir_1}").json()
        names1 = [e["experiment_name"] for e in res1["experiments_analysis"]]
        self.assertIn("Opp 1 Exp", names1)
        self.assertNotIn("Opp 2 Exp", names1)

        # Analysis for Opp 2 only includes Opp 2 Exp
        res2 = client.get(f"/api/projects/{self.proj.id}/results-analysis?direction_id={dir_2}").json()
        names2 = [e["experiment_name"] for e in res2["experiments_analysis"]]
        self.assertIn("Opp 2 Exp", names2)
        self.assertNotIn("Opp 1 Exp", names2)
