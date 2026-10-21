"""
IntelliResearch Performance Benchmark Suite
Executes real measurements on the existing codebase:
1. Paper Processing Time (PyMuPDF text extraction + rule-based NLP concept/metadata extraction)
2. Cold AI Model Loading vs Warm FAISS Semantic Search Response Time
3. Knowledge Graph Construction Time (NetworkX graph building from indexed database papers)
4. Research Gap Analysis Time (Multi-signal cross-paper gap detection)
"""

import os
import sys
import time
import json
import statistics
import platform
import ctypes
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import torch
import fitz
import faiss
import sentence_transformers
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.session import SessionLocal, init_db, engine
from app.models.paper_model import ResearchPaper
from app.services.pdf_service import PDFService
from app.services.metadata_extractor import MetadataExtractor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.semantic_index_service import SemanticIndexService
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.research_gap_service import ResearchGapService


def get_hardware_environment():
    kernel32 = ctypes.windll.kernel32
    c_ulonglong = ctypes.c_ulonglong
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ('dwLength', ctypes.c_ulong),
            ('dwMemoryLoad', ctypes.c_ulong),
            ('ullTotalPhys', c_ulonglong),
            ('ullAvailPhys', c_ulonglong),
            ('ullTotalPageFile', c_ulonglong),
            ('ullAvailPageFile', c_ulonglong),
            ('ullTotalVirtual', c_ulonglong),
            ('ullAvailVirtual', c_ulonglong),
            ('sullAvailExtendedVirtual', c_ulonglong),
        ]
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

    # CPU name via PowerShell or processor string
    cpu_name = platform.processor()
    try:
        import subprocess
        p = subprocess.run(['powershell', '-Command', '(Get-CimInstance Win32_Processor).Name'], capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and p.stdout.strip():
            cpu_name = p.stdout.strip()
    except Exception:
        pass

    return {
        "os": f"{platform.system()} {platform.release()} (Build {platform.version()})",
        "cpu": cpu_name,
        "logical_cores": os.cpu_count(),
        "total_ram_gb": round(stat.ullTotalPhys / (1024**3), 2),
        "available_ram_gb": round(stat.ullAvailPhys / (1024**3), 2),
        "python_version": sys.version.split()[0],
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device": "CPU" if not torch.cuda.is_available() else torch.cuda.get_device_name(0),
        "sentence_transformers_version": sentence_transformers.__version__,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimension": 384,
        "pymupdf_version": fitz.__version__,
        "faiss_version": faiss.__version__,
        "database": "SQLite (Local File DB)"
    }


def benchmark_paper_processing(pdf_files, repetitions=3):
    print("\n" + "="*80)
    print("1. BENCHMARKING PAPER PROCESSING & CONCEPT EXTRACTION")
    print("="*80)
    
    results = []

    for pdf_path in pdf_files:
        filename = pdf_path.name
        file_size_bytes = pdf_path.stat().st_size
        file_size_kb = round(file_size_bytes / 1024, 2)
        
        # Open PDF to get page count
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()

        print(f"\nEvaluating: {filename}")
        print(f"  Size: {file_size_kb} KB ({file_size_bytes} bytes) | Pages: {page_count}")

        runs = []
        last_extracted_data = None
        last_metadata = None

        for r in range(repetitions):
            # Stage 1: PDF Extraction
            t0 = time.perf_counter()
            extracted_data = PDFService.extract_metadata_and_text(pdf_path, filename)
            t1 = time.perf_counter()
            pdf_extract_time_ms = (t1 - t0) * 1000.0

            # Stage 2: Concept and Metadata Extraction
            t2 = time.perf_counter()
            metadata = MetadataExtractor.extract(
                title=extracted_data["title"],
                abstract=extracted_data["abstract"],
                full_text=extracted_data["full_text"]
            )
            t3 = time.perf_counter()
            concept_extract_time_ms = (t3 - t2) * 1000.0

            total_time_ms = pdf_extract_time_ms + concept_extract_time_ms

            runs.append({
                "run": r + 1,
                "pdf_extract_time_ms": round(pdf_extract_time_ms, 2),
                "concept_extract_time_ms": round(concept_extract_time_ms, 2),
                "total_processing_time_ms": round(total_time_ms, 2)
            })
            print(f"  Run {r+1}: PDF Extraction = {pdf_extract_time_ms:.2f} ms | Concepts Extraction = {concept_extract_time_ms:.2f} ms | Total = {total_time_ms:.2f} ms")
            last_extracted_data = extracted_data
            last_metadata = metadata

        total_times = [run["total_processing_time_ms"] for run in runs]
        pdf_times = [run["pdf_extract_time_ms"] for run in runs]
        concept_times = [run["concept_extract_time_ms"] for run in runs]

        summary = {
            "filename": filename,
            "file_size_kb": file_size_kb,
            "page_count": page_count,
            "text_length_chars": len(last_extracted_data["full_text"]) if last_extracted_data else 0,
            "extracted_title": last_extracted_data["title"] if last_extracted_data else "",
            "extracted_abstract_len": len(last_extracted_data["abstract"] or "") if last_extracted_data else 0,
            "extracted_counts": {
                "keywords": len(last_metadata.get("keywords", [])),
                "algorithms": len(last_metadata.get("algorithms", [])),
                "datasets": len(last_metadata.get("datasets", [])),
                "methodologies": len(last_metadata.get("methodologies", [])),
                "application_domains": len(last_metadata.get("application_domains", []))
            },
            "runs": runs,
            "metrics": {
                "pdf_extract_mean_ms": round(statistics.mean(pdf_times), 2),
                "concept_extract_mean_ms": round(statistics.mean(concept_times), 2),
                "total_mean_ms": round(statistics.mean(total_times), 2),
                "total_std_ms": round(statistics.stdev(total_times), 2) if len(total_times) > 1 else 0.0,
                "total_min_ms": round(min(total_times), 2),
                "total_max_ms": round(max(total_times), 2)
            }
        }
        results.append(summary)

    return results


def benchmark_model_loading_and_semantic_search(db_session, sample_queries, repetitions=5):
    print("\n" + "="*80)
    print("2. BENCHMARKING AI MODEL LOADING & FAISS SEMANTIC SEARCH")
    print("="*80)

    # 1. Cold Model Loading
    print("Testing Cold AI Model Load Time (Sentence-BERT all-MiniLM-L6-v2)...")
    EmbeddingService._model = None
    EmbeddingService._cache.clear()

    t_start_cold = time.perf_counter()
    EmbeddingService.get_model()
    t_end_cold = time.perf_counter()
    cold_load_time_ms = (t_end_cold - t_start_cold) * 1000.0
    print(f"  Cold Model Loading Time: {cold_load_time_ms:.2f} ms ({cold_load_time_ms/1000.0:.3f} s)")

    # 2. Vector Store Setup & Indexing from DB
    print("\nRebuilding FAISS Index from current database records...")
    semantic_service = SemanticIndexService()
    db_papers = db_session.query(ResearchPaper).all()
    t_idx_start = time.perf_counter()
    rebuild_stats = semantic_service.rebuild_index(papers=db_papers)
    t_idx_end = time.perf_counter()
    index_build_time_ms = (t_idx_end - t_idx_start) * 1000.0
    total_indexed = semantic_service.vector_store.index.ntotal
    print(f"  Index Rebuilt: {total_indexed} papers indexed in {index_build_time_ms:.2f} ms")

    # 3. Semantic Search Latency Benchmark
    query_benchmarks = []
    
    for query in sample_queries:
        print(f"\nQuery: '{query}'")
        runs = []
        
        # Warmup query embedding cache check: We test raw embedding generation vs cached/indexed search
        for r in range(repetitions):
            # Test stage A: Embedding generation
            # Bypass cache for measurement
            if query in EmbeddingService._cache:
                del EmbeddingService._cache[query]

            t0 = time.perf_counter()
            q_emb = EmbeddingService.generate_embedding(query)
            t1 = time.perf_counter()
            emb_gen_time_ms = (t1 - t0) * 1000.0

            # Test stage B: FAISS vector search only
            t2 = time.perf_counter()
            raw_hits = semantic_service.vector_store.search(q_emb, top_k=3)
            t3 = time.perf_counter()
            faiss_search_time_ms = (t3 - t2) * 1000.0

            # Test stage C: Full End-to-End Search (Service method with DB hydration)
            t4 = time.perf_counter()
            e2e_res = semantic_service.search_papers(query=query, top_k=3, db_session=db_session)
            t5 = time.perf_counter()
            e2e_search_time_ms = (t5 - t4) * 1000.0

            runs.append({
                "run": r + 1,
                "embedding_gen_ms": round(emb_gen_time_ms, 3),
                "faiss_search_only_ms": round(faiss_search_time_ms, 3),
                "e2e_search_ms": round(e2e_search_time_ms, 3),
                "results_returned": len(e2e_res.get("results", []))
            })
            print(f"  Run {r+1}: Embedding Gen = {emb_gen_time_ms:.3f} ms | FAISS Vector Search = {faiss_search_time_ms:.3f} ms | E2E = {e2e_search_time_ms:.3f} ms")

        e2e_times = [r["e2e_search_ms"] for r in runs]
        emb_times = [r["embedding_gen_ms"] for r in runs]
        faiss_times = [r["faiss_search_only_ms"] for r in runs]

        query_benchmarks.append({
            "query": query,
            "top_k": 3,
            "runs": runs,
            "metrics": {
                "embedding_gen_mean_ms": round(statistics.mean(emb_times), 3),
                "faiss_search_mean_ms": round(statistics.mean(faiss_times), 3),
                "e2e_search_mean_ms": round(statistics.mean(e2e_times), 3),
                "e2e_search_std_ms": round(statistics.stdev(e2e_times), 3) if len(e2e_times) > 1 else 0.0,
                "e2e_search_min_ms": round(min(e2e_times), 3),
                "e2e_search_max_ms": round(max(e2e_times), 3)
            }
        })

    # Overall semantic search summary across all queries
    all_e2e_means = [q["metrics"]["e2e_search_mean_ms"] for q in query_benchmarks]
    all_faiss_means = [q["metrics"]["faiss_search_mean_ms"] for q in query_benchmarks]
    all_emb_means = [q["metrics"]["embedding_gen_mean_ms"] for q in query_benchmarks]

    return {
        "cold_model_load_ms": round(cold_load_time_ms, 2),
        "cold_model_load_s": round(cold_load_time_ms / 1000.0, 3),
        "index_build_time_ms": round(index_build_time_ms, 2),
        "total_papers_indexed": total_indexed,
        "sample_queries": query_benchmarks,
        "aggregate_metrics": {
            "overall_e2e_search_mean_ms": round(statistics.mean(all_e2e_means), 3),
            "overall_faiss_search_mean_ms": round(statistics.mean(all_faiss_means), 3),
            "overall_emb_gen_mean_ms": round(statistics.mean(all_emb_means), 3)
        }
    }


def benchmark_knowledge_graph_construction(db_session, repetitions=5):
    print("\n" + "="*80)
    print("3. BENCHMARKING KNOWLEDGE GRAPH CONSTRUCTION")
    print("="*80)

    kg_builder = KnowledgeGraphBuilder()
    runs = []
    last_res = None

    for r in range(repetitions):
        # Clear graph to ensure from-scratch construction
        kg_builder.graph_service.clear_graph()

        t0 = time.perf_counter()
        res = kg_builder.build_from_database(db_session)
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000.0

        runs.append({
            "run": r + 1,
            "duration_ms": round(dur_ms, 2),
            "total_papers": res["total_papers"],
            "total_nodes": res["total_nodes"],
            "total_edges": res["total_edges"]
        })
        print(f"  Run {r+1}: Constructed KG in {dur_ms:.2f} ms ({res['total_nodes']} nodes, {res['total_edges']} edges, {res['total_papers']} papers)")
        last_res = res

    durations = [r["duration_ms"] for r in runs]

    return {
        "total_papers": last_res["total_papers"] if last_res else 0,
        "total_nodes": last_res["total_nodes"] if last_res else 0,
        "total_edges": last_res["total_edges"] if last_res else 0,
        "node_breakdown": last_res.get("node_breakdown", {}) if last_res else {},
        "edge_breakdown": last_res.get("edge_breakdown", {}) if last_res else {},
        "top_entities": last_res.get("top_entities", {}) if last_res else {},
        "runs": runs,
        "metrics": {
            "mean_ms": round(statistics.mean(durations), 2),
            "std_ms": round(statistics.stdev(durations), 2) if len(durations) > 1 else 0.0,
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2)
        }
    }


def benchmark_research_gap_analysis(db_session, repetitions=5, top_k=10):
    print("\n" + "="*80)
    print("4. BENCHMARKING RESEARCH GAP ANALYSIS")
    print("="*80)

    gap_service = ResearchGapService()
    runs = []
    last_gaps = None

    for r in range(repetitions):
        t0 = time.perf_counter()
        gaps = gap_service.detect_gaps(db_session=db_session, top_k=top_k)
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000.0

        runs.append({
            "run": r + 1,
            "duration_ms": round(dur_ms, 2),
            "gaps_found": len(gaps)
        })
        print(f"  Run {r+1}: Gap analysis completed in {dur_ms:.2f} ms ({len(gaps)} potential gaps detected)")
        last_gaps = gaps

    durations = [r["duration_ms"] for r in runs]

    sample_detected_gaps = []
    if last_gaps:
        for g in last_gaps[:5]:
            sample_detected_gaps.append({
                "title": g.get("title") or g.get("direction_title") or f"{g.get('concept_a')} + {g.get('concept_b')}",
                "gap_score": g.get("gap_score") or g.get("overall_score") or g.get("confidence_score"),
                "concept_a": g.get("concept_a"),
                "concept_b": g.get("concept_b"),
                "category": g.get("category") or g.get("gap_type")
            })

    return {
        "top_k_requested": top_k,
        "total_gaps_detected": len(last_gaps) if last_gaps else 0,
        "sample_gaps": sample_detected_gaps,
        "runs": runs,
        "metrics": {
            "mean_ms": round(statistics.mean(durations), 2),
            "std_ms": round(statistics.stdev(durations), 2) if len(durations) > 1 else 0.0,
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2)
        }
    }


def main():
    print("="*80)
    print("INTELLIRESEARCH PERFORMANCE BENCHMARK SUITE")
    print("="*80)

    # Database session setup
    init_db()
    db = SessionLocal()

    # Hardware & Environment
    env = get_hardware_environment()
    print("\n--- ENVIRONMENT & HARDWARE CONFIGURATION ---")
    for k, v in env.items():
        print(f"  {k:30}: {v}")

    # 1. Paper Processing
    papers_dir = settings.ORIGINAL_PAPERS_DIR
    pdf_files = sorted(list(papers_dir.glob("*.pdf")))
    if not pdf_files:
        print(f"ERROR: No PDF files found in {papers_dir}")
        return

    paper_proc_results = benchmark_paper_processing(pdf_files, repetitions=3)

    # 2. Semantic Search
    sample_queries = [
        "YOLO object detection for plant disease",
        "Swin Transformer axial attention agriculture",
        "Deep learning classification explainable artificial intelligence LIME",
        "PlantDoc and PlantVillage dataset benchmarks",
        "Real-time crop leaf disease identification"
    ]
    search_results = benchmark_model_loading_and_semantic_search(db, sample_queries, repetitions=5)

    # 3. Knowledge Graph
    kg_results = benchmark_knowledge_graph_construction(db, repetitions=5)

    # 4. Research Gap Analysis
    gap_results = benchmark_research_gap_analysis(db, repetitions=5, top_k=10)

    # Compile Final Benchmark Summary
    benchmark_data = {
        "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": env,
        "paper_processing": paper_proc_results,
        "semantic_search": search_results,
        "knowledge_graph": kg_results,
        "research_gap_analysis": gap_results
    }

    # Save to JSON
    json_path = backend_dir / "scratch" / "benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"\n[OK] Raw benchmark results successfully written to: {json_path}")

    # Generate PPT Slide Table Output
    print("\n" + "="*80)
    print("SUMMARY RESULTS TABLE (SUITABLE FOR POWERPOINT SLIDE)")
    print("="*80)
    print(f"{'Metric / Component':<38} | {'Mean Time':<12} | {'Min Time':<10} | {'Max Time':<10} | {'Notes / Scope'}")
    print("-" * 105)
    
    # Paper Processing entries
    for p in paper_proc_results:
        short_name = p['filename'][:28] + '...' if len(p['filename']) > 31 else p['filename']
        print(f"Paper Processing ({short_name:<18}) | {p['metrics']['total_mean_ms']:>8.1f} ms | {p['metrics']['total_min_ms']:>6.1f} ms | {p['metrics']['total_max_ms']:>6.1f} ms | {p['file_size_kb']} KB, {p['page_count']} pages")

    # Cold Model Load
    print(f"Cold SBERT Model Load (CPU)           | {search_results['cold_model_load_ms']:>8.1f} ms | {search_results['cold_model_load_ms']:>6.1f} ms | {search_results['cold_model_load_ms']:>6.1f} ms | One-time lazy init (all-MiniLM-L6-v2)")

    # Semantic Search
    print(f"Semantic Search (Embedding Gen)        | {search_results['aggregate_metrics']['overall_emb_gen_mean_ms']:>8.3f} ms |        -   |        -   | 384-d normalized vector encoding")
    print(f"Semantic Search (FAISS Index Search)   | {search_results['aggregate_metrics']['overall_faiss_search_mean_ms']:>8.3f} ms |        -   |        -   | IndexFlatIP cosine similarity (3 papers)")
    print(f"Semantic Search (End-to-End Latency)   | {search_results['aggregate_metrics']['overall_e2e_search_mean_ms']:>8.3f} ms |        -   |        -   | Embedding + FAISS + DB hydration")

    # Knowledge Graph
    print(f"Knowledge Graph Construction          | {kg_results['metrics']['mean_ms']:>8.1f} ms | {kg_results['metrics']['min_ms']:>6.1f} ms | {kg_results['metrics']['max_ms']:>6.1f} ms | {kg_results['total_nodes']} nodes, {kg_results['total_edges']} edges ({kg_results['total_papers']} papers)")

    # Research Gap Analysis
    print(f"Research Gap Analysis                 | {gap_results['metrics']['mean_ms']:>8.1f} ms | {gap_results['metrics']['min_ms']:>6.1f} ms | {gap_results['metrics']['max_ms']:>6.1f} ms | {gap_results['total_gaps_detected']} gaps detected (top-{gap_results['top_k_requested']})")
    print("-" * 105)

    db.close()


if __name__ == "__main__":
    main()
