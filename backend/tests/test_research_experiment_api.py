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


class TestResearchExperimentAPI(unittest.TestCase):

    def setUp(self):
        init_db(engine)
        self.db = TestingSessionLocal()
        # Create test projects
        self.proj_a = ResearchProject(name="Project Alpha", description="CV project", status="ACTIVE")
        self.proj_b = ResearchProject(name="Project Beta", description="NLP project", status="ACTIVE")
        self.db.add(self.proj_a)
        self.db.add(self.proj_b)
        self.db.commit()
        self.db.refresh(self.proj_a)
        self.db.refresh(self.proj_b)

    def tearDown(self):
        self.db.close()

    def test_01_get_project_experiments_empty(self):
        """Test GET /api/projects/{id}/experiments returns empty list for new project."""
        response = client.get(f"/api/projects/{self.proj_a.id}/experiments")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_02_get_project_experiment_summary(self):
        """Test GET /api/projects/{id}/experiments/summary returns valid metrics summary."""
        response = client.get(f"/api/projects/{self.proj_a.id}/experiments/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("total_planned", data)
        self.assertIn("not_started_count", data)
        self.assertIn("in_progress_count", data)
        self.assertIn("completed_count", data)
        self.assertIn("results_recorded_count", data)
        self.assertIn("needs_attention_count", data)

    def test_03_import_planned_experiments_workflow(self):
        """
        Test Requirements:
        - import planned experiments
        - status initialized to NOT_STARTED
        - no empirical results fabricated
        - duplicate import protection
        """
        dir_id_1 = "OPP_001_DETECTION_XAI"
        
        # Save a Research Plan for Opportunity 1
        plan_payload = {
            "direction_id": dir_id_1,
            "plan_data": {
                "title": "Explainable Object Detection Methodology Plan",
                "experiments": [
                    {
                        "experiment_number": 1,
                        "title": "Exp 1: Baseline Detector Performance",
                        "purpose": "Evaluate baseline detector on benchmark split.",
                        "variables": "Standalone Detector Baseline",
                        "baseline": "Detector Baseline",
                        "metrics": ["Precision", "Recall", "mAP@0.5"]
                    },
                    {
                        "experiment_number": 2,
                        "title": "Exp 2: Proposed Integrated Model",
                        "purpose": "Evaluate combined detector + XAI pipeline.",
                        "variables": "Proposed Architecture",
                        "baseline": "Detector Baseline",
                        "metrics": ["Precision", "Recall", "mAP@0.5", "Attribution Stability"]
                    }
                ],
                "dataset_plan": [{"name": "Benchmark Dataset"}],
                "proposed_method": {"architecture_name": "Proposed XAI-Detector"}
            },
            "notes": "Plan for Opportunity 1"
        }
        res_save = client.post(f"/api/projects/{self.proj_a.id}/research-plan/save", json=plan_payload)
        self.assertEqual(res_save.status_code, 200)

        # 1. First Import
        res_import1 = client.post(f"/api/projects/{self.proj_a.id}/experiments/import-plan", json={"direction_id": dir_id_1})
        self.assertEqual(res_import1.status_code, 200)
        data1 = res_import1.json()

        self.assertEqual(data1["project_id"], self.proj_a.id)
        self.assertEqual(data1["opportunity_id"], dir_id_1)
        self.assertEqual(data1["imported_count"], 2)
        self.assertEqual(data1["skipped_count"], 0)
        self.assertEqual(len(data1["experiments"]), 2)

        # Check status initialization and zero result fabrication
        for exp in data1["experiments"]:
            self.assertEqual(exp["status"], "NOT_STARTED")
            self.assertEqual(len(exp["runs"]), 0)  # Zero fake runs/results

        # 2. Second Import (Duplicate Protection)
        res_import2 = client.post(f"/api/projects/{self.proj_a.id}/experiments/import-plan", json={"direction_id": dir_id_1})
        self.assertEqual(res_import2.status_code, 200)
        data2 = res_import2.json()

        self.assertEqual(data2["imported_count"], 0)
        self.assertEqual(data2["skipped_count"], 2)
        self.assertIn("already imported", data2["message"])

    def test_04_project_and_opportunity_isolation(self):
        """
        Test Requirements:
        - Experiments from Project A must never appear in Project B.
        - Importing Opportunity 2 does not overwrite Opportunity 1 experiments.
        """
        dir_id_1 = "OPP_001_DETECTION_XAI"
        dir_id_2 = "OPP_002_TRANSFORMER_COMPARISON"

        # Save & import Plan 1 for Project A
        client.post(f"/api/projects/{self.proj_a.id}/research-plan/save", json={
            "direction_id": dir_id_1,
            "plan_data": {
                "title": "Plan Opp 1",
                "experiments": [{"experiment_number": 1, "title": "Opp 1 Exp A", "purpose": "Test Opp 1", "baseline": "Base 1"}]
            }
        })
        client.post(f"/api/projects/{self.proj_a.id}/experiments/import-plan", json={"direction_id": dir_id_1})

        # Save & import Plan 2 for Project A
        client.post(f"/api/projects/{self.proj_a.id}/research-plan/save", json={
            "direction_id": dir_id_2,
            "plan_data": {
                "title": "Plan Opp 2",
                "experiments": [{"experiment_number": 1, "title": "Opp 2 Exp B", "purpose": "Test Opp 2", "baseline": "Base 2"}]
            }
        })
        client.post(f"/api/projects/{self.proj_a.id}/experiments/import-plan", json={"direction_id": dir_id_2})

        # Check Project A experiments: contains both Opp 1 and Opp 2 exps without overwriting
        res_exps_a = client.get(f"/api/projects/{self.proj_a.id}/experiments")
        self.assertEqual(res_exps_a.status_code, 200)
        exps_a = res_exps_a.json()
        self.assertEqual(len(exps_a), 2)
        exp_titles_a = [e["name"] for e in exps_a]
        self.assertIn("Opp 1 Exp A", exp_titles_a)
        self.assertIn("Opp 2 Exp B", exp_titles_a)

        # Check Project B experiments: contains 0 experiments (Strict Project Isolation)
        res_exps_b = client.get(f"/api/projects/{self.proj_b.id}/experiments")
        self.assertEqual(res_exps_b.status_code, 200)
        self.assertEqual(len(res_exps_b.json()), 0)

    def test_05_custom_experiments_remain_independent(self):
        """Test custom experiment creation remains independent of research plans."""
        create_payload = {
            "name": "Custom User Benchmarking Test",
            "purpose": "Independent manual verification",
            "experiment_type": "CUSTOM",
            "status": "NOT_STARTED",
            "baseline_config": {"algorithm": "Baseline Model"},
            "proposed_config": {"architecture": "Custom Model"}
        }
        res_create = client.post(f"/api/projects/{self.proj_a.id}/experiments", json=create_payload)
        self.assertEqual(res_create.status_code, 201)
        exp = res_create.json()

        self.assertEqual(exp["name"], "Custom User Benchmarking Test")
        self.assertEqual(exp["execution_config"]["origin"], "CUSTOM")

    def test_06_create_run_and_record_empirical_results(self):
        """Test creating run and recording student-entered empirical results."""
        create_payload = {
            "name": "EXP-RUN-TEST Empirical Verification",
            "purpose": "Record real PyTorch run metrics",
            "experiment_type": "BASELINE_COMPARISON",
            "status": "NOT_STARTED"
        }
        res_create = client.post(f"/api/projects/{self.proj_a.id}/experiments", json=create_payload)
        exp_id = res_create.json()["id"]

        # Add Run
        res_run = client.post(f"/api/projects/{self.proj_a.id}/experiments/{exp_id}/runs", json={"seed": 42, "notes": "Run 1"})
        self.assertEqual(res_run.status_code, 201)
        run_id = res_run.json()["id"]

        # Record Results
        results_payload = [
            {"metric_name": "Accuracy", "metric_value": "0.88", "unit": "0-1", "method_type": "proposed"}
        ]
        res_rec = client.post(f"/api/projects/{self.proj_a.id}/experiments/runs/{run_id}/results", json=results_payload)
        self.assertEqual(res_rec.status_code, 201)
        self.assertEqual(len(res_rec.json()), 1)

        # Check summary reflects results_recorded_count = 1
        res_sum = client.get(f"/api/projects/{self.proj_a.id}/experiments/summary")
        self.assertEqual(res_sum.json()["results_recorded_count"], 1)

    def test_07_mark_experiment_complete_lifecycle(self):
        """
        Test Requirements:
        - NOT_STARTED -> COMPLETED updates DB
        - COMPLETED persists on reload
        - Zero result fabrication: results_recorded_count remains unchanged
        - Project isolation: Wrong project_id cannot modify experiment
        - Invalid experiment_id returns 404
        - Repeating completion does not corrupt data
        - All other fields (dataset, baseline, proposed, metrics, origin) preserved
        """
        # 1. Create Experiment in Project A
        create_payload = {
            "name": "EXP-COMPLETE-TEST Model Verification",
            "purpose": "Verify model completion flow",
            "experiment_type": "BASELINE_COMPARISON",
            "status": "NOT_STARTED",
            "dataset_config": {"dataset_name": "TestDataset", "samples": "1000"},
            "baseline_config": {"algorithm": "ResNet-18"},
            "proposed_config": {"architecture": "Proposed Transformer"},
            "execution_config": {"origin": "PLANNED", "metrics": ["Accuracy", "F1"]}
        }
        res_create = client.post(f"/api/projects/{self.proj_a.id}/experiments", json=create_payload)
        self.assertEqual(res_create.status_code, 201)
        exp_id = res_create.json()["id"]

        # Initial Summary Check
        res_sum_before = client.get(f"/api/projects/{self.proj_a.id}/experiments/summary").json()
        completed_before = res_sum_before["completed_count"]
        not_started_before = res_sum_before["not_started_count"]

        # 2. Mark Experiment Complete
        update_payload = {
            "status": "COMPLETED",
            "dataset_config": {"dataset_name": "TestDataset", "samples": "1000"},
            "baseline_config": {"algorithm": "ResNet-18"},
            "proposed_config": {"architecture": "Proposed Transformer"},
            "execution_config": {"origin": "PLANNED", "metrics": ["Accuracy", "F1"]}
        }
        res_update = client.patch(f"/api/projects/{self.proj_a.id}/experiments/{exp_id}", json=update_payload)
        self.assertEqual(res_update.status_code, 200)
        updated_exp = res_update.json()

        # Assert status updated and fields preserved
        self.assertEqual(updated_exp["status"], "COMPLETED")
        self.assertEqual(updated_exp["dataset_config"]["dataset_name"], "TestDataset")
        self.assertEqual(updated_exp["baseline_config"]["algorithm"], "ResNet-18")
        self.assertEqual(updated_exp["proposed_config"]["architecture"], "Proposed Transformer")
        self.assertEqual(updated_exp["execution_config"]["origin"], "PLANNED")

        # 3. Persistence Check on GET
        res_get = client.get(f"/api/projects/{self.proj_a.id}/experiments/{exp_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["status"], "COMPLETED")

        # 4. Summary & Counters Check
        res_sum_after = client.get(f"/api/projects/{self.proj_a.id}/experiments/summary").json()
        self.assertEqual(res_sum_after["completed_count"], completed_before + 1)
        self.assertEqual(res_sum_after["not_started_count"], not_started_before - 1)
        # Academic Integrity: Results recorded count remains 0 for this experiment (no runs added)
        self.assertEqual(res_sum_after["results_recorded_count"], 0)

        # 5. Project Isolation: Attempting to update with Project B's ID should return 404
        res_wrong_proj = client.patch(f"/api/projects/{self.proj_b.id}/experiments/{exp_id}", json={"status": "COMPLETED"})
        self.assertEqual(res_wrong_proj.status_code, 404)

        # 6. Invalid Experiment ID returns 404
        res_invalid_exp = client.patch(f"/api/projects/{self.proj_a.id}/experiments/999999", json={"status": "COMPLETED"})
        self.assertEqual(res_invalid_exp.status_code, 404)

        # 7. Repeating completion does not corrupt data
        res_repeat = client.patch(f"/api/projects/{self.proj_a.id}/experiments/{exp_id}", json={"status": "COMPLETED"})
        self.assertEqual(res_repeat.status_code, 200)
        self.assertEqual(res_repeat.json()["status"], "COMPLETED")


