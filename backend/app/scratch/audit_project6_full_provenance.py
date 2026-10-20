import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.link_prediction_service import LinkPredictionService
from app.services.research_gap_service import ResearchGapService, canonicalize_concept_name
from app.services.research_direction_service import ResearchDirectionService, normalize_token
from app.services.embedding_service import EmbeddingService
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.models.paper_model import ResearchPaper
from app.models.project_model import ProjectPaper, ResearchProject

db = SessionLocal()
try:
    print("==================================================")
    print("PART 1 & 2: TRACING 'CNN + DIFFUSION MODELS'")
    print("==================================================")
    # Check if Diffusion Models exists in database
    dm_papers = db.query(ResearchPaper).filter(ResearchPaper.full_text.like("%Diffusion Models%")).all()
    print(f"Papers in DB containing 'Diffusion Models': {len(dm_papers)}")
    
    p6_papers_db = db.query(ResearchPaper).join(ProjectPaper, ResearchPaper.id == ProjectPaper.paper_id).filter(ProjectPaper.project_id == 6).all()
    p6_dm = [p for p in p6_papers_db if "diffusion" in f"{p.title} {p.abstract} {p.full_text}".lower()]
    print(f"Project 6 papers containing 'Diffusion Models': {len(p6_dm)}")

    print("\n==================================================")
    print("PART 3 & 4: PROJECT 6 CANDIDATE PAIR PROVENANCE & CO-OCCURRENCE")
    print("==================================================")
    kg_svc = KnowledgeGraphService()
    for p in p6_papers_db:
        kg_svc.add_paper(p)
    graph = kg_svc.get_graph()

    link_svc = LinkPredictionService(graph_service=kg_svc)
    link_candidates = link_svc.predict_links(graph=graph, top_k=50)

    embed_svc = EmbeddingService()
    gap_svc = ResearchGapService(graph_service=kg_svc, link_prediction_service=link_svc, embedding_service=embed_svc)

    print(f"Total Link Candidates generated for Project 6: {len(link_candidates)}")

    all_pairs_to_check = [
        ("CNN", "Fusion Dataset", 16, "DATASET"),
        ("CNN", "Attention Mechanisms", 16, "KEYWORD"),
        ("CNN", "Axial Compression", 16, "KEYWORD"),
        ("CNN", "Deep Convolution", 16, "METHODOLOGY"),
        ("CNN", "Explainable Artificial Intelligence", 16, "METHODOLOGY"),
        ("Explainable Artificial Intelligence", "CNN", 16, "METHODOLOGY"),
        ("Axial Transformer", "CNN", 15, "ALGORITHM"),
        ("PlantDoc", "CNN", 14, "DATASET")
    ]

    for algo_a, concept_b, src_id, c_type in all_pairs_to_check:
        norm_a = canonicalize_concept_name(algo_a).lower()
        norm_b = canonicalize_concept_name(concept_b).lower()

        co_occurs = False
        co_occur_papers = []
        for p in p6_papers_db:
            p_terms = set(
                [canonicalize_concept_name(x).lower() for x in (getattr(p, 'algorithms', []) or []) if x] +
                [canonicalize_concept_name(x).lower() for x in (getattr(p, 'datasets', []) or []) if x] +
                [canonicalize_concept_name(x).lower() for x in (getattr(p, 'methodologies', []) or []) if x] +
                [canonicalize_concept_name(x).lower() for x in (getattr(p, 'application_domains', []) or []) if x] +
                [canonicalize_concept_name(x).lower() for x in (getattr(p, 'keywords', []) or []) if x]
            )
            if norm_a in p_terms and norm_b in p_terms:
                co_occurs = True
                co_occur_papers.append(p.id)

        # Pairwise Semantic Relationship Query
        rel_query = f"{algo_a} {concept_b} Plant Disease Detection and Classification Using AI"
        rel_query_emb = embed_svc.generate_embedding(rel_query)
        p_embs = [embed_svc.generate_embedding(f"{p.title}. {p.abstract or ''}") for p in p6_papers_db]
        sims = [gap_svc.compute_similarity(rel_query_emb, pe) for pe in p_embs]
        semantic_rel_score = round(float(max(sims)), 4) if sims else 0.0

        # Check future work text
        future_work_kw = ["future work", "limitation", "further research", "could be explored", "unexplored"]
        has_fw = False
        for p in p6_papers_db:
            p_full = f"{p.title} {p.abstract or ''}".lower()
            if any(fw in p_full for fw in future_work_kw):
                if norm_b in p_full or norm_a in p_full:
                    has_fw = True
                    break

        if co_occurs:
            ev_class = "CO_OCCURRING_PAIR"
            decision = "EXCLUDED (Already Co-occurs in Paper ID " + str(co_occur_papers) + ")"
        elif has_fw:
            ev_class = "DIRECTLY_SUPPORTED"
            decision = "QUALIFIED GAP"
        elif semantic_rel_score >= 0.35:
            ev_class = "STRONGLY_INFERRED"
            decision = "QUALIFIED GAP"
        elif any(lc['target_label'].lower() == concept_b.lower() for lc in link_candidates):
            ev_class = "UNDERREPRESENTATION_ONLY"
            decision = "GATED OUT (Insufficient Semantic Evidence)"
        else:
            ev_class = "INSUFFICIENT_EVIDENCE"
            decision = "GATED OUT"

        print(f"\n--- Pair: '{algo_a}' + '{concept_b}' ---")
        print(f"  Co-occurs in same paper: {co_occurs} {co_occur_papers if co_occurs else ''}")
        print(f"  Pairwise Semantic Relationship Score: {semantic_rel_score:.4f}")
        print(f"  Future Work Text Signal: {has_fw}")
        print(f"  Evidence Classification: {ev_class}")
        print(f"  Final Pipeline Decision: {decision}")

    print("\n==================================================")
    print("PART 5: REAL API RESPONSE FOR PROJECT 6")
    print("==================================================")
    intel_response = ProjectIntelligenceService.analyze_project(project_id=6, db=db).model_dump()
    print(f"Real API Research Gaps Count: {len(intel_response['research_gaps'])}")
    print(f"Real API Candidate Directions Count: {len(intel_response['candidate_research_directions'])}")
    print(f"Real API Underrepresented Concepts Count: {len(intel_response['underrepresented_concepts'])}")

    print("\nUnderrepresented concepts in Real API:")
    for u in intel_response['underrepresented_concepts']:
        print(f"  - {u['name']} ({u['type']}): {u['coverage_percentage']}% coverage ({u['paper_count']} paper)")

finally:
    db.close()
