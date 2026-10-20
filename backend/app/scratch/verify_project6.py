import sys
from pathlib import Path
import json
from unittest.mock import patch

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.services.research_direction_service import ResearchDirectionService
from app.models.paper_model import ResearchPaper

db = SessionLocal()
try:
    intel_response = ProjectIntelligenceService.analyze_project(project_id=6, db=db)
    intel_dict = intel_response.model_dump()
    
    print("=== PROJECT 6 RESEARCH GAPS ===")
    print(f"Total Gaps Count: {len(intel_dict['research_gaps'])}")
    for gap in intel_dict['research_gaps']:
        print(f"  - Missing Concept: {gap['missing_concept']} | Type: {gap['concept_type']} | Gap Score: {gap['gap_score']}")

    print("\n=== PROJECT 6 UNDERREPRESENTED CONCEPTS ===")
    print(f"Total Underrepresented Count: {len(intel_dict['underrepresented_concepts'])}")
    for u in intel_dict['underrepresented_concepts'][:10]:
        print(f"  - Name: {u['name']} | Type: {u['type']} | Coverage: {u['coverage_percentage']}% ({u['paper_count']} paper)")

    # Test Candidate Research Opportunities when a genuine collection-missing gap is detected
    fake_gaps = [{
        "source_paper_id": 16,
        "source_paper_title": "Improving Plant Disease Classification With Deep-Learning-Based Prediction Model Using Explainable Artificial Intelligence",
        "target_label": "Diffusion Models",
        "target_type": "ALGORITHM",
        "relationship_type": "uses_algorithm",
        "evidence": {
            "gap_score": 0.82,
            "semantic_evidence": 0.75,
            "link_prediction_score": 0.80,
            "underrepresentation_score": 1.0
        },
        "explanation": ["Collection-missing generative algorithm candidate for synthetic disease augmentation."]
    }]

    assigned_paper_ids = [14, 15, 16]
    papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(assigned_paper_ids)).all()

    with patch("app.services.research_direction_service.ResearchGapService.detect_gaps", return_value=fake_gaps):
        dirs_response = ResearchDirectionService.generate_directions(
            db=db,
            top_k=5,
            project_id=6,
            project_name="Plant Disease Detection and Classification Using AI",
            project_papers=papers
        )
        dirs_dict = dirs_response.model_dump()

    print("\n=== VERIFYING OPPORTUNITY GENERATION & DEDUPLICATION ===")
    print(f"Total Directions Generated: {len(dirs_dict['directions'])}")
    for d in dirs_dict['directions']:
        print(f"\nOpportunity Title: {d['title']}")
        print(f"  Candidate Algorithms: {[a['name'] for a in d['candidate_algorithms']]}")
        print(f"  Candidate Datasets: {[ds['name'] for ds in d['candidate_datasets']]}")
        print(f"  Candidate Methodologies: {[m['name'] for m in d['candidate_methodologies']]}")
        print(f"  Supporting Concepts: {d['supporting_concepts']}")

finally:
    db.close()
