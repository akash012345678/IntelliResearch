import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.link_prediction_service import LinkPredictionService
from app.services.research_direction_service import ResearchDirectionService
from app.models.paper_model import ResearchPaper
from app.models.project_model import ProjectPaper

db = SessionLocal()
try:
    assigned_paper_ids = list(set([pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == 6).all()]))
    papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(assigned_paper_ids)).all()

    kg_svc = KnowledgeGraphService()
    kg_svc.build_graph(papers)
    graph = kg_svc.get_graph()

    link_svc = LinkPredictionService(graph_service=kg_svc)
    raw_candidates = link_svc.predict_links(graph=graph, top_k=20)

    print("=== RAW LINK PREDICTION CANDIDATES FOR PROJECT 6 PAPERS ===")
    for idx, c in enumerate(raw_candidates[:10], start=1):
        print(f"{idx}. Source Paper {c['source_paper_id']} -> Target '{c['target_label']}' ({c['target_type']}) | Link Score: {c['scores']['combined']:.4f}")

    # Build simulated gap candidates representing the original underrepresented candidates
    gaps_sim = []
    for idx, c in enumerate(raw_candidates[:10], start=1):
        p_obj = next((p for p in papers if p.id == c['source_paper_id']), papers[0])
        gaps_sim.append({
            "source_paper_id": c['source_paper_id'],
            "source_paper_title": p_obj.title,
            "target_label": c['target_label'],
            "target_type": c['target_type'],
            "relationship_type": c['relationship_type'],
            "evidence": {
                "gap_score": 0.65 + (10 - idx) * 0.02,
                "semantic_evidence": 0.60,
                "link_prediction_score": c['scores']['combined'],
                "underrepresentation_score": 0.6667
            },
            "explanation": [f"Simulated gap candidate for {c['target_label']}"]
        })

    dirs_res = ResearchDirectionService.generate_directions(
        db=db,
        top_k=10,
        project_id=6,
        project_name="Plant Disease Detection and Classification Using AI",
        project_papers=papers
    )

    # Directly pass gaps_sim to generate_directions logic to trace Opportunities #1, #2, #3, #4
    from app.services.embedding_service import EmbeddingService
    
    # Trace generated opportunities from gaps_sim
    print("\n=== GENERATED OPPORTUNITIES FROM SIMULATED GAP CANDIDATES ===")
    
    # We test ResearchDirectionService with gaps_sim manually
    directions_by_key = {}
    for gap in gaps_sim:
        gap_src_id = gap["source_paper_id"]
        gap_target_label = gap["target_label"]
        gap_target_type = gap["target_type"].upper()
        source_paper = next((p for p in papers if p.id == gap_src_id), papers[0])
        
        p_algos = source_paper.algorithms or []
        p_datasets = source_paper.datasets or []
        p_methodologies = source_paper.methodologies or []
        p_domains = source_paper.application_domains or []
        p_keywords = source_paper.keywords or []
        
        primary_algo = p_algos[0] if p_algos else "baseline algorithms"
        research_domain = "Plant Disease Detection and Classification Using AI"

        # Determine specialized entity tokens
        cand_algos = []
        if primary_algo:
            cand_algos.append({"name": primary_algo})
        if gap_target_type == "ALGORITHM" and gap_target_label != primary_algo:
            cand_algos.append({"name": gap_target_label})

        cand_datasets = []
        if p_datasets:
            cand_datasets.append({"name": p_datasets[0]})
        if gap_target_type == "DATASET":
            cand_datasets.append({"name": gap_target_label})

        cand_methodologies = []
        if gap_target_type == "METHODOLOGY":
            cand_methodologies.append({"name": gap_target_label})

        # Deduplication logic
        specialized_tokens = set()
        for ca in cand_algos: specialized_tokens.add(ca["name"].lower())
        for cd in cand_datasets: specialized_tokens.add(cd["name"].lower())
        for cm in cand_methodologies: specialized_tokens.add(cm["name"].lower())
        for item in (p_algos + p_datasets + p_methodologies + p_domains):
            if item: specialized_tokens.add(item.lower())

        kw_pool = p_keywords + [gap_target_label]
        filtered_supp = []
        seen = set()
        for kw in kw_pool:
            if not kw or not isinstance(kw, str): continue
            n_kw = kw.strip().lower()
            if not n_kw: continue
            is_dup = False
            if n_kw in specialized_tokens or n_kw in seen:
                is_dup = True
            else:
                for spec in specialized_tokens:
                    if len(n_kw) >= 3 and len(spec) >= 3 and (n_kw == spec or n_kw in spec or spec in n_kw):
                        is_dup = True
                        break
            if not is_dup:
                seen.add(n_kw)
                filtered_supp.append(kw.strip())

        opp_title = f"Opportunity ({gap_target_type}): {gap_target_label} + {primary_algo}"
        print(f"\nGap Target: {gap_target_label} | Type: {gap_target_type} | Source Paper ID: {gap_src_id}")
        print(f"  Title: {opp_title}")
        print(f"  Candidate Algorithms: {[a['name'] for a in cand_algos]}")
        print(f"  Candidate Datasets: {[d['name'] for d in cand_datasets]}")
        print(f"  Candidate Methodologies: {[m['name'] for m in cand_methodologies]}")
        print(f"  Supporting Concepts (Filtered): {filtered_supp[:3]}")

finally:
    db.close()
