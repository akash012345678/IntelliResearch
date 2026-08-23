import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.link_prediction_service import LinkPredictionService
from app.services.knowledge_graph_service import (
    NODE_TYPE_PAPER,
    NODE_TYPE_KEYWORD,
    NODE_TYPE_ALGORITHM,
    NODE_TYPE_DATASET,
    NODE_TYPE_METHODOLOGY,
    NODE_TYPE_DOMAIN
)

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_NODE_TYPES = {
    NODE_TYPE_PAPER,
    NODE_TYPE_KEYWORD,
    NODE_TYPE_ALGORITHM,
    NODE_TYPE_DATASET,
    NODE_TYPE_METHODOLOGY,
    NODE_TYPE_DOMAIN
}


@router.get("/knowledge-graph", status_code=status.HTTP_200_OK)
def get_knowledge_graph(
    type: Optional[str] = Query(default=None, description="Optional node type filter (PAPER, KEYWORD, ALGORITHM, DATASET, METHODOLOGY, DOMAIN)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve full or filtered Knowledge Graph nodes, edges, and statistics built from Supabase PostgreSQL.
    """
    logger.info(f"Received request for Knowledge Graph with node type filter='{type}'")
    try:
        builder = KnowledgeGraphBuilder()
        graph_data = builder.build_from_database(db)
        graph = builder.graph_service.get_graph()

        # Build complete nodes list
        nodes_list = []
        for n_id, attrs in graph.nodes(data=True):
            node_item = {
                "id": n_id,
                "type": attrs.get("type", "UNKNOWN"),
                "label": attrs.get("label", n_id)
            }
            if attrs.get("paper_id") is not None:
                node_item["paper_id"] = attrs.get("paper_id")
            nodes_list.append(node_item)

        # Build complete edges list
        edges_list = [
            {
                "source": u,
                "target": v,
                "relation": attrs.get("relation", "")
            }
            for u, v, attrs in graph.edges(data=True)
        ]

        # Apply node type filtering if parameter provided
        if type and type.strip():
            filter_type = type.strip().upper()
            if filter_type not in VALID_NODE_TYPES:
                logger.warning(f"Invalid node type filter parameter '{type}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid node type '{type}'. Allowed types: {', '.join(sorted(VALID_NODE_TYPES))}"
                )

            # Keep nodes matching filter_type OR PAPER
            allowed_node_ids = set()
            filtered_nodes = []
            for node in nodes_list:
                if node["type"] == filter_type or node["type"] == NODE_TYPE_PAPER:
                    filtered_nodes.append(node)
                    allowed_node_ids.add(node["id"])

            # Filter edges connecting remaining nodes
            filtered_edges = [
                edge for edge in edges_list
                if edge["source"] in allowed_node_ids and edge["target"] in allowed_node_ids
            ]

            nodes_list = filtered_nodes
            edges_list = filtered_edges

        # Extract base statistics
        stats = {
            "total_nodes": graph_data.get("total_nodes", 0),
            "total_edges": graph_data.get("total_edges", 0),
            "paper_nodes": graph_data.get("paper_nodes", 0),
            "keyword_nodes": graph_data.get("keyword_nodes", 0),
            "algorithm_nodes": graph_data.get("algorithm_nodes", 0),
            "dataset_nodes": graph_data.get("dataset_nodes", 0),
            "methodology_nodes": graph_data.get("methodology_nodes", 0),
            "domain_nodes": graph_data.get("domain_nodes", 0)
        }

        return {
            "statistics": stats,
            "nodes": nodes_list,
            "edges": edges_list
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process Knowledge Graph request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the Knowledge Graph."
        )


@router.get("/knowledge-graph/statistics", status_code=status.HTTP_200_OK)
def get_knowledge_graph_statistics(
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Retrieve dynamic Knowledge Graph statistics calculated from NetworkX graph.
    """
    logger.info("Received request for Knowledge Graph statistics")
    try:
        builder = KnowledgeGraphBuilder()
        graph_data = builder.build_from_database(db)

        return {
            "total_nodes": graph_data.get("total_nodes", 0),
            "total_edges": graph_data.get("total_edges", 0),
            "paper_nodes": graph_data.get("paper_nodes", 0),
            "keyword_nodes": graph_data.get("keyword_nodes", 0),
            "algorithm_nodes": graph_data.get("algorithm_nodes", 0),
            "dataset_nodes": graph_data.get("dataset_nodes", 0),
            "methodology_nodes": graph_data.get("methodology_nodes", 0),
            "domain_nodes": graph_data.get("domain_nodes", 0)
        }
    except Exception as e:
        logger.error(f"Failed to fetch Knowledge Graph statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching Knowledge Graph statistics."
        )


@router.get("/knowledge-graph/top-entities", status_code=status.HTTP_200_OK)
def get_top_graph_entities(
    top_k: int = Query(default=5, ge=1, le=20, description="Number of top entities to return per category"),
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve the most connected research entities ordered by actual NetworkX in-degree connectivity.
    """
    logger.info(f"Received request for top Knowledge Graph entities with top_k={top_k}")
    try:
        builder = KnowledgeGraphBuilder()
        builder.build_from_database(db)
        top_entities = builder.get_top_entities(top_k=top_k)

        # Standardize field key names (name & paper_count)
        formatted_results = {}
        mapping = {
            "top_algorithms": "algorithms",
            "top_datasets": "datasets",
            "top_methodologies": "methodologies",
            "top_domains": "domains",
            "top_keywords": "keywords"
        }

        for orig_key, new_key in mapping.items():
            items = top_entities.get(orig_key, [])
            formatted_results[new_key] = [
                {
                    "name": item["label"],
                    "paper_count": item["paper_count"]
                }
                for item in items
            ]

        return formatted_results
    except ValueError as ve:
        logger.warning(f"Top entities parameter validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to fetch top Knowledge Graph entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching top Knowledge Graph entities."
        )


@router.get("/knowledge-graph/link-predictions", status_code=status.HTTP_200_OK)
def get_link_predictions(
    top_k: int = Query(default=10, ge=1, le=50, description="Number of top link predictions to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate graph-based link predictions for potential paper-concept relationships.
    """
    logger.info(f"Received request for graph link predictions with top_k={top_k}")
    try:
        builder = KnowledgeGraphBuilder()
        builder.build_from_database(db)

        prediction_service = LinkPredictionService(graph_service=builder.graph_service)
        predictions = prediction_service.predict_links(top_k=top_k)

        return {
            "total_candidates": len(predictions),
            "predictions": predictions
        }
    except Exception as e:
        logger.error(f"Failed to generate Knowledge Graph link predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating Knowledge Graph link predictions."
        )

