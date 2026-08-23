import logging
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Modular helper class to extract meaningful academic concepts and key phrases
    using n-gram extraction, title/abstract weighting, domain-awareness, technical term
    preservation, case normalization, stop-word filtering, and composite scoring.
    """

    # Comprehensive academic, generic, and common stop words to filter out
    STOP_WORDS = {
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

        # Academic generic words & verbs/nouns (low-information words)
        'can', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
        'discuss', 'discusses', 'discussed', 'discussing', 'demonstrate', 'demonstrates',
        'demonstrated', 'demonstrating', 'present', 'presents', 'presented', 'presenting',
        'introduce', 'introduces', 'introduced', 'introducing', 'include', 'includes', 'included',
        'comprehensive', 'comprehensively', 'detail', 'details', 'detailed',
        'scientific', 'literature', 'read', 'reading', 'write', 'writing', 'run', 'running',
        'architecture', 'architectures', 'index', 'indexing', 'indexed', 'parse', 'parsing', 'parsed',
        'result', 'results', 'finding', 'findings', 'conclusion', 'conclusions',
        'introduction', 'related', 'section', 'chapter', 'figure', 'table', 'chart',
        'also', 'therefore', 'thus', 'hence', 'however', 'nevertheless', 'nonetheless',
        'first', 'second', 'third', 'finally', 'lastly', 'next', 'previous',
        'recent', 'recently', 'current', 'currently', 'future', 'past',
        'well', 'good', 'great', 'excellent', 'high', 'highly', 'low', 'lower', 'better', 'best',
        'various', 'several', 'many', 'few', 'much', 'more', 'most', 'some', 'any',
        'structure', 'structures', 'structured', 'unstructured', 'process', 'processes', 'processing',
        'datum', 'data', 'information', 'metadata', 'content', 'contents',
        'accuracy', 'accurate', 'accurately', 'performance', 'performances', 'efficient', 'efficiently',
        'novel', 'new', 'different', 'same', 'similar', 'common', 'simple', 'complex',
        'author', 'authors', 'article', 'paper', 'manuscript', 'document', 'documents',
        'study', 'studies', 'research', 'researches', 'investigate', 'investigates', 'investigated',
        'method', 'methods', 'methodology', 'methodologies', 'approach', 'approaches', 'technique', 'techniques',
        'system', 'systems', 'model', 'models', 'framework', 'frameworks', 'algorithm', 'algorithms',
        'test', 'testing', 'tested', 'experiment', 'experiments', 'experimental', 'experimentally',
        'propose', 'proposes', 'proposed', 'proposing', 'suggest', 'suggests', 'suggested',
        'develop', 'develops', 'developed', 'developing', 'design', 'designs', 'designed', 'designing',
        'implement', 'implements', 'implemented', 'implementing', 'eval', 'evaluate', 'evaluates', 'evaluated',
        'evaluation', 'evaluations', 'compare', 'compares', 'compared', 'comparing', 'comparison', 'comparisons',
        'show', 'shows', 'shown', 'showing', 'find', 'finds', 'found',
        'identify', 'identifying', 'identified', 'identifies', 'discover', 'discovering', 'discovered',
        'leverage', 'leveraging', 'leveraged', 'use', 'uses', 'used', 'using', 'utility', 'utilize', 'utilizing',
        'give', 'gives', 'given', 'giving', 'make', 'makes', 'made', 'making', 'take', 'takes', 'taken', 'taking',
        'based', 'time', 'times', 'value', 'values', 'level', 'levels', 'type', 'types', 'case', 'cases',
        'work', 'works', 'working', 'base', 'bases', 'main', 'key', 'important', 'significant'
    }

    MONTH_NAMES = {
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec'
    }

    @classmethod
    def _is_date_or_noise(cls, phrase: str) -> bool:
        """
        Identify whether a phrase represents a date, timestamp, page/section number,
        author name pattern, or metadata artifact rather than a legitimate academic concept.
        """
        if not phrase or not phrase.strip():
            return True

        p_lower = phrase.strip().lower()
        words = p_lower.split()

        # 1. Pure digit or single character
        if p_lower.isdigit() or len(p_lower) <= 1:
            return True

        # 2. Date patterns with month names (e.g. "19 apr 2025", "apr 2025", "19 apr", "april 2024")
        has_month = any(w in cls.MONTH_NAMES for w in words)
        has_digit = any(w.isdigit() or bool(re.search(r'\d', w)) for w in words)
        if has_month and (has_digit or len(words) <= 2):
            return True
        if len(words) == 1 and p_lower in cls.MONTH_NAMES:
            return True

        # 3. Standard date regex patterns (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, YYYY)
        if re.match(r'^\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}$', p_lower):
            return True
        if re.match(r'^(19|20)\d{2}$', p_lower):
            return True

        # 4. Section, Page, Volume, Issue, ArXiv, version metadata noise
        # e.g. "page 12", "vol 4", "pp 100", "arxiv 2206 10983", "v5 cs lg", "section 3"
        if re.match(r'^(page|pages|pp|vol|volume|issue|no|number|sec|section|fig|figure|table|v\d+)\b', p_lower):
            return True
        if 'arxiv' in p_lower or 'doi' in p_lower:
            return True

        # 5. Small alphanumeric noise (e.g. "v5", "19", "p1")
        if re.match(r'^[a-z]?\d+[a-z]?$', p_lower) and len(p_lower) <= 3:
            return True

        return False

    # Known technical terms and acronyms with exact preferred canonical capitalization

    KNOWN_TECHNICAL_TERMS: Dict[str, str] = {
        # Acronyms
        "upi": "UPI",
        "ai": "AI",
        "iot": "IoT",
        "nlp": "NLP",
        "cv": "CV",
        "cnn": "CNN",
        "rnn": "RNN",
        "lstm": "LSTM",
        "gru": "GRU",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "bert": "BERT",
        "sbert": "SBERT",
        "yolo": "YOLO",
        "yolov5": "YOLOv5",
        "yolov8": "YOLOv8",
        "resnet": "ResNet",
        "densenet": "DenseNet",
        "svm": "SVM",
        "knn": "KNN",
        "gan": "GAN",
        "autoencoder": "AutoEncoder",
        "ml": "ML",
        "dl": "DL",
        "rl": "RL",
        "llm": "LLM",
        "llms": "LLMs",

        # Standard Multi-word Technical Concepts & Domains
        "fraud detection": "Fraud Detection",
        "financial fraud": "Financial Fraud",
        "financial fraud detection": "Financial Fraud Detection",
        "upi fraud detection": "UPI Fraud Detection",
        "online payment": "Online Payment",
        "transaction risk": "Transaction Risk",
        "payment security": "Payment Security",
        "online payment security": "Online Payment Security",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "natural language processing": "Natural Language Processing",
        "computer vision": "Computer Vision",
        "reinforcement learning": "Reinforcement Learning",
        "supervised learning": "Supervised Learning",
        "unsupervised learning": "Unsupervised Learning",
        "transfer learning": "Transfer Learning",
        "federated learning": "Federated Learning",
        "active learning": "Active Learning",
        "self-supervised learning": "Self-Supervised Learning",
        "contrastive learning": "Contrastive Learning",
        "zero-shot learning": "Zero-Shot Learning",
        "few-shot learning": "Few-Shot Learning",
        "driver drowsiness detection": "Driver Drowsiness Detection",
        "drowsiness detection": "Drowsiness Detection",
        "traffic congestion prediction": "Traffic Congestion Prediction",
        "traffic congestion": "Traffic Congestion",
        "object detection": "Object Detection",
        "semantic segmentation": "Semantic Segmentation",
        "image classification": "Image Classification",
        "edge computing": "Edge Computing",
        "knowledge distillation": "Knowledge Distillation",
        "recommender system": "Recommender System",
        "recommender systems": "Recommender Systems",
        "recommendation system": "Recommendation System",
        "recommendation systems": "Recommendation Systems",
        "information retrieval": "Information Retrieval",
        "data mining": "Data Mining",
        "graph embedding": "Graph Embedding",
        "generative adversarial network": "Generative Adversarial Network",
        "support vector machine": "Support Vector Machine",
        "decision tree": "Decision Tree",
        "random forest": "Random Forest",
        "semantic search": "Semantic Search",
        "smart city": "Smart City",
        "cyber security": "Cyber Security",
        "autonomous driving": "Autonomous Driving"
    }

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
        """
        Extract meaningful academic concept keywords with multi-factor scoring:
        frequency, phrase length (n-grams), title priority, abstract priority,
        technical term detection, domain relevance, and stop-word filtering.
        """
        # 1. Resolve text components
        title_text = (title or "").strip()
        abstract_text = (abstract or "").strip()
        full_text_content = (full_text or "").strip()

        # Fallback if only 'text' argument is provided
        if not title_text and not abstract_text and not full_text_content and text:
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            if parts:
                title_text = parts[0]
                if len(parts) > 1:
                    abstract_text = parts[1]
                if len(parts) > 2:
                    full_text_content = "\n".join(parts[2:])
                else:
                    full_text_content = text
            else:
                full_text_content = text

        # 2. Collect candidates across sections
        # Map: norm_key -> { 'canonical': str, 'title_count': int, 'abstract_count': int, 'full_count': int, 'words': List[str] }
        candidates: Dict[str, Dict] = {}

        def process_section(sec_text: str, sec_name: str):
            if not sec_text:
                return
            extracted_phrases = cls._extract_ngrams_and_terms(sec_text)
            for raw_phrase, canonical in extracted_phrases:
                norm_key = raw_phrase.lower()
                if norm_key not in candidates:
                    candidates[norm_key] = {
                        'canonical': canonical,
                        'title_count': 0,
                        'abstract_count': 0,
                        'full_count': 0,
                        'words': norm_key.split()
                    }
                if sec_name == 'title':
                    candidates[norm_key]['title_count'] += 1
                elif sec_name == 'abstract':
                    candidates[norm_key]['abstract_count'] += 1
                else:
                    candidates[norm_key]['full_count'] += 1

        process_section(title_text, 'title')
        process_section(abstract_text, 'abstract')
        process_section(full_text_content, 'full_text')

        # Also scan KNOWN_TECHNICAL_TERMS explicitly across sections
        combined_all = f"{title_text}\n{abstract_text}\n{full_text_content}"
        combined_lower = combined_all.lower()
        title_lower = title_text.lower()
        abstract_lower = abstract_text.lower()

        import math

        for term_lower, canonical_name in cls.KNOWN_TECHNICAL_TERMS.items():
            pattern = re.compile(rf'\b{re.escape(term_lower)}\b', re.IGNORECASE)
            t_matches = len(pattern.findall(title_lower))
            a_matches = len(pattern.findall(abstract_lower))
            total_matches = len(pattern.findall(combined_lower))
            if total_matches > 0:
                f_matches = max(0, total_matches - t_matches - a_matches)
                if term_lower not in candidates:
                    candidates[term_lower] = {
                        'canonical': canonical_name,
                        'title_count': t_matches,
                        'abstract_count': a_matches,
                        'full_count': f_matches,
                        'words': term_lower.split()
                    }
                else:
                    candidates[term_lower]['canonical'] = canonical_name
                    candidates[term_lower]['title_count'] = max(candidates[term_lower]['title_count'], t_matches)
                    candidates[term_lower]['abstract_count'] = max(candidates[term_lower]['abstract_count'], a_matches)

        if not candidates:
            return []

        # 3. Domain context building
        domain_terms: Set[str] = set()
        if metadata:
            for cat, val_list in metadata.items():
                if isinstance(val_list, list):
                    for v in val_list:
                        if isinstance(v, str) and v.strip():
                            domain_terms.add(v.strip().lower())

        # 4. Score each candidate
        scored_candidates: List[Tuple[str, float, str]] = []

        for norm_key, data in candidates.items():
            words = data['words']
            n_len = len(words)
            canonical = data['canonical']

            # Date and noise artifact filter
            if cls._is_date_or_noise(norm_key) or cls._is_date_or_noise(canonical):
                continue

            t_cnt = data['title_count']
            a_cnt = data['abstract_count']
            f_cnt = data['full_count']
            total_cnt = t_cnt + a_cnt + f_cnt


            if total_cnt == 0:
                continue

            # Filtering rules for unigrams
            if n_len == 1:
                # Unigrams MUST NOT be generic stop words
                if norm_key in cls.STOP_WORDS:
                    continue
                # Unigram must be a known technical term or a strong technical acronym (>1 char)
                is_known_unigram = (norm_key in cls.KNOWN_TECHNICAL_TERMS) or (norm_key.isupper() and len(norm_key) >= 2) or (canonical.isupper() and len(canonical) >= 2)
                if not is_known_unigram and len(norm_key) < 3:
                    continue
                if not is_known_unigram and t_cnt == 0 and a_cnt == 0 and total_cnt < 2:
                    continue

            # Filtering rules for N-grams (bigrams & trigrams)
            if n_len > 1:
                if norm_key not in cls.KNOWN_TECHNICAL_TERMS:
                    if words[0] in cls.STOP_WORDS or words[-1] in cls.STOP_WORDS:
                        continue
                    if all(w in cls.STOP_WORDS for w in words):
                        continue

            # --- Calculate Composite Score ---
            # a) Frequency score (sub-linear to prevent raw count takeover)
            frequency_score = min(total_cnt, 5) * 1.0 + math.log2(1 + total_cnt) * 0.5

            # b) Phrase length score (prefer bigrams/trigrams over isolated unigrams)
            if n_len == 3:
                phrase_score = 4.5
            elif n_len == 2:
                phrase_score = 3.5
            else:
                phrase_score = 0.5

            # c) Technical term score
            is_tech_term = (norm_key in cls.KNOWN_TECHNICAL_TERMS) or canonical.isupper()
            technical_term_score = 5.0 if is_tech_term else 0.0

            # d) Title score
            title_score = 0.0
            if t_cnt > 0:
                title_score = 8.0 + (t_cnt - 1) * 2.0
                if n_len >= 2:
                    title_score += 2.0  # Extra boost for title phrases

            # e) Abstract score
            abstract_score = 0.0
            if a_cnt > 0:
                abstract_score = 4.0 + (a_cnt - 1) * 1.0

            # f) Domain score
            domain_score = 0.0
            if domain_terms:
                if norm_key in domain_terms or any(dt in norm_key for dt in domain_terms):
                    domain_score = 4.0

            # g) Stop word penalty
            stop_word_penalty = 0.0
            if n_len == 1 and norm_key not in cls.KNOWN_TECHNICAL_TERMS:
                stop_word_penalty = 2.0

            keyword_score = (
                frequency_score
                + phrase_score
                + technical_term_score
                + title_score
                + abstract_score
                + domain_score
                - stop_word_penalty
            )

            # Minimum quality score threshold
            if keyword_score >= 3.5:
                scored_candidates.append((norm_key, keyword_score, canonical))

        # 5. Sort candidates by score descending, then length descending, then alphabetically
        scored_candidates.sort(key=lambda item: (-item[1], -len(item[0]), item[0]))

        # 6. Deduplication & Subsumption Filter
        final_keywords: List[str] = []
        selected_keys: List[str] = []

        for norm_key, score, canonical in scored_candidates:
            if any(k.lower() == norm_key for k in selected_keys):
                continue

            is_subsumed = False
            for selected_key in selected_keys:
                if norm_key != selected_key and norm_key in selected_key:
                    if len(norm_key.split()) == 1 and not (norm_key in cls.KNOWN_TECHNICAL_TERMS and cls.KNOWN_TECHNICAL_TERMS[norm_key].isupper()):
                        is_subsumed = True
                        break

            if not is_subsumed:
                final_keywords.append(canonical)
                selected_keys.append(norm_key)

            if len(final_keywords) >= top_n:
                break

        return final_keywords

    @classmethod
    def _extract_ngrams_and_terms(cls, text: str) -> List[Tuple[str, str]]:
        """
        Tokenize text into sentences/clauses, extract unigrams, bigrams, and trigrams,
        and assign canonical casing.
        """
        results: List[Tuple[str, str]] = []
        if not text:
            return results

        clauses = re.split(r'[.\n!?;:,/()\[\]"-]+', text)

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            raw_tokens = re.findall(r'\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b', clause)
            if not raw_tokens:
                continue

            n = len(raw_tokens)

            for i in range(n):
                w1 = raw_tokens[i]
                w1_lower = w1.lower()

                if w1_lower in cls.KNOWN_TECHNICAL_TERMS:
                    results.append((w1_lower, cls.KNOWN_TECHNICAL_TERMS[w1_lower]))
                elif w1.isupper() and len(w1) >= 2:
                    results.append((w1_lower, w1))
                else:
                    results.append((w1_lower, w1.capitalize()))

                if i + 1 < n:
                    w2 = raw_tokens[i + 1]
                    bg_raw = f"{w1} {w2}"
                    bg_lower = bg_raw.lower()
                    if bg_lower in cls.KNOWN_TECHNICAL_TERMS:
                        results.append((bg_lower, cls.KNOWN_TECHNICAL_TERMS[bg_lower]))
                    else:
                        bg_canonical = f"{w1.capitalize()} {w2.capitalize()}"
                        results.append((bg_lower, bg_canonical))

                if i + 2 < n:
                    w3 = raw_tokens[i + 2]
                    tg_raw = f"{w1} {w2} {w3}"
                    tg_lower = tg_raw.lower()
                    if tg_lower in cls.KNOWN_TECHNICAL_TERMS:
                        results.append((tg_lower, cls.KNOWN_TECHNICAL_TERMS[tg_lower]))
                    else:
                        tg_canonical = f"{w1.capitalize()} {w2.capitalize()} {w3.capitalize()}"
                        results.append((tg_lower, tg_canonical))

        return results


class AlgorithmExtractor:
    """
    Modular helper class to search for predefined algorithms inside text using
    case-insensitive word boundary regex matching to ensure precision and uniqueness.
    """

    ALGORITHMS_LIST = [
        "YOLO", "YOLOv5", "YOLOv8", "CNN", "RNN", "LSTM", "GRU", "Transformer", 
        "Vision Transformer", "BERT", "SBERT", "ResNet", "DenseNet", "Random Forest", 
        "Decision Tree", "SVM", "XGBoost", "LightGBM", "KNN", "GAN", "AutoEncoder"
    ]

    @classmethod
    def extract(cls, text: str) -> List[str]:
        """
        Scan text for canonical algorithms in ALGORITHMS_LIST and return unique matched values.
        """
        matched = []
        for algo in cls.ALGORITHMS_LIST:
            pattern = re.compile(rf'\b{re.escape(algo)}\b', re.IGNORECASE)
            if pattern.search(text):
                matched.append(algo)
        return matched


class DatasetExtractor:
    """
    Modular helper class to search for predefined datasets inside text using
    case-insensitive word boundary regex matching to ensure precision and uniqueness.
    """

    DATASETS_LIST = [
        "COCO", "ImageNet", "MNIST", "CIFAR-10", "KITTI", "BDD100K", 
        "Pascal VOC", "Waymo", "PhysioNet", "NTHU", "MIMIC", "UCF101", 
        "HMDB51", "GLUE", "SQuAD"
    ]

    @classmethod
    def extract(cls, text: str) -> List[str]:
        """
        Scan text for canonical datasets in DATASETS_LIST and return unique matched values.
        """
        matched = []
        for dataset in cls.DATASETS_LIST:
            pattern = re.compile(rf'\b{re.escape(dataset)}\b', re.IGNORECASE)
            if pattern.search(text):
                matched.append(dataset)
        return matched


class MethodologyExtractor:
    """
    Modular helper class to search for predefined methodologies inside text using
    case-insensitive word boundary regex matching to ensure precision and uniqueness.
    """

    METHODOLOGIES_LIST = [
        "Object Detection", "Image Classification", "Semantic Segmentation", 
        "Transfer Learning", "Deep Learning", "Machine Learning", "Federated Learning", 
        "Edge Computing", "Reinforcement Learning", "Knowledge Distillation"
    ]

    @classmethod
    def extract(cls, text: str) -> List[str]:
        """
        Scan text for canonical methodologies in METHODOLOGIES_LIST and return unique matched values.
        """
        matched = []
        for method in cls.METHODOLOGIES_LIST:
            pattern = re.compile(rf'\b{re.escape(method)}\b', re.IGNORECASE)
            if pattern.search(text):
                matched.append(method)
        return matched


class ApplicationDomainExtractor:
    """
    Modular helper class to search for predefined application domains inside text using
    case-insensitive word boundary regex matching to ensure precision and uniqueness.
    """

    DOMAINS_LIST = [
        "Healthcare", "Computer Vision", "Transportation", "Autonomous Driving", 
        "Agriculture", "Cyber Security", "Education", "Finance", "Robotics", 
        "Manufacturing", "IoT", "Smart City"
    ]

    @classmethod
    def extract(cls, text: str) -> List[str]:
        """
        Scan text for canonical domains in DOMAINS_LIST and return unique matched values.
        """
        matched = []
        for domain in cls.DOMAINS_LIST:
            pattern = re.compile(rf'\b{re.escape(domain)}\b', re.IGNORECASE)
            if pattern.search(text):
                matched.append(domain)
        return matched


class MetadataExtractor:
    """
    Service to extract structured metadata (keywords, algorithms, datasets, 
    methodologies, and application domains) from a research paper's title, 
    abstract, and full text content.
    """

    @classmethod
    def extract(
        cls, 
        title: str, 
        abstract: Optional[str], 
        full_text: str
    ) -> Dict[str, List[str]]:
        """
        Extracts metadata list fields from the paper text components.
        
        Args:
            title: The title of the paper.
            abstract: The abstract of the paper (optional).
            full_text: The full text content of the paper.
            
        Returns:
            A dictionary containing lists of keywords, algorithms, datasets,
            methodologies, and application domains.
        """
        logger.info(f"Extracting metadata for paper title: '{title[:50]}...'")
        
        combined_text = f"{title}\n{abstract or ''}\n{full_text}"
        
        algorithms = cls._extract_algorithms(combined_text)
        datasets = cls._extract_datasets(combined_text)
        methodologies = cls._extract_methodologies(combined_text)
        application_domains = cls._extract_application_domains(combined_text)

        metadata_context = {
            "algorithms": algorithms,
            "datasets": datasets,
            "methodologies": methodologies,
            "application_domains": application_domains
        }

        keywords = KeywordExtractor.extract(
            title=title,
            abstract=abstract,
            full_text=full_text,
            metadata=metadata_context,
            top_n=10
        )
        
        return {
            "keywords": keywords,
            "algorithms": algorithms,
            "datasets": datasets,
            "methodologies": methodologies,
            "application_domains": application_domains
        }

    @classmethod
    def _extract_keywords(cls, text: str) -> List[str]:
        """
        Identify key phrases or tags from the text using modular KeywordExtractor.
        """
        return KeywordExtractor.extract(text=text, top_n=10)

    @classmethod
    def _extract_algorithms(cls, text: str) -> List[str]:
        """
        Identify machine learning or data processing algorithms mentioned in the text.
        """
        return AlgorithmExtractor.extract(text)

    @classmethod
    def _extract_datasets(cls, text: str) -> List[str]:
        """
        Identify benchmark datasets mentioned in the text.
        """
        return DatasetExtractor.extract(text)

    @classmethod
    def _extract_methodologies(cls, text: str) -> List[str]:
        """
        Identify research methodologies or techniques used in the study.
        """
        return MethodologyExtractor.extract(text)

    @classmethod
    def _extract_application_domains(cls, text: str) -> List[str]:
        """
        Identify application domains or use cases of the research.
        """
        return ApplicationDomainExtractor.extract(text)

