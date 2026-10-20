import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database.session import SessionLocal
from app.services.project_intelligence_service import ProjectIntelligenceService

def run_audit():
    db = SessionLocal()
    try:
        # Clear cache first
        ProjectIntelligenceService.invalidate_cache(6)
        res = ProjectIntelligenceService.analyze_project(6, db, refresh=True)
        gaps = res.research_gaps
        print(f"=== PROJECT 6 AUDIT ===")
        print(f"Total research gaps: {len(gaps)}")
        rel_keys = []
        for idx, g in enumerate(gaps, 1):
            g_dict = g.model_dump() if hasattr(g, "model_dump") else g.dict()
            ev = g_dict.get("evidence", {})
            rkey = ev.get("canonical_relationship_key")
            rel_keys.append(rkey)
            print(f"\nGap {idx}:")
            print(f"  Title: {g_dict.get('title')}")
            print(f"  rel_key: {rkey}")
            print(f"  Aliases: {ev.get('evidence_aliases')}")
            print(f"  Supp Papers: {[p.get('paper_id') for p in ev.get('supporting_papers', [])]}")
            print(f"  Gap Reasoning: {g_dict.get('gap_reasoning')}")
        
        print("\nAll canonical rel keys:")
        for rk in rel_keys:
            print(f"  - {rk}")

        dups = [rk for rk in rel_keys if rel_keys.count(rk) > 1]
        print(f"Duplicate rel keys: {set(dups)}")

        dirs = res.candidate_research_directions
        print(f"\nTotal research opportunities: {len(dirs)}")
        for idx, d in enumerate(dirs, 1):
            d_dict = d.model_dump() if hasattr(d, "model_dump") else d.dict()
            print(f"\nOpportunity {idx}:")
            print(f"  Title: {d_dict.get('title')}")
            print(f"  gap_relationship_key: {d_dict.get('gap_relationship_key')}")
            print(f"  parent_gap_id: {d_dict.get('parent_gap_id')}")

    finally:
        db.close()

if __name__ == "__main__":
    run_audit()
