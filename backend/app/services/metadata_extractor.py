import logging
import re
from collections import Counter
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Modular helper class to extract technical keywords using regex,
    frequency analysis, phrase matching, and stop word filtering.
    """

    # Set of academic, generic, and common English stop words to filter out
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

        # Names & specific metadata
        'john', 'jane', 'doe', 'smith', 'abstract', 'abstracts',

        # Generic academic & paper verbs/nouns
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
        'show', 'shows', 'shown', 'showing', 'find', 'finds', 'found', 'finding', 'findings',
        'identify', 'identifying', 'identified', 'identifies', 'discover', 'discovering', 'discovered',
        'leverage', 'leveraging', 'leveraged', 'use', 'uses', 'used', 'using', 'utility', 'utilize', 'utilizing',
        'give', 'gives', 'given', 'giving', 'make', 'makes', 'made', 'making', 'take', 'takes', 'taken', 'taking'
    }

    # Common technical multi-word phrases to scan for in lower case
    TECHNICAL_PHRASES = [
        "machine learning", "deep learning", "neural network", "neural networks",
        "natural language processing", "computer vision", "reinforcement learning",
        "supervised learning", "unsupervised learning", "large language model",
        "large language models", "recommender system", "recommender systems",
        "recommendation system", "recommendation systems", "information retrieval",
        "data mining", "graph embedding", "graph embeddings", "transfer learning",
        "active learning", "generative adversarial network", "adversarial networks",
        "support vector machine", "decision tree", "random forest", "self-supervised learning",
        "contrastive learning", "zero-shot learning", "few-shot learning", "semantic search",
        "gap discovery", "recommendation engine"
    ]

    # Regex patterns
    ACRONYM_PATTERN = re.compile(r'\b[A-Z]{2,5}\b')
    WORD_PATTERN = re.compile(r'\b[a-z]{3,}\b')

    @classmethod
    def extract(cls, text: str, top_n: int = 10) -> List[str]:
        """
        Extract the top N keywords using acronym matching, phrase scanning,
        word tokenization, frequency analysis, and stop word filtering.
        """
        # 1. Extract acronyms (case-sensitive)
        acronyms = cls.ACRONYM_PATTERN.findall(text)
        acronym_counts = Counter(acronyms)

        # 2. Extract technical phrases (case-insensitive)
        text_lower = text.lower()
        phrase_counts = {}
        matched_phrases = []
        for phrase in cls.TECHNICAL_PHRASES:
            # Word boundary check to avoid substring overlaps (e.g. supervised inside unsupervised)
            pattern = re.compile(rf'\b{re.escape(phrase)}\b')
            count = len(pattern.findall(text_lower))
            if count > 0:
                phrase_counts[phrase] = count
                matched_phrases.append(phrase)

        # 3. Extract single words
        words = cls.WORD_PATTERN.findall(text_lower)
        filtered_words = []
        for word in words:
            if word in cls.STOP_WORDS:
                continue
            # Deduplicate/ignore single words that are already part of matched phrases
            if any(word in phrase for phrase in matched_phrases):
                continue
            filtered_words.append(word)

        word_counts = Counter(filtered_words)

        # 4. Combine all candidate terms
        candidates = {}

        # Add acronyms (avoid stop words)
        for acr, count in acronym_counts.items():
            if acr.lower() in cls.STOP_WORDS:
                continue
            candidates[acr] = count

        # Add phrases
        for phrase, count in phrase_counts.items():
            candidates[phrase] = count

        # Add single words
        for word, count in word_counts.items():
            candidates[word] = count

        # 5. Sort by frequency descending, then alphabetically ascending
        sorted_candidates = sorted(
            candidates.items(), 
            key=lambda item: (-item[1], item[0])
        )
        
        # Return top N keywords
        return [term for term, _ in sorted_candidates[:top_n]]


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
            # Word boundary regex search to ensure exact term matching, case-insensitive
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
            # Word boundary regex search to ensure exact term matching, case-insensitive
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
            # Word boundary regex search to ensure exact term matching, case-insensitive
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
            # Word boundary regex search to ensure exact term matching, case-insensitive
            pattern = re.compile(rf'\b{re.escape(domain)}\b', re.IGNORECASE)
            if pattern.search(text):
                matched.append(domain)
        return matched


class MetadataExtractor:
    """
    Service to extract structured metadata (keywords, algorithms, datasets, 
    methodologies, and application domains) from a research paper's title, 
    abstract, and full text content.
    
    This implementation uses lightweight placeholder heuristic/rule-based methods
    without external AI models, spaCy, or Sentence-BERT.
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
        
        return {
            "keywords": cls._extract_keywords(combined_text),
            "algorithms": cls._extract_algorithms(combined_text),
            "datasets": cls._extract_datasets(combined_text),
            "methodologies": cls._extract_methodologies(combined_text),
            "application_domains": cls._extract_application_domains(combined_text)
        }

    @classmethod
    def _extract_keywords(cls, text: str) -> List[str]:
        """
        Identify key phrases or tags from the text using modular KeywordExtractor.
        """
        return KeywordExtractor.extract(text, top_n=10)

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
