import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.link_prediction_service import LinkPredictionService
from app.services.research_gap_service import ResearchGapService
from app.services.research_direction_service import ResearchDirectionService
from app.services.embedding_service import EmbeddingService
from app.models.paper_model import ResearchPaper
from app.models.project_model import ProjectPaper, ResearchProject

db = SessionLocal()
try:
    project = db.query(ResearchProject).filter(ResearchProject.id == 6).first()
    assigned_paper_ids = list(set([pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == 6).all()]))
    papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(assigned_paper_ids)).all()

    print(f"Project 6: '{project.name}'")
    print(f"Assigned Papers ({len(papers)}):")
    for p in papers:
        print(f"\nPaper ID {p.id}: '{p.title}'")
        print(f"  Algorithms: {getattr(p, 'algorithms', [])}")
        print(f"  Datasets: {getattr(p, 'datasets', [])}")
        print(f"  Methodologies: {getattr(p, 'methodologies', [])}")
        print(f"  Domains: {getattr(p, 'application_domains', [])}")
        print(f"  Keywords: {getattr(p, 'keywords', [])}")

    kg_svc = KnowledgeGraphService()
    for p in papers:
        kg_svc.add_paper(p)
    graph = kg_svc.get_graph()

    link_svc = LinkPredictionService(graph_service=kg_svc)
    link_candidates = link_svc.predict_links(graph=graph, top_k=50)

    print("\n==================================================")
    print("ALL LINK PREDICTION CANDIDATES FOR PROJECT 6 PAPERS")
    print("==================================================")
    for idx, lc in enumerate(link_candidates, start=1):
        print(f"{idx}. Source Paper {lc['source_paper_id']} -> Target '{lc['target_label']}' ({lc['target_type']}) | Combined Link Score: {lc['scores']['combined']:.4f}")

    embed_svc = EmbeddingService()
    gap_svc = ResearchGapService(graph_service=kg_svc, link_prediction_service=link_svc, embedding_service=embed_svc)

    print("\n==================================================")
    print("DETAILED SCORING ANALYSIS FOR LINK PREDICTION CANDIDATES")
    print("==================================================")
    target_terms = [
        "Fusion Dataset",
        "Attention Mechanisms",
        "Axial Compression",
        "Deep Convolution",
        "Explainable Artificial Intelligence",
        "PlantDoc",
        "Axial Transformer",
        "DenseNet"
    ]

    for term in target_terms:
        # Find candidate matching term
        match_lc = next((lc for lc in link_candidates if lc['target_label'].lower() == term.lower()), None)
        if not match_lc:
            print(f"\n[Term: '{term}'] No link prediction candidate generated.")
            continue
        
        src_p_id = match_lc['source_paper_id']
        source_paper = next((p for p in papers if p.id == src_p_id), papers[0])
        source_title = source_paper.title
        source_domains = [d.lower() for d in (getattr(source_paper, "application_domains", []) or [])]
        source_kws = [k.lower() for k in (getattr(source_paper, "keywords", []) or [])]
        
        source_context = f"{project.name}. {source_title}. {getattr(source_paper, 'abstract', '') or ''} {' '.join(source_domains)} {' '.join(source_kws)}"
        source_emb = embed_svc.generate_embedding(source_context)
        target_emb = embed_svc.generate_embedding(term)
        domain_sim = gap_svc.compute_similarity(source_emb, target_emb)

        undirected = graph.to_undirected()
        target_node_id = match_lc['target_node_id']
        target_papers = set(undirected.neighbors(target_node_id)) if target_node_id in undirected else set()
        source_neighbors = set(undirected.neighbors(f"paper_{src_p_id}")) if f"paper_{src_p_id}" in undirected else set()

        related_papers = set()
        for c_node in source_neighbors:
            for p_node in undirected.neighbors(c_node):
                if p_node.startswith("paper_") and p_node != f"paper_{src_p_id}":
                    related_papers.add(p_node)

        if related_papers:
            supporting_papers = related_papers.intersection(target_papers)
            cross_paper_support = round(len(supporting_papers) / len(related_papers), 4)
        else:
            cross_paper_support = 0.0

        semantic_evidence = 0.0
        if source_paper and target_papers:
            target_embs = []
            for tp_node in target_papers:
                tp_num_id = graph.nodes[tp_node].get("paper_id")
                tp_obj = next((p for p in papers if p.id == tp_num_id), None)
                if tp_obj:
                    tp_text = f"{tp_obj.title}. {tp_obj.abstract or ''}"
                    target_embs.append(embed_svc.generate_embedding(tp_text))
            if target_embs:
                sims = [gap_svc.compute_similarity(source_emb, te) for te in target_embs]
                semantic_evidence = round(float(max(sims)), 4)

        paper_count = len(target_papers)
        coverage = round(paper_count / len(papers), 4)
        underrep_score = round(max(0.0, 1.0 - coverage), 4)

        link_score = match_lc['scores']['combined']
        substantive_signals_score = (0.45 * link_score + 0.35 * max(semantic_evidence, domain_sim) + 0.20 * cross_paper_support)

        gap_score = round(
            0.35 * link_score +
            0.25 * cross_paper_support +
            0.25 * max(semantic_evidence, domain_sim) +
            0.15 * underrep_score, 4
        )

        print(f"\n--- Analysis for '{term}' (Target Type: {match_lc['target_type']}) ---")
        print(f"  Source Paper ID: {src_p_id} ('{source_title}')")
        print(f"  Target Node ID: {target_node_id}")
        print(f"  Paper Count in Collection: {paper_count} / {len(papers)} (Coverage: {coverage*100:.1f}%)")
        print(f"  underrepresentation_score: {underrep_score:.4f} (Weight: 0.15 => Contribution: {0.15 * underrep_score:.4f})")
        print(f"  link_prediction_score: {link_score:.4f} (Weight: 0.35 => Contribution: {0.35 * link_score:.4f})")
        print(f"  semantic_evidence: {semantic_evidence:.4f}")
        print(f"  domain_similarity: {domain_sim:.4f}")
        print(f"  max(semantic, domain_sim): {max(semantic_evidence, domain_sim):.4f} (Weight: 0.25 => Contribution: {0.25 * max(semantic_evidence, domain_sim):.4f})")
        print(f"  cross_paper_support: {cross_paper_support:.4f} (Weight: 0.25 => Contribution: {0.25 * cross_paper_support:.4f})")
        print(f"  substantive_signals_score: {substantive_signals_score:.4f}")
        print(f"  Calculated gap_score: {gap_score:.4f} ({round(gap_score*100, 1)}%)")

finally:
    db.close()
