import os
import sys

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database.session import SessionLocal
from app.models.project_model import ResearchProject

def test_extract():
    db = SessionLocal()
    try:
        p = db.query(ResearchProject).filter(ResearchProject.id == 6).first()
        papers = [assoc.paper for assoc in (p.project_papers or []) if assoc.paper]
        exps = p.experiments or []
        proposals = p.proposals or []
        saved_dirs = p.saved_directions or []

        print("=== PAPERS DATASETS & ALGORITHMS ===")
        all_paper_ds = []
        all_paper_alg = []
        for paper in papers:
            ds = getattr(paper, 'datasets', []) or []
            alg = getattr(paper, 'algorithms', []) or []
            print(f"Paper {paper.id} ({paper.title}): datasets={ds}, algorithms={alg}")
            all_paper_ds.extend(ds)
            all_paper_alg.extend(alg)

        print("\n=== EXPERIMENTS CONFIGS ===")
        all_exp_ds = []
        all_exp_bl = []
        all_exp_pr = []
        all_exp_metrics = []
        for e in exps:
            ds_cfg = e.dataset_config or {}
            ds_name = ds_cfg.get("dataset_name") or ds_cfg.get("name")
            ds_all = ds_cfg.get("all_datasets") or []
            if ds_name: all_exp_ds.append(ds_name)
            all_exp_ds.extend(ds_all)

            bl_cfg = e.baseline_config or {}
            bl_alg = bl_cfg.get("algorithm") or bl_cfg.get("name")
            if bl_alg: all_exp_bl.append(bl_alg)

            pr_cfg = e.proposed_config or {}
            pr_arch = pr_cfg.get("architecture") or pr_cfg.get("name")
            if pr_arch: all_exp_pr.append(pr_arch)

            ex_cfg = e.execution_config or {}
            mets = ex_cfg.get("metrics") or ex_cfg.get("target_metrics") or []
            all_exp_metrics.extend(mets)

        print(f"Aggregated Experiment Datasets: {list(set(all_exp_ds))}")
        print(f"Aggregated Baseline Algs: {list(set(all_exp_bl))}")
        print(f"Aggregated Proposed Archs: {list(set(all_exp_pr))}")
        print(f"Aggregated Target Metrics: {list(set(all_exp_metrics))}")

    finally:
        db.close()

if __name__ == "__main__":
    test_extract()
