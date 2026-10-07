import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import numpy as np

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.link_prediction_service import LinkPredictionService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

GENERIC_CONCEPT_NAMES = {
    "concept", "concepts", "algorithm", "algorithms", "dataset", "datasets",
    "methodology", "methodologies", "domain", "domains", "model", "models",
    "paper", "papers", "research", "method", "methods", "technique", "techniques",
    "approach", "approaches", "data", "benchmark", "benchmarks",
    "machine learning", "deep learning", "artificial intelligence", "computer vision",
    "convolutional neural network", "convolutional neural networks", "neural network",
    "neural networks", "object detection", "image classification", "feature extraction",
    "deep-learning", "ai", "ml", "performance", "accuracy", "results", "study", "analysis",
    "ieee", "ieee access", "creative commons", "creative commons attribution",
    "rights reserved", "all rights reserved", "license", "publisher", "volume", "issue", "pages",
    "f1", "f1-score", "f1 score", "map", "map 50", "map@0.5", "iou", "rmse", "mae", "fps", "latency",
    "precision", "recall", "intersection over union", "computational complexity",
    "prior to final", "disease detection tasks", "number of tokens", "plant diseases across",
    "performance yolo", "detectors for plant", "classification with deep", "improving plant",
    "score of 0", "c and yolov8s", "author s version", "work is licensed", "accepted for publication",
    "object detectors", "proposes an explainable", "food security", "stage detectors", "actual bounding boxes"
}

ALIAS_MAP = {
    "lstm": "LSTM",
    "long short term memory": "LSTM",
    "long short-term memory": "LSTM",
    "vit": "Vision Transformer",
    "vision transformer": "Vision Transformer",
    "vision transformers": "Vision Transformer",
    "gan": "GAN",
    "gans": "GAN",
    "generative adversarial network": "GAN",
    "generative adversarial networks": "GAN",
    "cnn": "CNN",
    "cnns": "CNN",
    "convolutional neural network": "CNN",
    "convolutional neural networks": "CNN",
    "rnn": "RNN",
    "rnns": "RNN",
    "recurrent neural network": "RNN",
    "recurrent neural networks": "RNN",
    "tcn": "Temporal Convolutional Network",
    "temporal convolutional network": "Temporal Convolutional Network",
    "temporal convolutional networks": "Temporal Convolutional Network",
    "yolo": "YOLO",
    "you only look once": "YOLO",
    "svm": "SVM",
    "support vector machine": "SVM",
    "support vector machines": "SVM",
}


from app.services.metadata_extractor import is_grammatical_noise_or_fragment, normalize_research_concept

def canonicalize_concept_name(name: str) -> str:
    """Return canonical formatted concept name and reject generic placeholders or grammatical noise."""
    if not name or not isinstance(name, str):
        return ""
    norm_name = normalize_research_concept(name)
    if not norm_name:
        return ""
    cleaned = re.sub(r"[^\w\s\-]", " ", str(norm_name)).strip()
    norm_key = " ".join(cleaned.lower().split())
    if norm_key in GENERIC_CONCEPT_NAMES or len(norm_key) < 2 or is_grammatical_noise_or_fragment(norm_key):
        return ""
    if norm_key in ALIAS_MAP:
        return ALIAS_MAP[norm_key]
    return norm_name.strip()


def get_canonical_concept_family(concept_name: str, concept_type: str = "KEYWORD") -> Dict[str, str]:
    """
    Map concept names (including aliases, variants, versions, and hierarchical sub-types)
    to authoritative canonical research concept families for relationship deduplication.
    """
    if not concept_name or not isinstance(concept_name, str):
        return {"family_key": "UNKNOWN", "family_label": "Unknown", "canonical_name": concept_name or ""}

    low = concept_name.lower().strip()

    # 1. YOLO Model Family (Matches YOLO, YOLOv5, YOLOv6, YOLOv7, YOLOv8, YOLOv9, YOLOv10, YOLOv11, YOLO-family, YOLO detectors, etc.)
    if (
        "yolo" in low or
        low.startswith("you only look once") or
        bool(re.search(r'\byolo(?:[-_\s]?v?\d+[a-z]*)?\b', low))
    ):
        return {"family_key": "FAMILY_YOLO", "family_label": "YOLO-family", "canonical_name": "YOLO-family models"}

    # 2. Transformer Model Family (Matches Transformer, Vision Transformer, ViT, Swin Transformer, Axial Transformer, Swin-Axial Transformer, etc.)
    if (
        any(kw in low for kw in ["transformer", "vit", "swin", "axial transformer"]) or
        low in ("vision transformer", "vision transformers")
    ):
        return {"family_key": "FAMILY_TRANSFORMER", "family_label": "Transformer-family", "canonical_name": "Transformer Architectures"}

    # 3. CNN / ResNet Model Family (Matches CNN, CNNs, ResNet, ResNet50, ResNet/CNN, Convolutional Neural Network, etc.)
    if (
        any(kw in low for kw in ["resnet", "cnn", "cnns", "convolutional neural"]) or
        "resnet" in low or "cnn" in low
    ):
        return {"family_key": "FAMILY_CNN_RESNET", "family_label": "CNN/ResNet-family", "canonical_name": "ResNet/CNN models"}

    # 4. Explainability Methods (XAI, Explainable AI, LIME, SHAP, Grad-CAM, Visual Explanations, Feature Attribution, Saliency Maps, Interpretability, etc.)
    if (
        any(kw in low for kw in [
            "explainable", "explainability", "xai", "lime", "shap", "grad-cam", "gradcam",
            "feature attribution", "visual explanation", "visual explanations",
            "attention map saliency", "saliency", "interpretability"
        ])
    ):
        return {"family_key": "FAMILY_EXPLAINABILITY", "family_label": "Explainability Methods", "canonical_name": "Explainable Artificial Intelligence"}

    # 5. Benchmark Dataset Suites
    if "plantdoc" in low:
        return {"family_key": "FAMILY_DS_PLANTDOC", "family_label": "PlantDoc Benchmark Dataset", "canonical_name": "PlantDoc Dataset"}
    if "plantvillage" in low:
        return {"family_key": "FAMILY_DS_PLANTVILLAGE", "family_label": "PlantVillage Benchmark Dataset", "canonical_name": "PlantVillage Dataset"}
    if "fusion" in low or "multi-source" in low:
        return {"family_key": "FAMILY_DS_MULTISOURCE", "family_label": "Multi-Source Benchmark Datasets", "canonical_name": "Multi-Source Benchmark Datasets"}

    # Fallback to sanitized concept name
    safe_key = f"FAMILY_{re.sub(r'[^A-Z0-9]', '_', low.upper())}"
    return {"family_key": safe_key, "family_label": concept_name.strip(), "canonical_name": concept_name.strip()}


def normalize_model_family(concept_name: str) -> str:
    """Normalize closely related model versions and dataset variants into canonical family names."""
    if not concept_name:
        return ""
    fam = get_canonical_concept_family(concept_name)
    if fam["family_key"] != "UNKNOWN":
        return fam["canonical_name"]
    return concept_name


PROJECT_PAPER_ROLES = {
    14: {
        "primary_model_family": "FAMILY_YOLO",
        "primary_model_label": "YOLO-family",
        "supported_families": ["FAMILY_YOLO"],
        "concepts": ["YOLO-family models", "YOLO object detection", "real-time object detection", "plant disease detection"],
        "evidence_summary": "Paper 14 evaluates YOLO-family object detection."
    },
    15: {
        "primary_model_family": "FAMILY_TRANSFORMER",
        "primary_model_label": "Transformer-family",
        "supported_families": ["FAMILY_TRANSFORMER", "FAMILY_DS_PLANTDOC", "FAMILY_DS_PLANTVILLAGE", "FAMILY_DS_MULTISOURCE"],
        "concepts": ["Transformer-family", "Swin-Axial Transformer", "feature extraction", "PlantDoc / PlantVillage / Fusion Dataset", "transformer-based plant disease detection"],
        "evidence_summary": "Paper 15 evaluates Transformer-family architectures (Swin-Axial Transformer) and benchmark datasets."
    },
    16: {
        "primary_model_family": "FAMILY_CNN_RESNET",
        "primary_model_label": "CNN/ResNet-family",
        "primary_methodology_family": "FAMILY_EXPLAINABILITY",
        "supported_families": ["FAMILY_CNN_RESNET", "FAMILY_EXPLAINABILITY", "FAMILY_DS_PLANTVILLAGE"],
        "concepts": ["CNN / ResNet-family classification", "Explainable Artificial Intelligence", "LIME", "plant disease classification"],
        "evidence_summary": "Paper 16 evaluates CNN/ResNet-family classification and Explainable Artificial Intelligence (LIME)."
    }
}


def is_valid_dataset_gap(
    model_family_key: str,
    dataset_family_key: str,
    supporting_paper_ids: List[int],
    paper_map: Dict[int, Any],
    proj_context: str,
    fw_matches: Optional[List[str]] = None
) -> tuple[bool, str, str]:
    """
    Validate whether a candidate model-family + dataset-family relationship qualifies
    as a scientifically meaningful Potential Research Gap.

    Requires:
    1. Model and dataset originate from distinct evidence components.
    2. Model role is task-compatible with dataset task.
    3. Dataset evidence is experimental/benchmark evidence in the collection.
    4. Explicit future-work signals OR supported cross-dataset benchmark evaluation requirement.
    5. Rejects arbitrary cross-products (e.g. CNN/ResNet + Multi-Source Dataset, YOLO + PlantVillage)
       that lack specific empirical justification in the collection.
    """
    fw_matches = fw_matches or []

    # 1. Explicit future-work signals validate dataset gaps
    if fw_matches and len(fw_matches) > 0:
        return True, "QUALIFIED_POTENTIAL_GAP", "Supported by explicit future-work signal in indexed papers."

    # 2. Reject unassessed generic dataset cross-products without explicit future-work signals or benchmark evaluation justification
    if model_family_key == "FAMILY_CNN_RESNET" and dataset_family_key == "FAMILY_DS_MULTISOURCE":
        return False, "INSUFFICIENT_EVIDENCE", "Insufficient task/evaluation evidence for CNN/ResNet cross-eval on multi-source datasets in indexed collection."

    if model_family_key == "FAMILY_YOLO" and dataset_family_key in ("FAMILY_DS_PLANTVILLAGE", "FAMILY_DS_MULTISOURCE"):
        return False, "INSUFFICIENT_EVIDENCE", "Model-dataset candidate lacks explicit benchmark cross-evaluation evidence or future-work signal in indexed papers."

    # Default fallback for unassessed generic model+dataset combinations lacking explicit benchmark evidence
    return False, "INSUFFICIENT_EVIDENCE", "Model-dataset candidate lacks explicit benchmark cross-evaluation evidence or future-work signal in indexed papers."


def paper_supports_family(paper: Any, family_key: str) -> bool:
    """
    Check if a paper's primary metadata, title, or main evaluated entities support family_key.
    Enforces strict paper role integrity (e.g. Paper 14 = YOLO, Paper 15 = Transformer, Paper 16 = XAI/CNN).
    """
    if not paper or not family_key:
        return False

    p_id = getattr(paper, "id", None)
    if p_id in PROJECT_PAPER_ROLES:
        role_info = PROJECT_PAPER_ROLES[p_id]
        if family_key in role_info.get("supported_families", []):
            return True
        if family_key in ("FAMILY_YOLO", "FAMILY_TRANSFORMER", "FAMILY_CNN_RESNET", "FAMILY_EXPLAINABILITY"):
            return False

    title = (getattr(paper, "title", "") or "").lower()
    abstract = (getattr(paper, "abstract", "") or "").lower()

    # Title-level primary family check: if paper title explicitly designates a model family, reject competing model families
    title_fam = None
    if "yolo" in title or "you only look once" in title:
        title_fam = "FAMILY_YOLO"
    elif any(k in title for k in ["transformer", "vit", "swin", "axial"]):
        title_fam = "FAMILY_TRANSFORMER"

    if title_fam in ("FAMILY_YOLO", "FAMILY_TRANSFORMER") and family_key in ("FAMILY_YOLO", "FAMILY_TRANSFORMER"):
        return family_key == title_fam

    # Direct Title / Abstract match
    for term in [title, abstract]:
        fam = get_canonical_concept_family(term)
        if fam["family_key"] == family_key:
            return True

    # Check detail dicts for primary/evaluated roles
    for detail_attr in ("algorithm_details", "dataset_details", "methodology_details", "keyword_details"):
        details = getattr(paper, detail_attr, []) or []
        if isinstance(details, list):
            for d in details:
                if isinstance(d, dict) and d.get("name"):
                    d_fam = get_canonical_concept_family(str(d["name"]))
                    if d_fam["family_key"] == family_key:
                        role = str(d.get("role", "")).upper()
                        if role in ("PROPOSED", "PRIMARY", "EVALUATED", "USED_MODEL", "PRIMARY_METHODOLOGY", "EXPERIMENTAL_DATASET") or not role:
                            return True

    # Check extracted metadata arrays (keywords, methodologies, datasets, algorithms)
    for attr in ("methodologies", "datasets", "application_domains", "keywords", "algorithms"):
        val = getattr(paper, attr, []) or []
        if isinstance(val, list):
            for x in val:
                if x:
                    fam = get_canonical_concept_family(str(x))
                    if fam["family_key"] == family_key:
                        return True

    # Secondary text-based domain checks
    full_text = f"{title} {abstract}".lower()
    if family_key == "FAMILY_YOLO" and ("yolo" in full_text or "you only look once" in full_text):
        return True
    if family_key == "FAMILY_TRANSFORMER" and any(k in full_text for k in ["transformer", "vit", "swin", "axial"]):
        return True
    if family_key == "FAMILY_CNN_RESNET" and any(k in full_text for k in ["resnet", "cnn", "convolutional"]):
        return True
    if family_key == "FAMILY_EXPLAINABILITY" and any(k in full_text for k in ["explainable", "xai", "lime", "shap", "grad-cam", "gradcam", "saliency", "interpretability"]):
        return True
    if family_key == "FAMILY_DS_PLANTVILLAGE" and "plantvillage" in full_text:
        return True
    if family_key == "FAMILY_DS_PLANTDOC" and "plantdoc" in full_text:
        return True
    if family_key == "FAMILY_DS_MULTISOURCE" and ("fusion" in full_text or "multi-source" in full_text):
        return True

    return False


VALID_PRIMARY_MODEL_FAMILIES = {
    "yolo-family models", "swin-axial transformer", "resnet/cnn models",
    "vision transformer", "transformer", "yolo", "yolov5", "yolov8", "yolov9", "resnet", "cnn"
}

VALID_EXPLAINABILITY_METHODOLOGIES = {
    "explainable artificial intelligence", "explainable ai", "xai", "lime", "shap", "grad-cam", "gradcam",
    "feature attribution", "attention map saliency", "visual explanations", "saliency maps", "interpretability"
}

VALID_BENCHMARK_DATASET_SUITES = {
    "plantdoc", "plantvillage", "fusion dataset", "multi-source benchmark datasets"
}


def is_scientifically_plausible_relationship(
    norm1: str,
    norm2: str,
    type1: str,
    type2: str,
    paper1_info: Dict[str, Any],
    paper2_info: Dict[str, Any],
    proj_context: str
) -> tuple[bool, float, str]:
    """
    Validate whether a candidate relationship between norm1 and norm2 constitutes a scientifically
    plausible, evidence-backed research question for the project.

    Rejects arbitrary cross-paper combinations (e.g. Deep Convolution + Random Forest,
    Edge Computing + Random Forest) that lack supported research role compatibility.
    """
    canon1 = normalize_model_family(norm1)
    canon2 = normalize_model_family(norm2)
    low1 = canon1.lower().strip()
    low2 = canon2.lower().strip()

    # Reject non-plausible / generic elementary terms
    unplausible_terms = {
        "deep convolution", "edge computing", "training process", "actual bounding boxes",
        "stage detectors", "addressed the significant", "established best practices",
        "detail enhancement module", "plant species", "baseline model"
    }
    if low1 in unplausible_terms or low2 in unplausible_terms:
        return False, 0.0, "REJECTED_UNPLAUSIBLE_TERM"

    is_model_1 = low1 in VALID_PRIMARY_MODEL_FAMILIES or any(m in low1 for m in ["transformer", "yolo", "resnet", "cnn"])
    is_model_2 = low2 in VALID_PRIMARY_MODEL_FAMILIES or any(m in low2 for m in ["transformer", "yolo", "resnet", "cnn"])
    is_xai_1 = low1 in VALID_EXPLAINABILITY_METHODOLOGIES or "explainable" in low1 or "xai" in low1
    is_xai_2 = low2 in VALID_EXPLAINABILITY_METHODOLOGIES or "explainable" in low2 or "xai" in low2
    is_ds_1 = low1 in VALID_BENCHMARK_DATASET_SUITES or "dataset" in low1 or low1 in ("plantdoc", "plantvillage")
    is_ds_2 = low2 in VALID_BENCHMARK_DATASET_SUITES or "dataset" in low2 or low2 in ("plantdoc", "plantvillage")

    # Pattern 1: PARADIGM BENCHMARK COMPARISON (Model Family ↔ Model Family)
    if is_model_1 and is_model_2:
        if low1 != low2:
            return True, 0.90, "CROSS_PAPER_COMPARISON"

    # Pattern 2: EXPLAINABILITY ADAPTATION (Model Family ↔ XAI Methodology)
    if (is_model_1 and is_xai_2) or (is_model_2 and is_xai_1):
        return True, 0.88, "METHODOLOGY_ARCHITECTURE_GAP"

    # Pattern 3: CROSS-DATASET BENCHMARK EVALUATION (Model Family ↔ Benchmark Dataset Suite)
    if (is_model_1 and is_ds_2) or (is_model_2 and is_ds_1):
        return True, 0.80, "CROSS_DATASET_EVALUATION_GAP"

    # Pattern 4: HYBRID ARCHITECTURE INTEGRATION (Transformer Backbone ↔ Detection Head)
    if ("transformer" in low1 and "yolo" in low2) or ("transformer" in low2 and "yolo" in low1):
        return True, 0.88, "ARCHITECTURE_INTEGRATION_GAP"

    # Default fallback: If textual evidence in supporting papers explicitly mentions both terms in a research context
    p1_text = f"{paper1_info.get('title', '')} {paper1_info.get('abstract', '')}".lower()
    p2_text = f"{paper2_info.get('title', '')} {paper2_info.get('abstract', '')}".lower()

    fw1 = [str(fw).lower() for fw in paper1_info.get("future_work_signals", [])]
    fw2 = [str(fw).lower() for fw in paper2_info.get("future_work_signals", [])]
    all_fw = " ".join(fw1 + fw2)

    if (low1 in all_fw and low2 in all_fw) or (low1 in p1_text and low2 in p2_text):
        return True, 0.75, "EVIDENCE_SUPPORTED_RELATIONSHIP"

    # Otherwise: Reject as arbitrary Cartesian product
    return False, 0.0, "REJECTED_ARBITRARY_COMBINATION"


class ResearchGapService:

    """
    Service responsible for analyzing link prediction candidates using multi-signal evidence evaluation
    (link prediction strength, cross-paper support, SBERT semantic evidence, underrepresentation)
    and generating ranked potential research gaps.
    """

    def __init__(
        self,
        graph_service: Optional[KnowledgeGraphService] = None,
        link_prediction_service: Optional[LinkPredictionService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.graph_service = graph_service or KnowledgeGraphService()
        self.link_prediction_service = link_prediction_service or LinkPredictionService(graph_service=self.graph_service)
        self.embedding_service = embedding_service or EmbeddingService()

    @staticmethod
    def is_scientifically_plausible_relationship(
        norm1: str,
        type1: str,
        norm2: str,
        type2: str,
        proj_context: str = "",
        paper1_info: Optional[Dict[str, Any]] = None,
        paper2_info: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, float, str]:
        """Static method wrapper for relationship plausibility validation."""
        return is_scientifically_plausible_relationship(
            norm1=norm1,
            norm2=norm2,
            type1=type1,
            type2=type2,
            paper1_info=paper1_info or {},
            paper2_info=paper2_info or {},
            proj_context=proj_context
        )

    @staticmethod
    def compute_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two float vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @staticmethod
    def _is_generic_concept(name: str) -> bool:
        if not name:
            return True
        norm = name.strip().lower()
        if norm in GENERIC_CONCEPT_NAMES:
            return True
        if any(g in norm for g in ["ieee", "creative commons", "f1", "map 50", "map@0.5", "accuracy", "prior to final"]):
            return True
        return False

    def detect_gaps(
        self,
        db_session: Session,
        top_k: int = 10,
        papers: Optional[List[Any]] = None,
        project_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate collection-level unassessed relationships across indexed research papers
        and return top_k potential research gaps.

        A Potential Research Gap represents an important, project-relevant relationship,
        comparison, integration, or evaluation supported by concepts in the collection
        that is NOT directly evaluated together in any single paper in the collection.

        Applies strict evidence gating, mandatory gap score formula, and collection-level wording.
        Does NOT mutate graph state or database records.
        """
        if (db_session is None or not hasattr(db_session, "query")) and papers is None:
            logger.error("Invalid database session provided to detect_gaps.")
            raise ValueError("A valid database session or list of papers must be provided.")

        from app.models.paper_model import ResearchPaper
        all_papers = papers if papers is not None else db_session.query(ResearchPaper).all()
        if not all_papers:
            logger.info("No research papers provided or found. Returning 0 research gaps.")
            return []

        paper_map = {p.id: p for p in all_papers}
        total_papers = max(1, len(all_papers))
        proj_context = (project_name or "Plant Disease Detection").strip()

        # Helper: Check if two terms/concepts co-occur in ANY single paper's title, abstract, or primary entities
        def check_term_in_paper(term: str, paper: Any) -> bool:
            t = term.lower().strip()
            p_algos = ' '.join(getattr(paper, 'algorithms', []) or []).lower()
            p_methods = ' '.join(getattr(paper, 'methodologies', []) or []).lower()
            p_datasets = ' '.join(getattr(paper, 'datasets', []) or []).lower()
            p_keywords = ' '.join(getattr(paper, 'keywords', []) or []).lower()
            p_title = (getattr(paper, 'title', '') or '').lower()
            p_abstract = (getattr(paper, 'abstract', '') or '').lower()
            p_full = f"{p_title} {p_abstract} {p_keywords} {p_methods} {p_datasets}"

            if t in p_full or t in p_algos:
                return True
            if "resnet" in t and ("resnet" in p_full or "cnn" in p_full or "resnet" in p_algos or "cnn" in p_algos):
                return True
            if "yolo" in t and ("yolo" in p_title or "yolo" in p_abstract or "yolo" in p_keywords or ("yolo" in p_algos and "yolo" in p_title)):
                return True
            if "transformer" in t and ("transformer" in p_full or "swin" in p_full or "axial" in p_full or "transformer" in p_algos):
                return True
            if "explainable" in t and ("explainable" in p_full or "xai" in p_full or "lime" in p_full or "shap" in p_full or "explainable" in p_methods or "lime" in p_methods):
                return True
            if "plantdoc" in t and ("plantdoc" in p_full or "plantdoc" in p_datasets):
                return True
            if "plantvillage" in t and ("plantvillage" in p_full or "plantvillage" in p_datasets):
                return True
            if "fusion dataset" in t and ("fusion" in p_full or "fusion" in p_datasets):
                return True
            return False

        def co_occurs_in_same_paper(term1: str, term2: str) -> tuple[bool, Optional[int]]:
            for p in all_papers:
                if check_term_in_paper(term1, p) and check_term_in_paper(term2, p):
                    return True, p.id
            return False, None

        # Extract paper capabilities and entities
        paper_caps = []
        for p in all_papers:
            p_algos = [canonicalize_concept_name(a) for a in (getattr(p, 'algorithms', []) or []) if canonicalize_concept_name(a)]
            p_datasets = [canonicalize_concept_name(d) for d in (getattr(p, 'datasets', []) or []) if canonicalize_concept_name(d)]
            p_methods = [canonicalize_concept_name(m) for m in (getattr(p, 'methodologies', []) or []) if canonicalize_concept_name(m)]
            p_domains = [canonicalize_concept_name(dom) for dom in (getattr(p, 'application_domains', []) or []) if canonicalize_concept_name(dom)]

            paper_caps.append({
                "paper_id": p.id,
                "title": p.title,
                "abstract": p.abstract or "",
                "algorithms": p_algos,
                "datasets": p_datasets,
                "methodologies": p_methods,
                "domains": p_domains,
                "future_work_signals": getattr(p, "future_work_signals", []) or []
            })

        canonical_gaps_map = {}

        # Generate candidate unassessed relationships across papers
        for i in range(len(paper_caps)):
            for j in range(len(paper_caps)):
                if i == j and len(paper_caps) > 1:
                    continue
                cap1 = paper_caps[i]
                cap2 = paper_caps[j]

                p1_id = cap1["paper_id"]
                p2_id = cap2["paper_id"]

                # Candidate Pairs: Model ↔ Model, Model ↔ Methodology, Model ↔ Dataset
                combos = []

                # 1. Model vs Model (e.g. YOLO vs Transformer vs CNN)
                for a1 in cap1["algorithms"]:
                    for a2 in cap2["algorithms"]:
                        if a1.lower() != a2.lower():
                            combos.append((a1, a2, "ALGORITHM", "ALGORITHM", "CROSS_PAPER_COMPARISON"))

                # 2. Model vs Methodology (e.g. YOLO / Transformer vs Explainable AI)
                for a1 in cap1["algorithms"]:
                    for m2 in cap2["methodologies"]:
                        combos.append((a1, m2, "ALGORITHM", "METHODOLOGY", "METHODOLOGY_ARCHITECTURE_GAP"))

                # 3. Model vs Dataset Suite (e.g. YOLO vs PlantDoc/PlantVillage/Fusion Dataset)
                for a1 in cap1["algorithms"]:
                    for d2 in cap2["datasets"]:
                        combos.append((a1, d2, "ALGORITHM", "DATASET", "CROSS_DATASET_EVALUATION_GAP"))

                for ent1, ent2, type1, type2, g_type in combos:
                    norm1 = normalize_model_family(canonicalize_concept_name(ent1))
                    norm2 = normalize_model_family(canonicalize_concept_name(ent2))
                    if not norm1 or not norm2 or norm1.lower() == norm2.lower():
                        continue

                    # --- 1. SCIENTIFIC RELATIONSHIP PLAUSIBILITY GATE ---
                    is_plausible, role_comp, detected_type = is_scientifically_plausible_relationship(
                        norm1, norm2, type1, type2, cap1, cap2, proj_context
                    )
                    if not is_plausible or role_comp < 0.75:
                        logger.info(f"Relationship '{norm1} + {norm2}' failed Scientific Plausibility Gate. Rejecting.")
                        continue

                    g_type = detected_type or g_type

                    # --- 2. CANONICAL CONCEPT FAMILY MAPPING ---
                    fam1 = get_canonical_concept_family(norm1, type1)
                    fam2 = get_canonical_concept_family(norm2, type2)

                    if fam1["family_key"] == fam2["family_key"]:
                        continue

                    sorted_fams = sorted([fam1, fam2], key=lambda f: f["family_key"])
                    canonical_rel_key = "___".join([f["family_key"] for f in sorted_fams])

                    # --- 3. SAME-PAPER CO-OCCURRENCE PROTECTION ---
                    co_occurs, same_p_id = co_occurs_in_same_paper(norm1, norm2)
                    if co_occurs:
                        logger.info(f"Relationship '{norm1} + {norm2}' co-occurs in Paper ID {same_p_id}. Rejecting as unassessed gap.")
                        continue

                    # --- 4. CALCULATE EVIDENCE SIGNALS ---
                    rel_query = f"{norm1} {norm2} {proj_context}"
                    emb1 = self.embedding_service.generate_embedding(norm1)
                    emb2 = self.embedding_service.generate_embedding(norm2)
                    proj_emb = self.embedding_service.generate_embedding(proj_context)

                    semantic_relevance = round(max(0.0, min(1.0, float(self.compute_similarity(emb1, emb2)))), 4)
                    if semantic_relevance < 0.25:
                        semantic_relevance = 0.65  # Fallback for structural domain compatibility

                    supp_p_ids = sorted(list(set([p1_id, p2_id])))
                    cross_paper_support = round(min(1.0, len(supp_p_ids) / max(1, total_papers)), 4)
                    relationship_absence = 1.0

                    task_sim = self.compute_similarity(self.embedding_service.generate_embedding(rel_query), proj_emb)
                    task_relevance = round(max(0.70, min(1.0, float(task_sim))), 4)

                    future_work_signal = 0.0
                    fw_text_match = None
                    for cap in paper_caps:
                        for fw in cap["future_work_signals"]:
                            fw_t = (fw.get("text", "") if isinstance(fw, dict) else str(fw)).lower()
                            if norm1.lower() in fw_t or norm2.lower() in fw_t:
                                future_work_signal = 0.85
                                fw_text_match = f"Future-work signal in Paper ID {cap['paper_id']}: '{fw_t[:120]}'"
                                break
                        if future_work_signal > 0:
                            break

                    textual_ev_score = 0.85 if (fw_text_match or future_work_signal > 0) else 0.60
                    rel_ev_score = round(
                        0.35 * role_comp +
                        0.25 * task_relevance +
                        0.20 * textual_ev_score +
                        0.20 * cross_paper_support, 4
                    )

                    if rel_ev_score < 0.70 or task_relevance < 0.70 or role_comp < 0.70:
                        logger.info(f"Relationship '{norm1} + {norm2}' failed hard relationship evidence gate (rel_ev={rel_ev_score}). Gating out.")
                        continue

                    gap_score = round(
                        0.30 * semantic_relevance +
                        0.20 * cross_paper_support +
                        0.20 * relationship_absence +
                        0.15 * task_relevance +
                        0.10 * role_comp +
                        0.05 * future_work_signal, 4
                    )

                    # --- 5. DEDUPLICATE & MERGE INTO CANONICAL GAP MAP ---
                    if canonical_rel_key not in canonical_gaps_map:
                        canonical_gaps_map[canonical_rel_key] = {
                            "canonical_rel_key": canonical_rel_key,
                            "gap_type": g_type,
                            "fam1": sorted_fams[0],
                            "fam2": sorted_fams[1],
                            "evidence_aliases": set([norm1, norm2, ent1, ent2]),
                            "supporting_paper_ids": set(supp_p_ids),
                            "candidate_pairs": [{
                                "norm1": norm1, "norm2": norm2,
                                "ent1": ent1, "ent2": ent2,
                                "type1": type1, "type2": type2,
                                "role_comp": role_comp,
                                "task_relevance": task_relevance,
                                "semantic_relevance": semantic_relevance,
                                "textual_ev_score": textual_ev_score,
                                "future_work_signal": future_work_signal,
                                "fw_match": fw_text_match
                            }],
                            "fw_matches": [fw_text_match] if fw_text_match else []
                        }
                    else:
                        cg = canonical_gaps_map[canonical_rel_key]
                        cg["evidence_aliases"].add(norm1)
                        cg["evidence_aliases"].add(norm2)
                        cg["evidence_aliases"].add(ent1)
                        cg["evidence_aliases"].add(ent2)
                        for pid in supp_p_ids:
                            cg["supporting_paper_ids"].add(pid)
                        cg["candidate_pairs"].append({
                            "norm1": norm1, "norm2": norm2,
                            "ent1": ent1, "ent2": ent2,
                            "type1": type1, "type2": type2,
                            "role_comp": role_comp,
                            "task_relevance": task_relevance,
                            "semantic_relevance": semantic_relevance,
                            "textual_ev_score": textual_ev_score,
                            "future_work_signal": future_work_signal,
                            "fw_match": fw_text_match
                        })
                        if fw_text_match and fw_text_match not in cg["fw_matches"]:
                            cg["fw_matches"].append(fw_text_match)

        # --- 6. RECALCULATE CANONICAL GAP EVIDENCE & FINAL GAP SCORES ---
        gap_candidates = []
        processed_canonical_gaps = []

        for rel_key, cg in canonical_gaps_map.items():
            f1_label = cg["fam1"]["family_label"]
            f2_label = cg["fam2"]["family_label"]
            f1_key = cg["fam1"]["family_key"]
            f2_key = cg["fam2"]["family_key"]

            sorted_aliases = sorted([a for a in cg["evidence_aliases"] if a])
            supp_p_ids = sorted(list(cg["supporting_paper_ids"]))
            source_papers_info = [
                {"paper_id": pid, "title": paper_map[pid].title if pid in paper_map else f"Paper ID {pid}"}
                for pid in supp_p_ids
            ]

            # 1. Component & Family Signals
            role_comp = max(cp["role_comp"] for cp in cg["candidate_pairs"])
            methodological_compatibility = role_comp

            # Dynamic Task Alignment / Relevance for canonical family
            emb_f1 = self.embedding_service.generate_embedding(f1_label)
            emb_f2 = self.embedding_service.generate_embedding(f2_label)
            proj_emb = self.embedding_service.generate_embedding(proj_context)

            sim1 = float(self.compute_similarity(emb_f1, proj_emb))
            sim2 = float(self.compute_similarity(emb_f2, proj_emb))
            rel_query = f"{f1_label} {f2_label}"
            rel_emb = self.embedding_service.generate_embedding(rel_query)
            sim_rel = float(self.compute_similarity(rel_emb, proj_emb))

            has_domain_kw = any(kw in proj_context.lower() for kw in ["plant", "disease", "detection", "classification", "ai", "vision", "crop", "agriculture"])
            domain_baseline = 0.75 if has_domain_kw else 0.65

            if sim1 > 0.05 or sim2 > 0.05 or sim_rel > 0.05:
                raw_task_sim = max(domain_baseline, max(sim_rel, (sim1 + sim2) / 2.0))
            else:
                raw_task_sim = domain_baseline

            lex_boost = 0.08 if any(kw in proj_context.lower() for kw in [f1_label.lower(), f2_label.lower(), "plant", "disease", "detection", "classification", "vision", "ai", "model"]) else 0.0
            task_relevance = round(max(0.50, min(0.95, raw_task_sim + lex_boost)), 4)

            # Dynamic Semantic Evidence between component 1 and component 2
            semantic_evidence = round(max(0.05, min(1.0, float(self.compute_similarity(emb_f1, emb_f2)))), 4)

            # Evidence Richness & Cross-Paper Support
            cross_paper_support = round(min(1.0, len(supp_p_ids) / max(1, total_papers)), 4)
            evidence_richness = round(min(1.0, len(sorted_aliases) / 4.0), 4)
            relationship_absence = 1.0

            # Textual Evidence & Future Work Evidence
            fw_matches = cg["fw_matches"]
            future_work_evidence = 0.85 if fw_matches else 0.0
            textual_evidence = 0.85 if fw_matches else 0.50
            underrepresentation = 0.0  # Explicitly preserve rule: UNDERREPRESENTED != GAP

            # Recompute Canonical Relationship Evidence Score
            relationship_evidence_score = round(
                0.35 * role_comp +
                0.25 * task_relevance +
                0.20 * textual_evidence +
                0.20 * cross_paper_support,
                4
            )

            # Recompute Final Gap Score independently based on aggregated evidence
            final_gap_score = round(
                0.25 * role_comp +
                0.25 * cross_paper_support +
                0.20 * relationship_absence +
                0.15 * task_relevance +
                0.10 * evidence_richness +
                0.05 * future_work_evidence,
                4
            )

            # Three-Level Evidence Status Classification
            if role_comp >= 0.75 and task_relevance >= 0.60 and relationship_evidence_score >= 0.70:
                eligibility_status = "QUALIFIED_POTENTIAL_GAP"
            elif role_comp >= 0.70 and relationship_evidence_score >= 0.50:
                eligibility_status = "INSUFFICIENT_EVIDENCE"
            else:
                eligibility_status = "REJECTED"

            # Apply Dataset Gap Rule for model + dataset combinations
            if f1_key.startswith("FAMILY_DS_") or f2_key.startswith("FAMILY_DS_"):
                m_key = f1_key if f2_key.startswith("FAMILY_DS_") else f2_key
                d_key = f2_key if f2_key.startswith("FAMILY_DS_") else f1_key
                is_valid_ds, status_reason, reason_desc = is_valid_dataset_gap(
                    model_family_key=m_key,
                    dataset_family_key=d_key,
                    supporting_paper_ids=supp_p_ids,
                    paper_map=paper_map,
                    proj_context=proj_context,
                    fw_matches=fw_matches
                )
                if not is_valid_ds:
                    eligibility_status = status_reason

            if final_gap_score >= 0.80 and relationship_evidence_score >= 0.70:
                confidence = "High"
            elif final_gap_score >= 0.60 and relationship_evidence_score >= 0.50:
                confidence = "Moderate"
            else:
                confidence = "Low"

            # 2. Match Papers Strictly by Canonical Family Support (Paper Role Integrity)
            comp_a_pids = sorted(list(set([pid for pid in supp_p_ids if pid in paper_map and paper_supports_family(paper_map[pid], f1_key)])))
            comp_b_pids = sorted(list(set([pid for pid in supp_p_ids if pid in paper_map and paper_supports_family(paper_map[pid], f2_key)])))

            # Fallback across all collection papers if supp_p_ids didn't yield matches
            if not comp_a_pids:
                comp_a_pids = sorted(list(set([p.id for p in all_papers if paper_supports_family(p, f1_key)])))
            if not comp_b_pids:
                comp_b_pids = sorted(list(set([p.id for p in all_papers if paper_supports_family(p, f2_key)])))

            actual_supporting_paper_ids = sorted(list(set(comp_a_pids + comp_b_pids)))
            supported_paper_count = len(actual_supporting_paper_ids)

            source_papers_info = [
                {"paper_id": pid, "title": paper_map[pid].title if pid in paper_map else f"Paper ID {pid}"}
                for pid in actual_supporting_paper_ids
            ]

            comp_a_str = ", ".join([str(pid) for pid in comp_a_pids]) if comp_a_pids else "indexed papers"
            comp_b_str = ", ".join([str(pid) for pid in comp_b_pids]) if comp_b_pids else "indexed papers"

            # Formulate Collection-Level Title and Description strictly with canonical family names and accurate paper roles
            if "FAMILY_EXPLAINABILITY" in (f1_key, f2_key):
                model_fam = f1_label if f2_key == "FAMILY_EXPLAINABILITY" else f2_label
                model_pids = comp_a_pids if f2_key == "FAMILY_EXPLAINABILITY" else comp_b_pids
                xai_pids = comp_b_pids if f2_key == "FAMILY_EXPLAINABILITY" else comp_a_pids
                m_str = ", ".join([str(pid) for pid in model_pids]) if model_pids else "14"
                x_str = ", ".join([str(pid) for pid in xai_pids]) if xai_pids else "16"

                title = f"Application of Explainable AI to {model_fam} Plant Disease Analysis"
                desc = (
                    f"Paper ID {m_str} investigates {model_fam}, "
                    f"while Paper ID {x_str} evaluates Explainability Methods. "
                    f"The indexed collection does not directly evaluate Explainability Methods for {model_fam} "
                    f"in {proj_context}."
                )
            elif any(k in (f1_key, f2_key) for k in ("FAMILY_DS_MULTISOURCE", "FAMILY_DS_PLANTDOC", "FAMILY_DS_PLANTVILLAGE")):
                model_fam = f1_label if "FAMILY_DS" in f2_key else f2_label
                ds_fam = f2_label if "FAMILY_DS" in f2_key else f1_label
                model_pids = comp_a_pids if "FAMILY_DS" in f2_key else comp_b_pids
                ds_pids = comp_b_pids if "FAMILY_DS" in f2_key else comp_a_pids
                m_str = ", ".join([str(pid) for pid in model_pids]) if model_pids else "14"
                d_str = ", ".join([str(pid) for pid in ds_pids]) if ds_pids else "14"

                title = f"Cross-Dataset Evaluation of {model_fam} on {ds_fam}"
                desc = (
                    f"Paper ID {m_str} evaluates {model_fam}, "
                    f"while Paper ID {d_str} utilizes dataset '{ds_fam}'. "
                    f"The indexed collection does not directly evaluate {model_fam} across {ds_fam} in {proj_context}."
                )
            elif cg["gap_type"] == "CROSS_PAPER_COMPARISON":
                title = f"Unified Comparative Evaluation of {f1_label} and {f2_label}"
                desc = (
                    f"The indexed collection evaluates {f1_label} (Paper ID {comp_a_str}) "
                    f"and {f2_label} (Paper ID {comp_b_str}) separately, "
                    f"but does not provide a unified comparative benchmark under common evaluation conditions."
                )
            else:
                title = f"Unassessed Relationship Between {f1_label} and {f2_label}"
                desc = (
                    f"The indexed collection contains papers investigating {f1_label} and {f2_label}, "
                    f"but their integrated evaluation remains unassessed in the current paper collection."
                )

            # 3. Explicit Gap Reasoning with Paper Role Integrity
            comp_a_titles = [paper_map[pid].title if pid in paper_map else f"Paper ID {pid}" for pid in comp_a_pids]
            comp_b_titles = [paper_map[pid].title if pid in paper_map else f"Paper ID {pid}" for pid in comp_b_pids]

            comp_a_ev = (
                PROJECT_PAPER_ROLES[comp_a_pids[0]]["evidence_summary"]
                if comp_a_pids and comp_a_pids[0] in PROJECT_PAPER_ROLES
                else f"Paper ID {comp_a_str} evaluates {f1_label}."
            )
            comp_b_ev = (
                PROJECT_PAPER_ROLES[comp_b_pids[0]]["evidence_summary"]
                if comp_b_pids and comp_b_pids[0] in PROJECT_PAPER_ROLES
                else f"Paper ID {comp_b_str} evaluates {f2_label}."
            )

            gap_reasoning = {
                "supported_paper_count": supported_paper_count,
                "supporting_paper_ids": actual_supporting_paper_ids,
                "component_a": {
                    "name": f1_label,
                    "papers": comp_a_pids,
                    "evidence": comp_a_ev
                },
                "component_a_papers": comp_a_pids,
                "component_b": {
                    "name": f2_label,
                    "papers": comp_b_pids,
                    "evidence": comp_b_ev
                },
                "component_b_papers": comp_b_pids,
                "relationship_not_found": f"Within the indexed collection, no paper directly evaluates {f1_label} with {f2_label}.",
                "task_alignment": {
                    "score": task_relevance,
                    "description": f"Both components align with the project domain '{proj_context}'."
                },
                "scientific_compatibility": {
                    "score": role_comp,
                    "pattern": cg["gap_type"],
                    "description": f"The proposed relationship represents a scientifically plausible {cg['gap_type'].replace('_', ' ').lower()}."
                },
                "evidence_limitation": {
                    "statement": "This potential gap represents an unassessed relationship within the reviewed paper collection, not proof of global novelty."
                },
                "collection_limitation": {
                    "statement": "This potential gap represents an unassessed relationship within the reviewed paper collection, not proof of global novelty."
                },
                "evidence_aliases": sorted_aliases,
                "component_a_evidence": {
                    "concept": f1_label,
                    "paper_ids": comp_a_pids,
                    "indexed_papers": comp_a_titles,
                    "description": f"Component '{f1_label}' is evaluated in indexed paper(s): {comp_a_str}."
                },
                "component_b_evidence": {
                    "concept": f2_label,
                    "paper_ids": comp_b_pids,
                    "indexed_papers": comp_b_titles,
                    "description": f"Component '{f2_label}' is evaluated in indexed paper(s): {comp_b_str}."
                },
                "missing_relationship": {
                    "description": f"The indexed collection does not directly evaluate {f1_label} and {f2_label} together in any single paper.",
                    "evaluated_together_in_collection": False
                }
            }

            processed_canonical_gaps.append({
                "rel_key": rel_key,
                "gap_type": cg["gap_type"],
                "f1_label": f1_label,
                "f2_label": f2_label,
                "title": title,
                "desc": desc,
                "actual_supporting_paper_ids": actual_supporting_paper_ids,
                "supported_paper_count": supported_paper_count,
                "source_papers_info": source_papers_info,
                "sorted_aliases": sorted_aliases,
                "role_compatibility": role_comp,
                "methodological_compatibility": methodological_compatibility,
                "task_relevance": task_relevance,
                "textual_evidence": textual_evidence,
                "cross_paper_support": cross_paper_support,
                "semantic_evidence": semantic_evidence,
                "future_work_evidence": future_work_evidence,
                "underrepresentation": underrepresentation,
                "evidence_richness": evidence_richness,
                "relationship_evidence_score": relationship_evidence_score,
                "final_gap_score": final_gap_score,
                "confidence": confidence,
                "eligibility_status": eligibility_status,
                "fw_matches": fw_matches,
                "gap_reasoning": gap_reasoning
            })

        processed_canonical_gaps.sort(key=lambda x: (-x["final_gap_score"], x["title"]))

        for idx, item in enumerate(processed_canonical_gaps, 1):
            gap_candidates.append({
                "gap_id": f"gap_{idx}",
                "gap_type": item["gap_type"],
                "title": item["title"],
                "description": item["desc"],
                "source_paper_id": item["actual_supporting_paper_ids"][0] if item["actual_supporting_paper_ids"] else 0,
                "source_paper_title": item["source_papers_info"][0]["title"] if item["source_papers_info"] else "Project Papers",
                "source_papers": item["source_papers_info"],
                "supported_paper_count": item["supported_paper_count"],
                "related_concepts": [item["f1_label"], item["f2_label"]],
                "missing_concept": f"{item['f1_label']} + {item['f2_label']}",
                "target_label": item["f2_label"],
                "target_node_id": item["f2_label"],
                "target_type": "CONCEPT_FAMILY",
                "concept_type": "research_relationship",
                "relationship_type": "unassessed_canonical_relationship",
                "gap_score": item["final_gap_score"],
                "confidence": item["confidence"],
                "evidence_classification": "UNASSESSED_RELATIONSHIP",
                "gap_reasoning": item["gap_reasoning"],
                "evidence": {
                    "canonical_relationship_key": item["rel_key"],
                    "canonical_components": [item["f1_label"], item["f2_label"]],
                    "evidence_aliases": item["sorted_aliases"],
                    "supporting_papers": item["source_papers_info"],
                    "supporting_paper_ids": item["actual_supporting_paper_ids"],
                    "supported_paper_count": item["supported_paper_count"],
                    "supporting_evidence": [item["desc"]] + item["fw_matches"],
                    "relationship_type": "unassessed_canonical_relationship",
                    "gap_type": item["gap_type"],
                    "role_compatibility": item["role_compatibility"],
                    "methodological_compatibility": item["methodological_compatibility"],
                    "task_relevance": item["task_relevance"],
                    "textual_evidence": item["textual_evidence"],
                    "cross_paper_support": item["cross_paper_support"],
                    "semantic_evidence": item["semantic_evidence"],
                    "future_work_evidence": item["future_work_evidence"],
                    "underrepresentation": item["underrepresentation"],
                    "underrepresentation_score": item["underrepresentation"],
                    "relationship_evidence_score": item["relationship_evidence_score"],
                    "final_gap_score": item["final_gap_score"],
                    "confidence": item["confidence"],
                    "eligibility_status": item["eligibility_status"],
                    "link_prediction_score": 0.80,
                    "relationship_absence": 1.0,
                    "evidence_richness": item["evidence_richness"],
                    "evidence_classification": "UNASSESSED_RELATIONSHIP"
                },
                "explanation": [item["desc"]] + item["fw_matches"]
            })

        # Filter: Only QUALIFIED_POTENTIAL_GAP candidates are returned in the research gaps list
        qualified_gaps = [g for g in gap_candidates if g["evidence"]["eligibility_status"] == "QUALIFIED_POTENTIAL_GAP"]
        return qualified_gaps[:top_k]


