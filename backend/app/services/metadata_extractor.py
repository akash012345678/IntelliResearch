import logging
import re
import math
from typing import Dict, List, Optional, Tuple, Set, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CONSTANTS & DICTIONARIES
# ---------------------------------------------------------------------------

METRICS_SET = {
    "f1", "f1-score", "f1 score", "map", "map 50", "map@0.5", "map@0.5:0.95", "map 50-95",
    "accuracy", "precision", "recall", "iou", "auc", "roc-auc", "rmse", "mae", "fps",
    "latency", "throughput", "inference time", "psnr", "ssim", "bleu", "rouge", "loss"
}

PUBLISHER_METADATA_SET = {
    "ieee", "ieee access", "creative commons", "creative commons attribution",
    "rights reserved", "all rights reserved", "digital object identifier", "doi", "issn",
    "volume", "issue", "pages", "license", "publisher", "downloaded from", "terms of use"
}

def clean_text_for_extraction(text: str) -> str:
    """Strip references section, publication boilerplate, copyright lines, and URLs before extraction."""
    if not text:
        return ""
    # Strip bibliography/references section if present
    ref_match = re.search(r'\n\s*(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography)\s*\n', text)
    if ref_match:
        text = text[:ref_match.start()]

    # Strip common publisher boilerplate lines/phrases
    text = re.sub(r'Creative\s+Commons\s+Attribution[^\.\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'IEEE\s+Access[^\.\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'All\s+rights\s+reserved[^\.\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Digital\s+Object\s+Identifier[^\.\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'\bdoi:\s*[^\s]+', '', text, flags=re.IGNORECASE)
    return text


GENERIC_STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'cant', 'cannot', 'could',
    'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent', 'having', 'he', 'hed', 'hell', 'hes', 'her', 'here',
    'heres', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in',
    'into', 'is', 'isnt', 'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor',
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', 'shant', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such', 'than', 'that', 'thats',
    'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres', 'these', 'they', 'theyd', 'theyll',
    'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasnt', 'we',
    'wed', 'well', 'were', 'weve', 'werent', 'what', 'whats', 'when', 'whens', 'where', 'wheres', 'which', 'while',
    'who', 'whos', 'whom', 'why', 'whys', 'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve',
    'your', 'yours', 'yourself', 'yourselves',

    # Names & metadata words
    'john', 'jane', 'doe', 'smith', 'abstract', 'abstracts', 'et', 'al', 'etc',

    # Low-information verbs/nouns
    'improving', 'improved', 'improve', 'improvement', 'classification', 'classified', 'classify',
    'predicting', 'prediction', 'predicted', 'predict', 'detecting', 'detection', 'detected', 'detect',
    'evaluating', 'evaluation', 'evaluated', 'evaluate', 'comparing', 'comparison', 'compared', 'compare',
    'proposing', 'proposal', 'proposed', 'propose', 'using', 'use', 'used', 'uses', 'utilizing', 'utilize',
    'demonstrating', 'demonstrate', 'demonstrated', 'presenting', 'present', 'presents', 'presented',
    'introducing', 'introduce', 'introduced', 'including', 'include', 'included', 'based', 'model', 'models',
    'method', 'methods', 'methodology', 'approach', 'approaches', 'technique', 'techniques', 'system', 'systems',
    'framework', 'frameworks', 'algorithm', 'algorithms', 'paper', 'papers', 'article', 'manuscript', 'study',
    'studies', 'research', 'result', 'results', 'finding', 'findings', 'conclusion', 'introduction', 'section',
    'chapter', 'figure', 'table', 'also', 'therefore', 'thus', 'however', 'new', 'novel', 'different', 'same',
    'similar', 'high', 'low', 'better', 'best', 'well', 'good', 'great', 'various', 'several', 'many', 'few',
    'species', 'process', 'training', 'testing', 'recognition', 'context', 'task', 'tasks', 'data', 'details', 'detail', 'practices', 'practice',
    'plant', 'plants', 'disease', 'diseases', 'crop', 'crops', 'leaf', 'leaves', 'image', 'images', 'feature', 'features'
}

MONTH_NAMES = {
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december',
    'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec'
}

KNOWN_TECHNICAL_TERMS: Dict[str, str] = {
    "yolo": "YOLO",
    "yolov5": "YOLOv5",
    "yolov8": "YOLOv8",
    "yolov9": "YOLOv9",
    "resnet": "ResNet",
    "densenet": "DenseNet",
    "swin transformer": "Swin Transformer",
    "axial transformer": "Axial Transformer",
    "swin-axial transformer": "Swin-Axial Transformer",
    "vision transformer": "Vision Transformer",
    "cnn": "CNN",
    "rnn": "RNN",
    "lstm": "LSTM",
    "svm": "SVM",
    "xgboost": "XGBoost",
    "random forest": "Random Forest",
    "decision tree": "Decision Tree",
    "knn": "KNN",
    "gan": "GAN",
    "autoencoder": "AutoEncoder",
    "upi": "UPI",
    "ai": "AI",
    "bert": "BERT",
    "sbert": "SBERT",
    "payment security": "Payment Security",
    "explainable artificial intelligence": "Explainable Artificial Intelligence",
    "explainable ai": "Explainable Artificial Intelligence",
    "xai": "Explainable Artificial Intelligence",
    "plant disease classification": "Plant Disease Classification",
    "plant disease detection": "Plant Disease Detection",
    "plant pathology": "Plant Pathology",
    "crop disease detection": "Crop Disease Detection",
    "leaf disease classification": "Leaf Disease Classification",
    "driver drowsiness detection": "Driver Drowsiness Detection",
    "fraud detection": "Fraud Detection",
    "online payment": "Online Payment",
    "transaction risk": "Transaction Risk",
    "traffic congestion prediction": "Traffic Congestion Prediction",
    "quantum cryptography": "Quantum Cryptography",
    "quantum cryptography protocols": "Quantum Cryptography Protocols",
    "object detection": "Object Detection",
    "image classification": "Image Classification",
    "semantic segmentation": "Semantic Segmentation",
    "transfer learning": "Transfer Learning",
    "deep learning": "Deep Learning",
    "machine learning": "Machine Learning",
    "edge computing": "Edge Computing",
    "knowledge distillation": "Knowledge Distillation",
    "plantdoc": "PlantDoc",
    "plantvillage": "PlantVillage",
    "coco": "COCO",
    "ms coco": "MS COCO",
    "imagenet": "ImageNet",
}


# ---------------------------------------------------------------------------
# PROVENANCE & EVIDENCE SNIPPET HELPER
# ---------------------------------------------------------------------------

def find_entity_provenance(
    key_or_pattern: Any,
    title: str = "",
    abstract: Optional[str] = None,
    full_text: str = ""
) -> Tuple[Optional[str], str, str, float]:
    """
    Search title, abstract, and full text for exact sentence evidence and section location.
    Returns: (evidence_text, evidence_section, source, location_confidence_bonus)
    """
    if isinstance(key_or_pattern, str):
        pattern = re.compile(rf'\b{re.escape(key_or_pattern)}\b', re.IGNORECASE)
    else:
        pattern = key_or_pattern

    t_text = (title or "").strip()
    a_text = (abstract or "").strip()
    f_text = clean_text_for_extraction(full_text or "").strip()

    # 1. Check Title
    if t_text and pattern.search(t_text):
        return (t_text, "Title", "title", 0.35)

    # 2. Check Abstract
    if a_text and pattern.search(a_text):
        sentences = [s.strip() for s in re.split(r'[.\n!?;]+', a_text) if s.strip()]
        for s in sentences:
            if pattern.search(s):
                clean_s = re.sub(r'\s+', ' ', s)
                return (clean_s, "Abstract", "abstract", 0.25)
        return (a_text[:250], "Abstract", "abstract", 0.25)

    # 3. Check Full Text (Body)
    if f_text and pattern.search(f_text):
        sentences = [s.strip() for s in re.split(r'[.\n!?;]+', f_text) if s.strip()]
        for s in sentences:
            if pattern.search(s):
                clean_s = re.sub(r'\s+', ' ', s)
                return (clean_s[:250], "Body", "body", 0.10)

    return (None, "Unknown", "body", 0.0)


# ---------------------------------------------------------------------------
# 1. DATASET EXTRACTOR WITH ROLE CLASSIFICATION
# ---------------------------------------------------------------------------

class DatasetExtractor:
    """
    Extracts dataset mentions and classifies their role in paper context:
    - experimental (or EXPERIMENTAL_DATASET): Dataset explicitly used for training/testing/evaluation in paper.
    - benchmark (or BENCHMARK_DATASET): Explicitly used for benchmarking.
    - mentioned (or BACKGROUND_DATASET): Mentioned as prior work or background reference.
    """

    KNOWN_DATASETS = {
        "plantdoc": "PlantDoc",
        "plant-doc": "PlantDoc",
        "plantdoc dataset": "PlantDoc",
        "plant doc dataset": "PlantDoc",
        "plant-doc dataset": "PlantDoc",
        "plantvillage": "PlantVillage",
        "plant village": "PlantVillage",
        "plantvillage dataset": "PlantVillage",
        "plant village dataset": "PlantVillage",
        "fusion dataset": "Fusion Dataset",
        "self-constructed fusion dataset": "Fusion Dataset",
        "custom fusion dataset": "Fusion Dataset",
        "coco": "COCO",
        "ms coco": "MS COCO",
        "imagenet": "ImageNet",
        "mnist": "MNIST",
        "cifar-10": "CIFAR-10",
        "cifar-100": "CIFAR-100",
        "pascal voc": "Pascal VOC",
        "kitti": "KITTI",
        "bdd100k": "BDD100K",
        "physionet": "PhysioNet",
        "nthu-ddd": "NTHU-DDD",
        "nthu ddd": "NTHU-DDD",
        "nthu-ddd dataset": "NTHU-DDD",
        "nthu": "NTHU",
        "mimic": "MIMIC"
    }

    EXPERIMENTAL_TRIGGERS = [
        r'\bused\b', r'\busing\b', r'trained\s+on', r'evaluated\s+on', r'experiments?\s+conducted\s+on',
        r'on\s+(?:the\s+)?[\w\-]+\s+dataset', r'precision\s+of\s+[\d\.\%]+\s+on\s+(?:the\s+)?[\w\-]+',
        r'accuracy\s+of\s+[\d\.\%]+\s+on\s+(?:the\s+)?[\w\-]+',
        r'training\s+dataset', r'test\s+dataset', r'validation\s+dataset',
        r'experimental\s+results?\s+on', r'our\s+dataset', r'materials?\s+and\s+methods?',
        r'dataset\s+collection', r'data\s+collection', r'we\s+collected', r'image\s+collection',
        r'fusion\s+dataset', r'self-constructed', r'collected\s+from', r'obtained\s+from',
        r'dataset\s+consisted\s+of', r'dataset\s+contains', r'achieves?\s+[^\.\n]+on\s+(?:the\s+)?[\w\-]+'
    ]

    BACKGROUND_PRETRAIN_TRIGGERS = [
        r'pre-?trained\s+on', r'pre-?training', r'weights?\s+on', r'initial\s+weights',
        r'fine-?tuned\s+from', r'coco\s+pre-?trained', r'coco\s+weights', r'introduced\s+by',
        r'previous\s+studies\s+used'
    ]

    BENCHMARK_TRIGGERS = [
        r'benchmark\s+dataset', r'standard\s+benchmark', r'used\s+as\s+a?\s+benchmark'
    ]

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        combined = f"{title}\n{abstract or ''}\n{full_text}"
        sentences = [s.strip().lower() for s in re.split(r'[.\n!?;]+', combined) if s.strip()]
        results: List[Dict[str, Any]] = []
        seen_names = set()

        # Sort known dataset terms by length descending to match longer specific names first
        sorted_known = sorted(cls.KNOWN_DATASETS.items(), key=lambda x: -len(x[0]))
        for key, canonical in sorted_known:
            pattern = re.compile(rf'\b{re.escape(key)}\b', re.IGNORECASE)
            matching_sentences = [s for s in sentences if pattern.search(s)]
            if not matching_sentences:
                continue

            evidence_text, evidence_section, source, loc_bonus = find_entity_provenance(pattern, title, abstract, full_text)

            role = "mentioned"
            base_confidence = 0.50

            for sentence in matching_sentences:
                is_pretrain = any(re.search(trg, sentence) for trg in cls.BACKGROUND_PRETRAIN_TRIGGERS)
                is_experimental = any(re.search(trg, sentence) for trg in cls.EXPERIMENTAL_TRIGGERS)
                is_benchmark = any(re.search(trg, sentence) for trg in cls.BENCHMARK_TRIGGERS)

                if is_experimental and not is_pretrain:
                    role = "experimental"
                    base_confidence = 0.85
                    break
                elif is_benchmark:
                    role = "benchmark"
                    base_confidence = 0.75
                elif is_pretrain:
                    role = "mentioned"
                    base_confidence = 0.40

            final_conf = round(min(0.99, base_confidence + loc_bonus), 2)
            norm_name = canonical.lower()

            if norm_name not in seen_names:
                seen_names.add(norm_name)
                results.append({
                    "name": canonical,
                    "dataset": canonical,
                    "category": "dataset",
                    "role": role,
                    "confidence": final_conf,
                    "evidence_text": evidence_text or matching_sentences[0][:250],
                    "evidence_section": evidence_section,
                    "source": source
                })

        results.sort(key=lambda x: (x["role"] != "experimental", x["role"] != "benchmark", -x["confidence"]))
        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        full_txt = text if text else f"{title}\n{abstract or ''}"
        role_data = cls.extract_with_roles(full_text=full_txt, title=title, abstract=abstract)
        exp_datasets = [d["name"] for d in role_data if d["role"] in ("experimental", "benchmark")]
        if not exp_datasets and role_data:
            exp_datasets = [d["name"] for d in role_data]
        return exp_datasets


# ---------------------------------------------------------------------------
# 2. DOMAIN EXTRACTOR WITH ROLE CLASSIFICATION
# ---------------------------------------------------------------------------

class ApplicationDomainExtractor:
    """
    Extracts application domains and classifies roles:
    - primary: Core domain of the paper (Title, Abstract objective, Research problem).
    - secondary: Strongly evaluated secondary domain context.
    - mentioned: Incidental mentions in introductory example lists.
    """

    DOMAIN_KEYWORDS = {
        "Plant Diseases": [r'\bplant\s+diseases?\b', r'\bplant\s+pathology\b', r'\bcrop\s+diseases?\b'],
        "Agriculture": [r'\bplant\b', r'\bcrop\b', r'\bleaf\b', r'\bleaves\b', r'\bagricultur', r'\bfarming\b', r'\bplantdoc\b', r'\bplantvillage\b', r'\bpests?\b', r'\bfoliar\b'],
        "Computer Vision": [r'\bcomputer\s+vision\b', r'\bobject\s+detection\b', r'\bimage\s+classification\b', r'\bsemantic\s+segmentation\b'],
        "Driver Safety": [r'\bdrowsiness\b', r'\bdriver\b', r'\bvehicular\b', r'\btraffic\b', r'\broad\s+safety\b'],
        "Transportation": [r'\btransportation\b', r'\btraffic\s+congestion\b'],
        "Financial Fraud": [r'\bfraud\b', r'\bupi\b', r'\bpayment\b', r'\btransaction\b', r'\bbanking\b'],
        "Healthcare": [r'\bhealthcare\b', r'\bhealth\s*care\b', r'\bmedical\b', r'\bclinical\b', r'\bpatient\b', r'\bhospital\b', r'\bpathology\b', r'\blesion\b', r'\bmri\b'],
        "Autonomous Driving": [r'\bautonomous\s+(?:driving|vehicles?|cars?)\b'],
        "IoT": [r'\biot\b', r'\binternet\s+of\s+things\b', r'\bsmart\s+city\b', r'\bsensor\s+network\b'],
        "Education": [r'\beducation\b', r'\be-learning\b', r'\bonline\s+class\b', r'\bstudent\b']
    }

    INCIDENTAL_LIST_TRIGGERS = [
        r'such\s+as', r'for\s+example', r'including', r'applied\s+to\s+various',
        r'ranging\s+from', r'used\s+in\s+fields', r'widely\s+used\s+in', r'various\s+applications'
    ]

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        title_text = (title or "").lower()
        abstract_text = (abstract or "").lower()
        full_lower = full_text.lower()
        combined = f"{title_text}\n{abstract_text}\n{full_lower}"
        sentences = [s.strip() for s in re.split(r'[.\n!?;]+', combined) if s.strip()]
        results: List[Dict[str, Any]] = []

        for domain_name, patterns in cls.DOMAIN_KEYWORDS.items():
            t_matches = sum(1 for p in patterns if re.search(p, title_text))
            a_matches = sum(1 for p in patterns if re.search(p, abstract_text))
            f_matches = sum(1 for p in patterns if re.search(p, full_lower))

            total_matches = t_matches + a_matches + f_matches
            if total_matches == 0:
                continue

            matching_sentences = [s for s in sentences if any(re.search(p, s) for p in patterns)]
            is_incidental_list = any(
                any(re.search(trg, s) for trg in cls.INCIDENTAL_LIST_TRIGGERS)
                for s in matching_sentences
            )

            if t_matches > 0:
                role = "primary"
            elif a_matches >= 2 and not is_incidental_list:
                role = "primary"
            elif a_matches > 0 and not is_incidental_list:
                role = "secondary"
            else:
                role = "mentioned"

            evidence_text, evidence_section, source, _ = find_entity_provenance(patterns[0], title, abstract, full_text)

            results.append({
                "name": domain_name,
                "domain": domain_name,
                "category": "domain",
                "role": role,
                "score": t_matches * 10 + a_matches * 4 + min(f_matches, 3),
                "confidence": 0.95 if role == "primary" else (0.75 if role == "secondary" else 0.40),
                "evidence_text": evidence_text or (matching_sentences[0][:250] if matching_sentences else ""),
                "evidence_section": evidence_section,
                "source": source
            })

        results.sort(key=lambda x: -x["score"])
        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        full_txt = text if text else f"{title}\n{abstract or ''}"
        role_data = cls.extract_with_roles(full_text=full_txt, title=title, abstract=abstract)
        primary = [d["domain"] for d in role_data if d["role"] in ("primary", "secondary")]
        if primary:
            return primary
        return [d["domain"] for d in role_data[:1]] if role_data else []


# ---------------------------------------------------------------------------
# 3. ALGORITHM EXTRACTOR WITH ROLE CLASSIFICATION
# ---------------------------------------------------------------------------

class MetricExtractor:
    METRIC_MAP = {
        "f1": "F1",
        "f1-score": "F1-Score",
        "f1 score": "F1-Score",
        "map": "mAP",
        "map@0.5": "mAP@0.5",
        "map 50": "mAP@0.5",
        "iou": "IoU",
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "auc": "AUC",
        "rmse": "RMSE",
        "mae": "MAE",
        "fps": "FPS",
        "latency": "Latency"
    }

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_txt = clean_text_for_extraction(full_text)
        combined = f"{title}\n{abstract or ''}\n{cleaned_txt}"
        results: List[Dict[str, Any]] = []
        seen = set()

        for term, canonical in cls.METRIC_MAP.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            if pattern.search(combined):
                evidence_text, evidence_section, source, _ = find_entity_provenance(pattern, title, abstract, full_text)
                norm_c = canonical.lower()
                if norm_c not in seen:
                    seen.add(norm_c)
                    results.append({
                        "name": canonical,
                        "metric": canonical,
                        "category": "metric",
                        "role": "evaluation_metric",
                        "confidence": 0.90,
                        "evidence_text": evidence_text or "",
                        "evidence_section": evidence_section,
                        "source": source
                    })

        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        cleaned_txt = clean_text_for_extraction(text)
        role_data = cls.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        return [m["name"] for m in role_data]


class AlgorithmExtractor:
    """
    Extracts algorithm mentions and classifies roles:
    - primary: Model explicitly introduced/proposed in the paper.
    - comparison: Baseline model evaluated for comparison.
    - mentioned: Background mention in related work.
    """

    ALGORITHMS_MAP = {
        "swin-axial transformer": "Swin-Axial Transformer",
        "swin transformer": "Swin Transformer",
        "axial transformer": "Axial Transformer",
        "vision transformer": "Vision Transformer",
        "transformer": "Transformer",
        "yolov9": "YOLOv9",
        "yolov8": "YOLOv8",
        "yolov6": "YOLOv6",
        "yolov5": "YOLOv5",
        "yolo": "YOLO",
        "resnet": "ResNet",
        "densenet": "DenseNet",
        "cnn": "CNN",
        "rnn": "RNN",
        "lstm": "LSTM",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "random forest": "Random Forest",
        "decision tree": "Decision Tree",
        "svm": "SVM",
        "knn": "KNN",
        "gan": "GAN",
        "autoencoder": "AutoEncoder"
    }

    PROPOSED_TRIGGERS = [
        r'we\s+propose', r'we\s+proposed', r'this\s+paper\s+proposes', r'our\s+proposed', r'our\s+model',
        r'our\s+method', r'the\s+proposed\s+model', r'the\s+proposed\s+approach', r'we\s+develop',
        r'we\s+introduce', r'we\s+present', r'innovative\s+(?:model|architecture|transformer|network)',
        r'our\s+approach', r'proposed\s+architecture', r'proposed\s+framework'
    ]

    COMPARISON_TRIGGERS = [
        r'compared\s+with', r'compared\s+to', r'comparison\s+with', r'baselines?', r'benchmark',
        r'existing\s+methods', r'state-of-the-art', r'sota', r'we\s+compare', r'other\s+models',
        r'previous\s+methods', r'reference\s+models', r'competitive\s+methods', r'traditional\s+methods',
        r'versus', r'\bvs\.?\b', r'against', r'outperform', r'evaluated\s+alongside'
    ]

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_txt = clean_text_for_extraction(full_text)
        combined = f"{title}\n{abstract or ''}\n{cleaned_txt}"
        sentences = [s.strip().lower() for s in re.split(r'[.\n!?;]+', combined) if s.strip()]
        results: List[Dict[str, Any]] = []
        seen = set()

        t_lower = (title or "").lower()

        for key, canonical in cls.ALGORITHMS_MAP.items():
            pattern = re.compile(rf'\b{re.escape(key)}\b', re.IGNORECASE)
            matching_sentences = [s for s in sentences if pattern.search(s)]
            if not matching_sentences:
                continue

            evidence_text, evidence_section, source, loc_bonus = find_entity_provenance(pattern, title, abstract, full_text)

            role = "mentioned"
            base_confidence = 0.50

            # Title check for proposed model
            is_title_match = bool(pattern.search(t_lower))
            if is_title_match and any(w in t_lower for w in ["using", "innovative", "proposed", "novel", "with", "improving"]):
                role = "primary"
                base_confidence = 0.90

            for sentence in matching_sentences:
                is_comparison = any(re.search(trg, sentence) for trg in cls.COMPARISON_TRIGGERS)
                is_proposed = any(re.search(trg, sentence) for trg in cls.PROPOSED_TRIGGERS)

                if is_proposed and not is_comparison:
                    role = "primary"
                    base_confidence = 0.88
                    evidence_text = sentence
                    break
                elif is_comparison and role != "primary":
                    role = "comparison"
                    base_confidence = 0.75
                    evidence_text = sentence

            final_conf = round(min(0.99, base_confidence + loc_bonus), 2)
            norm_c = canonical.lower()

            if norm_c not in seen:
                seen.add(norm_c)
                results.append({
                    "name": canonical,
                    "algorithm": canonical,
                    "category": "algorithm",
                    "role": role,
                    "confidence": final_conf,
                    "evidence_text": evidence_text or matching_sentences[0][:250],
                    "evidence_section": evidence_section,
                    "source": source
                })

        results.sort(key=lambda x: (x["role"] != "primary", x["role"] != "comparison", -x["confidence"]))
        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        full_txt = text if text else f"{title}\n{abstract or ''}"
        role_data = cls.extract_with_roles(full_text=full_txt, title=title, abstract=abstract)
        return [a["name"] for a in role_data]


# ---------------------------------------------------------------------------
# 4. METHODOLOGY EXTRACTOR WITH CANONICAL ALIASES
# ---------------------------------------------------------------------------

class MethodologyExtractor:
    METHODOLOGY_ALIAS_MAP = {
        "explainable ai": "Explainable Artificial Intelligence",
        "xai": "Explainable Artificial Intelligence",
        "explainable artificial intelligence": "Explainable Artificial Intelligence",
        "lime": "LIME",
        "local interpretable model-agnostic explanations": "LIME",
        "feature extraction": "Feature Extraction",
        "object detection": "Object Detection",
        "object detectors": "Object Detection",
        "image classification": "Image Classification",
        "semantic segmentation": "Semantic Segmentation",
        "transfer learning": "Transfer Learning",
        "deep learning": "Deep Learning",
        "machine learning": "Machine Learning",
        "federated learning": "Federated Learning",
        "reinforcement learning": "Reinforcement Learning",
        "knowledge distillation": "Knowledge Distillation"
    }

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_txt = clean_text_for_extraction(full_text)
        results: List[Dict[str, Any]] = []
        seen = set()

        for term, canonical in cls.METHODOLOGY_ALIAS_MAP.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            evidence_text, evidence_section, source, loc_bonus = find_entity_provenance(pattern, title, abstract, full_text)
            if not evidence_text:
                continue

            norm_c = canonical.lower()
            if norm_c not in seen:
                seen.add(norm_c)
                is_primary = (source in ("title", "abstract")) or (canonical in ("Object Detection", "Image Classification", "Explainable Artificial Intelligence"))
                role = "primary" if is_primary else "mentioned"
                base_conf = 0.80 if is_primary else 0.60
                results.append({
                    "name": canonical,
                    "methodology": canonical,
                    "category": "methodology",
                    "role": role,
                    "confidence": round(min(0.99, base_conf + loc_bonus), 2),
                    "evidence_text": evidence_text,
                    "evidence_section": evidence_section,
                    "source": source
                })

        results.sort(key=lambda x: (x["role"] != "primary", -x["confidence"]))
        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        full_txt = text if text else f"{title}\n{abstract or ''}"
        role_data = cls.extract_with_roles(full_text=full_txt, title=title, abstract=abstract)
        return [m["name"] for m in role_data]


# ---------------------------------------------------------------------------
# 4B. METRIC EXTRACTOR
# ---------------------------------------------------------------------------

class MetricExtractor:
    """Extracts evaluation metrics and tags them as EVALUATION_METRIC (never keywords)."""

    METRIC_MAP = {
        "accuracy": "Accuracy",
        "highest accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f1": "F1",
        "f1-score": "F1",
        "f1 score": "F1",
        "highest f1": "F1",
        "highest f1 score": "F1",
        "specificity": "Specificity",
        "sensitivity": "Sensitivity",
        "auc": "AUC",
        "roc-auc": "ROC-AUC",
        "roc auc": "ROC-AUC",
        "map": "mAP",
        "map50": "mAP50",
        "map 50": "mAP50",
        "map@0.5": "mAP50",
        "map@0.5:0.95": "mAP50-95",
        "iou": "IoU (Intersection over Union)",
        "intersection over union": "IoU (Intersection over Union)",
        "dice": "Dice",
        "mae": "MAE",
        "mse": "MSE",
        "rmse": "RMSE",
        "r2": "R2",
        "bleu": "BLEU",
        "rouge": "ROUGE",
        "perplexity": "Perplexity",
        "latency": "Latency",
        "fps": "FPS",
        "inference time": "Inference Time",
        "computational complexity": "Computational Complexity"
    }

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_txt = clean_text_for_extraction(full_text)
        combined = f"{title}\n{abstract or ''}\n{cleaned_txt}"
        results: List[Dict[str, Any]] = []
        seen = set()

        for term, canonical in cls.METRIC_MAP.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            if pattern.search(combined):
                norm_c = canonical.lower()
                if norm_c not in seen:
                    seen.add(norm_c)
                    results.append({
                        "name": canonical,
                        "metric": canonical,
                        "role": "EVALUATION_METRIC",
                    })

        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        cleaned_txt = clean_text_for_extraction(text)
        role_data = cls.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        return [m["name"] for m in role_data]


# ---------------------------------------------------------------------------
# 4C. TASK EXTRACTOR
# ---------------------------------------------------------------------------

class TaskExtractor:
    """
    Extracts explicit research task objectives and classifies roles:
    - PRIMARY_TASK: Core target task of the research paper.
    - SECONDARY_TASK: Benchmark or related sub-task.
    """

    TASK_ALIAS_MAP = {
        "object detection": "Object Detection",
        "image classification": "Image Classification",
        "semantic segmentation": "Semantic Segmentation",
        "object tracking": "Object Tracking",
        "driver drowsiness detection": "Driver Drowsiness Detection",
        "drowsiness detection": "Drowsiness Detection",
        "traffic congestion prediction": "Traffic Congestion Prediction",
        "fraud detection": "Fraud Detection",
        "medical image classification": "Medical Image Classification",
        "cybersecurity threat detection": "Cybersecurity Threat Detection",
        "quantum key distribution": "Quantum Key Distribution",
        "quantum cryptography": "Quantum Cryptography"
    }

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_txt = clean_text_for_extraction(full_text)
        combined = f"{title}\n{abstract or ''}\n{cleaned_txt}"
        title_lower = (title or "").lower()
        abstract_lower = (abstract or "").lower()
        results: List[Dict[str, Any]] = []
        seen = set()

        for term, canonical in cls.TASK_ALIAS_MAP.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            if pattern.search(combined):
                norm_c = canonical.lower()
                if norm_c not in seen:
                    seen.add(norm_c)
                    is_primary = bool(pattern.search(title_lower) or pattern.search(abstract_lower))
                    results.append({
                        "name": canonical,
                        "task": canonical,
                        "role": "PRIMARY_TASK" if is_primary else "SECONDARY_TASK",
                        "confidence": "HIGH" if is_primary else "MODERATE"
                    })

        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        cleaned_txt = clean_text_for_extraction(text)
        role_data = cls.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        return [t["name"] for t in role_data]


# ---------------------------------------------------------------------------
# 4D. APPLICATION EXTRACTOR
# ---------------------------------------------------------------------------

class ApplicationExtractor:
    """
    Extracts system deployment formats and application targets:
    - Mobile Application
    - Web Application
    - Real-Time System
    - Embedded System
    - Edge Deployment
    - Decision Support System
    - Driver Assistance System
    """

    APPLICATION_ALIAS_MAP = {
        "mobile application": "Mobile Application",
        "mobile app": "Mobile Application",
        "web application": "Web Application",
        "web app": "Web Application",
        "real-time monitoring": "Real-Time Monitoring",
        "real-time system": "Real-Time System",
        "embedded system": "Embedded System",
        "edge deployment": "Edge Deployment",
        "decision support system": "Decision Support System",
        "driver assistance system": "Driver Assistance System",
        "food security": "Food Security",
        "agricultural productivity": "Agricultural Productivity"
    }

    @classmethod
    def extract_with_roles(cls, full_text: str, title: str = "", abstract: Optional[str] = None) -> List[Dict[str, Any]]:
        cleaned_txt = clean_text_for_extraction(full_text)
        combined = f"{title}\n{abstract or ''}\n{cleaned_txt}"
        results: List[Dict[str, Any]] = []
        seen = set()

        for term, canonical in cls.APPLICATION_ALIAS_MAP.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            if pattern.search(combined):
                norm_c = canonical.lower()
                if norm_c not in seen:
                    seen.add(norm_c)
                    results.append({
                        "name": canonical,
                        "application": canonical,
                        "role": "SYSTEM_APPLICATION",
                        "confidence": "HIGH"
                    })

        return results

    @classmethod
    def extract(cls, text: str, title: str = "", abstract: Optional[str] = None) -> List[str]:
        cleaned_txt = clean_text_for_extraction(text)
        role_data = cls.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        return [a["name"] for a in role_data]


# ---------------------------------------------------------------------------
# GENERIC SENTENCE FRAGMENT & LINGUISTIC NOISE DETECTOR
# ---------------------------------------------------------------------------

PREPOSITION_CONJUNCTION_SET = {
    "across", "above", "below", "between", "during", "into", "through", "under", "until",
    "via", "with", "within", "without", "about", "against", "among", "around", "at", "before",
    "behind", "beside", "by", "for", "from", "in", "of", "off", "on", "onto", "over", "past",
    "to", "toward", "towards", "and", "or", "but", "nor", "so", "yet", "both", "either",
    "neither", "that", "which", "who", "whom", "whose", "when", "where", "while", "as",
    "than", "because", "although", "if", "unless", "prior", "prior to", "due to", "in terms of", "along"
}

NON_TECHNICAL_PROSE_VERBS = {
    "led", "led to", "edited", "fully", "substantial", "change", "ensuring", "minimizing",
    "exploring", "exploration", "obtaining", "achieving", "achieved", "showing", "shown",
    "demonstrating", "demonstrated", "resulting", "results in", "leads to", "proposing",
    "proposed", "improving", "improved", "enhancing", "enhanced", "evaluating", "evaluated",
    "comparing", "compared", "compares", "compare", "using", "used", "utilizing", "utilized", "including", "included",
    "produce", "producing", "foster", "fostering", "identify", "identifying", "predict", "predicting",
    "enhance", "enhances", "select", "selecting", "selects"
}

AUXILIARY_MODAL_VERBS = {
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "may", "might", "must", "can", "could", "should", "would", "will", "shall"
}

NON_TECHNICAL_GERUNDS = {
    "selecting", "identifying", "classifying", "employing", "aligning", "showing",
    "demonstrating", "obtaining", "achieving", "resulting", "providing", "performing",
    "improving", "enhancing", "evaluating", "comparing", "using", "utilizing", "ensuring",
    "minimizing", "exploring", "editing", "leading", "proposing", "conducting"
}

GENERIC_COUNT_WORDS = {
    "number", "count", "amount", "total", "sample", "samples", "token", "tokens",
    "value", "values", "score", "scores", "rate", "rates", "percent", "percentage",
    "level", "levels", "figure", "table", "section", "part", "version", "work", "task", "tasks",
    "process", "processes", "procedure", "procedures", "practice", "practices", "decision", "decisions", "step", "steps",
    "information", "data", "detail", "details", "aspect", "aspects", "approach", "approaches", "result", "results",
    "paper", "papers", "study", "studies", "finding", "findings", "development", "developments", "production", "productions",
    "technology", "technologies", "load", "loads", "calculation", "calculations", "parameter", "parameters", "direction", "directions"
}

INSTITUTIONAL_BOILERPLATE_NOUNS = {
    "laboratory", "department", "faculty", "university", "institute", "school", "college",
    "license", "attribution", "commons", "creative", "rights", "reserved", "doi", "issn",
    "volume", "issue", "pages", "page", "copyright", "publisher", "editor", "edited",
    "received", "accepted", "revised", "published", "article", "manuscript", "downloaded",
    "author", "authors", "affiliation", "affiliations", "email", "address", "organization",
    "citation", "publication", "access", "content", "ieee", "springer", "elsevier", "acm", "arxiv", "journal"
}

GENERIC_ADJECTIVES_VERBS = {
    "early", "accurate", "substantial", "high", "low", "good", "better", "best", "highest", "lowest",
    "new", "novel", "recent", "five", "three", "two", "four", "many", "several",
    "edited", "licensed", "published", "proposed", "improved", "enhanced", "constructed",
    "optimal", "crucial", "additional", "final", "initial", "previous", "following", "various", "certain",
    "local", "global", "actual", "overall", "general", "main", "key", "important", "significant", "different", "similar",
    "traditional", "conventional", "typical", "distinct", "strong", "weak", "innovative", "scale", "state-of-the-art",
    "efficient", "rapid", "complex", "large", "small", "huge", "tiny", "heavy", "light"
}


METRIC_NOISE_TERMS = {
    "f1", "f1 score", "f1-score", "highest f1", "highest f1 score", "map", "map 50", "map@0.5", "precision", "recall",
    "accuracy", "highest accuracy", "iou", "intersection over union", "precision and recall", "terms of f1",
    "achieved an f1", "yolov5s at 0", "score of 0", "fps", "latency", "auc", "rmse", "mae", "map metrics", "map metric"
}


TECHNICAL_NOUN_SUFFIXES = {
    "tion", "sion", "ism", "ment", "ity", "ing", "nomy", "logy", "ics", "work",
    "graph", "base", "set", "model", "net", "network", "system", "module", "layer",
    "method", "approach", "algorithm", "architecture", "technique", "feature", "representation",
    "classifier", "detector", "transformer", "encoder", "decoder", "species", "disease", "diseases"
}

GENERIC_IMPACT_NOUNS = {
    "productivity", "range", "performance", "solution", "solutions", "effect", "effects",
    "cost", "costs", "capability", "capabilities", "requirement", "requirements",
    "volume", "volumes", "show", "shows", "decision", "decisions", "result", "results",
    "bottleneck", "bottlenecks", "aim", "aims", "goal", "goals", "claim", "claims",
    "promise", "promises", "alignment", "alignments", "yield", "yields", "loss", "losses",
    "gain", "gains", "ailment", "ailments", "self", "size", "strategy", "strategies", "module", "modules"
}

TECHNICAL_GERUND_WHITELIST = {
    "learning", "monitoring", "processing", "computing", "reasoning", "mapping",
    "embedding", "tracking", "mining", "clustering", "filtering", "sampling", "modeling"
}

TECHNICAL_PARTICIPLE_WHITELIST = {
    "embedded", "supervised", "unsupervised", "semi-supervised", "weighted", "integrated",
    "convolutional", "recurrent", "pretrained", "fine-tuned", "aligned"
}

THIRD_PERSON_ACTION_VERBS = {
    "proposes", "proposed", "addresses", "addressed", "validates", "validated", "establishes", "established",
    "avoids", "avoided", "reduces", "reduced", "lowers", "lowered", "raises", "raised", "revolutionizes",
    "revolutionized", "affects", "affected", "provides", "provided", "demonstrates", "demonstrated",
    "shows", "showed", "shown", "improves", "improved", "enhances", "enhanced", "produces", "produced", "produce",
    "fosters", "fostered", "identifies", "identified", "identify", "conducts", "conducted", "requires", "required",
    "achieves", "achieved", "leads", "led", "yields", "yielded", "includes", "included", "compares", "compared", "compare",
    "face", "faces", "faced", "extract", "extracts", "extracted", "represents", "represent", "represented",
    "combines", "combined", "incorporates", "incorporated", "introduces", "introduced", "utilizes", "utilized",
    "discusses", "discussed", "investigates", "investigated", "evaluates", "evaluated", "formulates", "formulated"
}


def normalize_research_concept(concept: str) -> str:
    """
    Generic, domain-independent entity normalizer.
    Strips trailing generic container/suffix words (e.g. 'Axial Compression Strategies' -> 'Axial Compression', 'PlantDoc Dataset' -> 'PlantDoc').
    """
    if not concept or not isinstance(concept, str):
        return ""
    clean = " ".join(concept.strip().split())
    words = clean.split()
    if len(words) >= 2:
        last_l = words[-1].lower()
        if last_l in ("strategies", "strategy", "module", "modules", "dataset", "datasets") and len(words) >= 2:
            stem = " ".join(words[:-1])
            if len(stem) >= 3 and not is_grammatical_noise_or_fragment(stem):
                return stem
    return clean


def is_grammatical_noise_or_fragment(phrase: str) -> bool:
    """
    Generic, domain-independent grammatical classifier function.
    Returns True if the phrase is a sentence fragment, linguistic noise, or non-technical prose fragment.
    Does NOT rely on domain-specific hardcoded term lists.
    """
    if not phrase or not isinstance(phrase, str):
        return True

    clean_p = " ".join(phrase.strip().split())
    if len(clean_p) < 2 or len(clean_p) > 60:
        return True

    p_lower = clean_p.lower()

    # Exempt known valid taxonomy terms
    if (
        p_lower in KNOWN_TECHNICAL_TERMS
        or p_lower in TaskExtractor.TASK_ALIAS_MAP
        or p_lower in MethodologyExtractor.METHODOLOGY_ALIAS_MAP
        or p_lower in AlgorithmExtractor.ALGORITHMS_MAP
        or p_lower in DatasetExtractor.KNOWN_DATASETS
        or p_lower in ApplicationExtractor.APPLICATION_ALIAS_MAP
    ):
        return False

    # 0. Check metric terms
    if p_lower in METRIC_NOISE_TERMS:
        return True
    if any(m in p_lower for m in ["intersection over union", "precision and recall", "f1 score", "terms of f1", "map 50", "score of 0"]):
        return True

    words = [w.lower() for w in clean_p.split()]
    if not words:
        return True

    first_word = words[0]
    last_word = words[-1]

    # Date check
    if any(w in MONTH_NAMES for w in words):
        return True

    # 1. Single or 2-letter non-acronym unigrams
    if len(words) == 1 and len(words[0]) <= 2 and words[0].upper() not in ("AI", "UI", "ML"):
        return True

    # 2. Connective boundaries check: Starts or ends with prepositions, conjunctions, or articles
    if first_word in PREPOSITION_CONJUNCTION_SET or last_word in PREPOSITION_CONJUNCTION_SET:
        return True

    # 3. Auxiliary / modal verbs present in phrase
    if any(w in AUXILIARY_MODAL_VERBS for w in words):
        return True

    # 4. Adverbs ending in -ly at boundaries
    if first_word.endswith("ly") or last_word.endswith("ly"):
        return True

    # 5. Non-technical gerunds ending in -ing
    for w in words:
        if w.endswith("ing") and len(w) > 4 and w not in TECHNICAL_GERUND_WHITELIST:
            return True

    # 6. Non-technical past participles ending in -ed
    if (first_word.endswith("ed") and first_word not in TECHNICAL_PARTICIPLE_WHITELIST) or (last_word.endswith("ed") and last_word not in TECHNICAL_PARTICIPLE_WHITELIST):
        return True

    # 7. Action / 3rd-person prose verbs anywhere in phrase
    if any(w in THIRD_PERSON_ACTION_VERBS for w in words):
        return True

    # 8. Generic count words / impact nouns / non-technical adjectives & verbs at boundary
    if first_word in GENERIC_COUNT_WORDS or last_word in GENERIC_COUNT_WORDS or last_word in GENERIC_IMPACT_NOUNS:
        return True
    if first_word in GENERIC_ADJECTIVES_VERBS or last_word in GENERIC_ADJECTIVES_VERBS:
        return True

    # 9. Phrase starts or ends with number
    if first_word.isdigit() or last_word.isdigit() or (len(first_word) > 0 and first_word[0].isdigit()):
        return True

    # 10. Institutional, license & publisher metadata artifacts
    if any(w in INSTITUTIONAL_BOILERPLATE_NOUNS for w in words):
        return True

    # 11. Check if phrase has conjunctions or prepositions in the middle
    for i in range(1, len(words) - 1):
        if words[i] in PREPOSITION_CONJUNCTION_SET:
            return True

    # 12. Check if phrase is a generic multi-word fragment containing only low-information words
    all_generic = all(w in GENERIC_STOP_WORDS or w in PREPOSITION_CONJUNCTION_SET or w in NON_TECHNICAL_PROSE_VERBS or w in GENERIC_COUNT_WORDS for w in words)
    if all_generic:
        return True

    # 13. Check single-letter/number artifacts or broken PDF extraction fragments (e.g. "O License", "4 0 License", "S Parameter Size")
    if len(words[0]) == 1 and not (words[0].isupper() and words[0] in ("A", "I")):
        return True

    return False


# ---------------------------------------------------------------------------
# 5. KEYWORD EXTRACTOR WITH TITLE-FRAGMENT FILTERING & NORMALIZATION
# ---------------------------------------------------------------------------

class KeywordExtractor:
    """
    Extracts canonical academic keywords (residual research concepts) while strictly rejecting
    metrics, publisher/license boilerplate, algorithms, datasets, methodologies, and title fragments.
    """

    TITLE_START_STOPWORDS = {
        "improving", "improves", "improved", "enhancing", "enhancement", "evaluating",
        "evaluation", "predicting", "prediction", "developing", "development", "proposed",
        "proposing", "a", "an", "the", "using", "study", "analysis", "performance", "detectors",
        "innovative", "new", "novel", "towards", "explore", "exploring", "scale"
    }

    TITLE_END_STOPWORDS = {
        "with", "for", "in", "of", "on", "by", "and", "deep", "using", "from", "via", "to"
    }

    ACRONYMS = {"UPI", "AI", "BERT", "SBERT", "XGBoost", "YOLO", "YOLOv5", "YOLOv8", "YOLOv9", "LSTM", "CNN", "RNN", "GAN", "SVM", "KNN", "XAI", "ViT", "COCO", "LIME", "ANOVA"}

    @classmethod
    def extract_explicit_pdf_keywords(cls, full_text: str) -> List[str]:
        """
        Extract explicit 'Keywords:' or 'Index Terms:' section block from PDF text.
        """
        if not full_text:
            return []
        match = re.search(r'(?:Keywords|Index\s+Terms|Key\s+Words)\s*:\s*([^\n\.]+)', full_text, re.IGNORECASE)
        if not match:
            return []
        raw_block = match.group(1)
        raw_items = re.split(r'[,;•\n]+', raw_block)
        clean_items = []
        for item in raw_items:
            t = item.strip()
            if t and not is_grammatical_noise_or_fragment(t):
                clean_items.append(t)
        return clean_items

    @classmethod
    def _is_title_fragment(cls, phrase: str, title: str) -> bool:
        """
        Check if phrase is a leading/trailing truncated fragment of paper title.
        """
        if not phrase or not title:
            return False

        p_norm = " ".join(phrase.lower().split())
        t_norm = " ".join(title.lower().split())

        if p_norm == t_norm:
            return False

        p_words = p_norm.split()
        if not p_words:
            return False

        if p_words[0] in cls.TITLE_START_STOPWORDS or p_words[-1] in cls.TITLE_END_STOPWORDS:
            return True

        return False

    @classmethod
    def extract(
        cls,
        text: str = "",
        top_n: int = 10,
        title: str = "",
        abstract: Optional[str] = None,
        full_text: str = "",
        metadata: Optional[Dict[str, List[str]]] = None
    ) -> List[str]:
        title_text = (title or "").strip()
        abstract_text = (abstract or "").strip()
        full_text_content = clean_text_for_extraction(full_text or text or "").strip()

        combined = f"{title_text}\n{abstract_text}\n{full_text_content}".strip()
        if not combined:
            return []

        candidates: Dict[str, Dict[str, Any]] = {}
        title_lower = title_text.lower()
        combined_lower = combined.lower()

        # Build blacklist sets of entity names from other categories if metadata provided
        other_cat_keys = set()
        if metadata:
            for cat_list in metadata.values():
                if isinstance(cat_list, list):
                    for item in cat_list:
                        if isinstance(item, str) and item.strip():
                            other_cat_keys.add(item.strip().lower())

        # Add all static taxonomy dictionary terms to blacklist for keywords
        for k in DatasetExtractor.KNOWN_DATASETS.keys():
            other_cat_keys.add(k.lower())
        for k in MetricExtractor.METRIC_MAP.keys():
            other_cat_keys.add(k.lower())
        for k in MethodologyExtractor.METHODOLOGY_ALIAS_MAP.keys():
            other_cat_keys.add(k.lower())
        for k in AlgorithmExtractor.ALGORITHMS_MAP.keys():
            other_cat_keys.add(k.lower())
        for k in TaskExtractor.TASK_ALIAS_MAP.keys():
            other_cat_keys.add(k.lower())
        for k in ApplicationExtractor.APPLICATION_ALIAS_MAP.keys():
            other_cat_keys.add(k.lower())
        for k in ApplicationDomainExtractor.DOMAIN_KEYWORDS.keys():
            other_cat_keys.add(k.lower())

        def belongs_to_other_categories(term_lower: str) -> bool:
            if term_lower in other_cat_keys:
                return True
            for ok in other_cat_keys:
                if term_lower == ok:
                    return True
                if len(term_lower) >= 4 and len(ok) >= 4 and (term_lower in ok or ok in term_lower):
                    return True
            return False

        # Add explicit PDF keywords if available
        explicit_kws = cls.extract_explicit_pdf_keywords(full_text_content)
        for kw in explicit_kws:
            kw_lower = kw.lower()
            if not is_grammatical_noise_or_fragment(kw) and not belongs_to_other_categories(kw_lower):
                candidates[kw_lower] = {
                    "canonical": kw,
                    "score": 30,
                    "is_known": True
                }

        # 1. Known Technical Terms
        for term_lower, canonical_name in KNOWN_TECHNICAL_TERMS.items():
            if belongs_to_other_categories(term_lower) or is_grammatical_noise_or_fragment(term_lower):
                continue

            pattern = re.compile(rf'\b{re.escape(term_lower)}\b', re.IGNORECASE)
            matches = len(pattern.findall(combined_lower))
            if matches > 0:
                t_bonus = 20 if pattern.search(title_lower) else 10
                candidates[term_lower] = {
                    "canonical": canonical_name,
                    "score": matches * 5 + t_bonus,
                    "is_known": True
                }

        # 2. Extract Unigrams (Acronyms), Bigrams, and Trigrams strictly from Title, Abstract, and Explicit Keywords
        high_value_text = f"{title_text}\n{abstract_text}".strip()
        clauses = re.split(r'[.\n!?;:,/()\[\]"-]+', high_value_text)
        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue
            tokens = re.findall(r'\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b', clause)
            if not tokens:
                continue

            for tok in tokens:
                tok_upper = tok.upper()
                tok_lower = tok.lower()
                if tok_lower in GENERIC_STOP_WORDS or is_grammatical_noise_or_fragment(tok_lower) or belongs_to_other_categories(tok_lower):
                    continue
                if tok_upper in cls.ACRONYMS or (len(tok) >= 2 and tok.isupper() and tok.lower() not in MONTH_NAMES):
                    norm_k = tok.lower()
                    is_acronym = tok_upper in cls.ACRONYMS
                    if norm_k not in candidates:
                        canonical = tok_upper if is_acronym else tok
                        candidates[norm_k] = {
                            "canonical": canonical,
                            "score": 15 if norm_k in title_lower else 5,
                            "is_known": is_acronym
                        }
                    else:
                        candidates[norm_k]["score"] += 1

            for i in range(len(tokens) - 1):
                w1, w2 = tokens[i].lower(), tokens[i+1].lower()
                bg_lower = f"{w1} {w2}"
                if w1 in GENERIC_STOP_WORDS or w2 in GENERIC_STOP_WORDS or is_grammatical_noise_or_fragment(bg_lower) or belongs_to_other_categories(bg_lower):
                    continue
                if bg_lower not in candidates:
                    canonical = f"{format_word(tokens[i])} {format_word(tokens[i+1])}"
                    score = 25 if bg_lower in title_lower else 10
                    candidates[bg_lower] = {
                        "canonical": canonical,
                        "score": score,
                        "is_known": False
                    }
                else:
                    candidates[bg_lower]["score"] += 3

            for i in range(len(tokens) - 2):
                w1, w2, w3 = tokens[i].lower(), tokens[i+1].lower(), tokens[i+2].lower()
                tg_lower = f"{w1} {w2} {w3}"
                if w1 in GENERIC_STOP_WORDS or w3 in GENERIC_STOP_WORDS or is_grammatical_noise_or_fragment(tg_lower) or belongs_to_other_categories(tg_lower):
                    continue
                if tg_lower not in candidates:
                    canonical = f"{format_word(tokens[i])} {format_word(tokens[i+1])} {format_word(tokens[i+2])}"
                    score = 28 if tg_lower in title_lower else 12
                    candidates[tg_lower] = {
                        "canonical": canonical,
                        "score": score,
                        "is_known": False
                    }
                else:
                    candidates[tg_lower]["score"] += 4

        filtered_keywords: List[str] = []
        seen_norm = set()

        sorted_cand = sorted(candidates.items(), key=lambda item: (-item[1]["score"], -len(item[0])))

        for norm_key, data in sorted_cand:
            canonical = data["canonical"]
            if belongs_to_other_categories(norm_key) or norm_key in seen_norm or is_grammatical_noise_or_fragment(norm_key):
                continue

            if cls._is_title_fragment(norm_key, title_text) or cls._is_title_fragment(canonical, title_text):
                continue

            # Subsumption check
            if not data.get("is_known") and canonical not in cls.ACRONYMS:
                if any(norm_key != s and norm_key in s for s in seen_norm):
                    continue

            seen_norm.add(norm_key)
            filtered_keywords.append(canonical)

            if len(filtered_keywords) >= top_n:
                break

        return filtered_keywords

    @classmethod
    def extract_with_roles(
        cls,
        title: str = "",
        abstract: Optional[str] = None,
        full_text: str = "",
        metadata: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        kws = cls.extract(title=title, abstract=abstract, full_text=full_text, metadata=metadata)
        results = []
        t_lower = (title or "").lower()
        a_lower = (abstract or "").lower()
        explicit_set = set(k.lower() for k in cls.extract_explicit_pdf_keywords(full_text))

        for kw in kws:
            kw_lower = kw.lower()
            pattern = re.compile(rf'\b{re.escape(kw_lower)}\b', re.IGNORECASE)
            evidence_text, evidence_section, source, loc_bonus = find_entity_provenance(pattern, title, abstract, full_text)
            
            is_explicit = kw_lower in explicit_set
            in_title = bool(pattern.search(t_lower))
            is_primary = is_explicit or in_title or bool(pattern.search(a_lower))
            
            role = "primary" if is_primary else "mentioned"
            base_conf = 0.90 if is_explicit else (0.80 if in_title else 0.65)
            
            results.append({
                "name": kw,
                "keyword": kw,
                "category": "keyword",
                "role": role,
                "confidence": round(min(0.99, base_conf + loc_bonus), 2),
                "evidence_text": evidence_text or (title if in_title else abstract or kw),
                "evidence_section": evidence_section,
                "source": source
            })

        return results


def format_word(w: str) -> str:
    if w.upper() in KeywordExtractor.ACRONYMS:
        return w.upper()
    if len(w) <= 3 and w.isupper():
        return w
    return w.capitalize()


# ---------------------------------------------------------------------------
# 6. FUTURE WORK EXTRACTOR
# ---------------------------------------------------------------------------

class FutureWorkExtractor:
    """
    Scans text for explicit future-work signals and research suggestions.
    """

    FUTURE_PATTERNS = [
        r'future\s+work\s+(?:includes?|will|should|aims?\s+to)\s+([^\.\n]+)',
        r'future\s+directions?\s+include\s+([^\.\n]+)',
        r'can\s+be\s+extended\s+to\s+([^\.\n]+)',
        r'we\s+plan\s+to\s+([^\.\n]+)',
        r'aim\s+to\s+explore\s+([^\.\n]+)',
        r'lightweight\s+deployment\s+([^\.\n]+)',
        r'real-time\s+monitoring\s+([^\.\n]+)'
    ]

    @classmethod
    def extract_signals(cls, text: str) -> List[Dict[str, str]]:
        signals = []
        if not text:
            return signals

        for pat in cls.FUTURE_PATTERNS:
            matches = re.finditer(pat, text, re.IGNORECASE)
            for m in matches:
                snippet = m.group(0).strip()
                signals.append({
                    "type": "FUTURE_WORK_SIGNAL",
                    "snippet": snippet[:150],
                    "confidence": "HIGH"
                })
        return signals


# ---------------------------------------------------------------------------
# 7. MAIN METADATA EXTRACTOR SERVICE
# ---------------------------------------------------------------------------

class MetadataExtractor:
    """
    Facade service orchestrating role-aware dataset, domain, algorithm, methodology,
    and title-fragment-filtered keyword extraction.
    """

    @classmethod
    def extract(
        cls,
        title: str,
        abstract: Optional[str],
        full_text: str
    ) -> Dict[str, Any]:
        logger.info(f"Role-aware metadata extraction for: '{title[:50]}...'")

        cleaned_txt = clean_text_for_extraction(full_text)

        datasets_data = DatasetExtractor.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        domains_data = ApplicationDomainExtractor.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        algos_data = AlgorithmExtractor.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        metrics_data = MetricExtractor.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)

        datasets = [d["name"] for d in datasets_data if d["role"] in ("experimental", "benchmark")]
        if not datasets and datasets_data:
            datasets = [d["name"] for d in datasets_data]

        application_domains = [d["domain"] for d in domains_data if d["role"] in ("primary", "secondary")]
        if not application_domains and domains_data:
            application_domains = [d["domain"] for d in domains_data]

        algorithms = [a["name"] for a in algos_data]
        method_roles = MethodologyExtractor.extract_with_roles(cleaned_txt, title=title, abstract=abstract)
        methodologies = [m["name"] for m in method_roles]
        metrics = [m["name"] for m in metrics_data]
        tasks_data = TaskExtractor.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        tasks = [t["name"] for t in tasks_data]
        apps_data = ApplicationExtractor.extract_with_roles(full_text=cleaned_txt, title=title, abstract=abstract)
        applications = [a["name"] for a in apps_data]

        meta_dict = {
            "algorithms": algorithms,
            "methodologies": methodologies,
            "datasets": datasets,
            "application_domains": application_domains,
            "metrics": metrics,
            "tasks": tasks,
            "applications": applications
        }

        keywords = KeywordExtractor.extract(
            title=title,
            abstract=abstract,
            full_text=cleaned_txt,
            top_n=10,
            metadata=meta_dict
        )

        keyword_details = KeywordExtractor.extract_with_roles(
            title=title,
            abstract=abstract,
            full_text=cleaned_txt,
            metadata=meta_dict
        )

        return {
            "keywords": keywords,
            "algorithms": algorithms,
            "datasets": datasets,
            "methodologies": methodologies,
            "application_domains": application_domains,
            "metrics": metrics,
            "tasks": tasks,
            "applications": applications,
            "keyword_details": keyword_details,
            "algorithm_details": algos_data,
            "dataset_details": datasets_data,
            "methodology_details": method_roles,
            "domain_details": domains_data
        }

    @classmethod
    def is_valid_research_concept(cls, concept: str) -> bool:
        """
        Public helper validating whether a string is a genuine substantive research entity.
        Rejects non-technical sentence fragments, linguistic noise, metadata, or publisher text.
        """
        if not concept or not isinstance(concept, str):
            return False
        return not is_grammatical_noise_or_fragment(concept)

    @classmethod
    def extract_rich_metadata(
        cls,
        title: str,
        abstract: Optional[str],
        full_text: str
    ) -> Dict[str, Any]:
        """
        Extended extraction returning role-annotated metadata, metrics, tasks, applications, and future-work signals.
        """
        basic = cls.extract(title=title, abstract=abstract, full_text=full_text)
        cleaned_txt = clean_text_for_extraction(full_text)
        future_signals = FutureWorkExtractor.extract_signals(cleaned_txt)

        return {
            **basic,
            "dataset_roles": basic.get("dataset_details", []),
            "domain_roles": basic.get("domain_details", []),
            "algorithm_roles": basic.get("algorithm_details", []),
            "methodology_roles": basic.get("methodology_details", []),
            "keyword_roles": basic.get("keyword_details", []),
            "future_work_signals": future_signals
        }

