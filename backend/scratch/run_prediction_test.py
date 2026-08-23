import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.link_prediction_service import LinkPredictionService

def main():
    db = SessionLocal()
    builder = KnowledgeGraphBuilder()
    builder.build_from_database(db)
    db.close()

    pred_service = LinkPredictionService(graph_service=builder.graph_service)
    predictions = pred_service.predict_links(top_k=10)

    print(f"=== Real Supabase Link Prediction Results (Top {len(predictions)}) ===")
    for idx, p in enumerate(predictions, 1):
        print(f"\n#{idx}: Paper ID {p['source_paper_id']} -> {p['target_label']} ({p['target_type']})")
        print(f"    Relationship Type: {p['relationship_type']}")
        print(f"    Jaccard: {p['scores']['jaccard']}")
        print(f"    Adamic-Adar: {p['scores']['adamic_adar']}")
        print(f"    Resource Allocation: {p['scores']['resource_allocation']}")
        print(f"    Combined Score: {p['scores']['combined']}")

if __name__ == "__main__":
    main()
