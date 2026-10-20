import sys
import os

sys.path.insert(0, os.getcwd())

from app.database.session import SessionLocal
from app.services.project_intelligence_service import ProjectIntelligenceService

db = SessionLocal()
res = ProjectIntelligenceService.analyze_project(6, db, refresh=True)

print("==================================================")
print("PROJECT 6 FINAL OPPORTUNITY FAMILY AUDIT")
print("==================================================")
print(f"Total Papers: {res.collection_summary.total_papers}")
print(f"Research Gaps Count: {len(res.research_gaps)}")
print(f"Underrepresented Concepts Count: {len(res.underrepresented_concepts)}")
print(f"Candidate Research Directions Count: {len(res.candidate_research_directions)}")
print("==================================================")

for i, d in enumerate(res.candidate_research_directions):
    print(f"\nOpportunity #{i+1}: {d.title}")
    print(f"  Opportunity Family: {d.opportunity_family_id}")
    print(f"  Research Question: {d.research_question}")
    print(f"  Confidence: {d.confidence}")
    print(f"  Evidence Classification: {d.evidence.get('evidence_classification')}")
    print(f"  Opportunity Score: {d.evidence.get('opportunity_score')}")
    print(f"  Supporting Concepts: {d.supporting_concepts}")
    print("  Supporting Papers:")
    for sp in d.supporting_papers:
        p_id = sp.get('paper_id') if isinstance(sp, dict) else getattr(sp, 'paper_id', None)
        p_title = sp.get('title') if isinstance(sp, dict) else getattr(sp, 'title', None)
        p_role = sp.get('role') if isinstance(sp, dict) else getattr(sp, 'role', None)
        print(f"    - Paper ID {p_id}: '{p_title}' (Role: {p_role})")

db.close()
