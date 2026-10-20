import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.metadata_extractor import KeywordExtractor, MetadataExtractor



class TestKeywordExtractor(unittest.TestCase):
    """
    Unit test suite for the improved KeywordExtractor and MetadataExtractor.
    """

    def test_01_case_normalization_and_deduplication(self):
        """
        Verify case normalization (e.g. UPI, upi, Upi) producing a single canonical keyword 'UPI'.
        """
        text = "UPI is widely used for digital payments. upi processes instant transactions. Upi security is critical."
        keywords = KeywordExtractor.extract(text=text)
        
        self.assertIn("UPI", keywords)
        self.assertNotIn("upi", keywords)
        self.assertNotIn("Upi", keywords)
        # Ensure count of UPI variants in result list is exactly 1
        upi_count = sum(1 for k in keywords if k.lower() == "upi")
        self.assertEqual(upi_count, 1)

    def test_02_stop_word_filtering(self):
        """
        Verify generic academic stop-words (based, time, system, study, result, paper, research)
        are excluded as isolated unigram keywords.
        """
        title = "A New Study on System Performance and Results"
        abstract = "This paper presents a research method based on time analysis. Different models propose new results."
        full_text = "system system paper research result based time approach method study model performance data"
        
        keywords = KeywordExtractor.extract(title=title, abstract=abstract, full_text=full_text)
        
        generic_words = {"based", "time", "system", "study", "result", "paper", "research", "method", "model", "data", "performance"}
        for word in keywords:
            self.assertNotIn(word.lower(), generic_words, f"Generic stop word '{word}' should not be returned as isolated keyword.")

    def test_03_bigram_extraction(self):
        """
        Verify multi-word technical bigrams like 'Fraud Detection', 'Online Payment', 'Transaction Risk' are prioritized.
        """
        text = "Fraud detection is essential for online payment systems to mitigate transaction risk."
        keywords = KeywordExtractor.extract(text=text)
        
        expected_bigrams = {"Fraud Detection", "Online Payment", "Transaction Risk"}
        found = set(keywords).intersection(expected_bigrams)
        self.assertTrue(len(found) >= 2, f"Expected bigrams not sufficiently found. Got: {keywords}")

    def test_04_trigram_extraction(self):
        """
        Verify extraction of meaningful trigrams like 'Driver Drowsiness Detection' or 'Traffic Congestion Prediction'.
        """
        title = "Driver Drowsiness Detection System Using Computer Vision"
        abstract = "We propose a real-time driver drowsiness detection algorithm."
        full_text = "The driver drowsiness detection approach improves safety."
        
        meta = MetadataExtractor.extract(title=title, abstract=abstract, full_text=full_text)
        all_entities = meta["keywords"] + meta.get("tasks", []) + meta.get("algorithms", [])
        
        self.assertTrue(any("Driver Drowsiness Detection" in e for e in all_entities))

    def test_05_title_weighting(self):
        """
        Verify terms appearing in the title receive higher score and priority over repeated full-text terms.
        """
        title = "Quantum Cryptography Protocols"
        abstract = "We study security protocols."
        full_text = "database database database network network network server server server protocol protocol"
        
        keywords = KeywordExtractor.extract(title=title, abstract=abstract, full_text=full_text)
        
        # 'Quantum Cryptography Protocols' or 'Quantum Cryptography' should be ranked near top despite 'database' repeating in full_text
        self.assertTrue(any("Quantum" in k or "Cryptography" in k for k in keywords[:3]))

    def test_06_technical_term_detection(self):
        """
        Verify technical terms and acronyms (UPI, AI, XGBoost, BERT, YOLO, LSTM) are detected with proper capitalization.
        """
        text = "We compare bert, xgboost, yolo, and lstm for ai based image and text processing."
        meta = MetadataExtractor.extract(title="", abstract="", full_text=text)
        all_entities = meta["keywords"] + meta.get("algorithms", []) + meta.get("methodologies", [])
        
        expected_tech_terms = ["AI", "BERT", "XGBoost", "YOLO", "LSTM"]
        for term in expected_tech_terms:
            self.assertIn(term, all_entities, f"Technical term '{term}' was not found in extracted metadata: {meta}")

    def test_07_maximum_keyword_limit_and_thresholding(self):
        """
        Verify that at most 10 keywords are returned, and fewer than 10 when text lacks high-scoring concepts.
        """
        short_text = "UPI payment security."
        keywords = KeywordExtractor.extract(text=short_text, top_n=10)
        
        self.assertLessEqual(len(keywords), 10)
        self.assertTrue(len(keywords) < 10, f"Expected fewer than 10 keywords for short text, got {len(keywords)}: {keywords}")

    def test_08_short_papers(self):
        """
        Verify short paper inputs do not raise errors and yield reasonable output.
        """
        title = "Deep Learning Overview"
        meta = MetadataExtractor.extract(title=title, abstract=None, full_text="")
        all_entities = meta["keywords"] + meta.get("methodologies", [])
        
        self.assertIn("Deep Learning", all_entities)

    def test_09_missing_abstract(self):
        """
        Verify handling of papers with abstract=None or empty abstract string.
        """
        title = "Object Detection with YOLO"
        full_text = "We evaluate YOLO for real-time object detection."
        
        metadata = MetadataExtractor.extract(title=title, abstract=None, full_text=full_text)
        all_entities = metadata["keywords"] + metadata.get("algorithms", []) + metadata.get("methodologies", [])
        
        self.assertIn("YOLO", metadata["algorithms"])
        self.assertTrue(any("Object Detection" in e for e in all_entities))

    def test_10_target_paper_test_case(self):
        """
        Test case specified in user requirements:
        Paper title: 'AI - FRAUD DETECTION FOR UPI / ONLINE PAYMENT'
        Verify expected concepts are returned and generic stop words are excluded.
        """
        title = "AI - FRAUD DETECTION FOR UPI / ONLINE PAYMENT"
        abstract = (
            "This paper presents a machine learning based transaction risk model for UPI and online payment security. "
            "We propose an XGBoost framework for financial fraud detection to prevent fraudulent transactions in real time."
        )
        full_text = (
            "Introduction: Fraud detection in digital payment systems is critical. "
            "System study result paper research based time upi UPI transaction risk payment security machine learning."
        )
        
        metadata = MetadataExtractor.extract(title=title, abstract=abstract, full_text=full_text)
        keywords = metadata["keywords"]
        all_entities = keywords + metadata.get("algorithms", []) + metadata.get("application_domains", []) + metadata.get("methodologies", []) + metadata.get("tasks", []) + metadata.get("applications", [])
        
        # 1. Must contain meaningful concepts across appropriate entity categories
        expected_concepts = [
            "Fraud Detection",
            "Online Payment",
            "Transaction Risk",
            "Machine Learning",
            "Payment Security"
        ]
        
        for concept in expected_concepts:
            self.assertIn(
                concept,
                all_entities,
                f"Required concept '{concept}' missing from extracted metadata: {metadata}"
            )
            
        # 2. Must NOT contain generic terms as isolated keywords
        forbidden_terms = ["based", "time", "system", "study", "result", "paper", "research"]
        for term in keywords:
            self.assertNotIn(
                term.lower(),
                forbidden_terms,
                f"Forbidden generic term '{term}' returned in keywords: {keywords}"
            )

        # 3. Must NOT return 'UPI' and 'upi' separately
        upi_lower_matches = [k for k in keywords if k.lower() == "upi"]
        self.assertLessEqual(len(upi_lower_matches), 1, f"Duplicate UPI cases returned: {upi_lower_matches}")

    def test_11_date_keyword_filtering(self):
        """
        Verify dates (e.g. '19 Apr 2025', 'Apr 2025', '19 Apr', '2025-04-19'),
        page numbers ('page 12'), section identifiers ('section 3'), and author name noise are rejected.
        """
        title = "Driver Drowsiness Detection System Published 19 Apr 2025"
        abstract = "Published on Apr 2025 in Vol 12, Page 15. See Section 3 for arXiv 2206.10983 details."
        full_text = "19 Apr 2025 19 Apr Apr 2025 page 12 vol 4 section 3 doi 10 1007 v5 cs lg 2025-04-19"

        keywords = KeywordExtractor.extract(title=title, abstract=abstract, full_text=full_text)

        date_noise = {"19 Apr 2025", "Apr 2025", "19 Apr", "2025-04-19", "Page 12", "Vol 4", "Section 3"}
        for noise in date_noise:
            self.assertNotIn(noise, keywords, f"Date or metadata noise '{noise}' should be filtered out from keywords: {keywords}")

    def test_12_technical_acronym_preservation(self):
        """
        Verify legitimate technical terms and acronyms (SBERT, LSTM, RNN, BERT)
        are preserved as valid keywords and not accidentally over-filtered by date/noise rules.
        """
        title = "Neural Architectures for Real-Time Sequence Processing"
        abstract = "We compare BERT, SBERT, LSTM, and RNN architectures for sequence classification."
        full_text = "BERT SBERT LSTM RNN evaluation results."

        meta = MetadataExtractor.extract(title=title, abstract=abstract, full_text=full_text)
        all_entities = meta["keywords"] + meta.get("algorithms", [])

        expected_terms = ["BERT", "SBERT", "LSTM", "RNN"]
        for term in expected_terms:
            self.assertIn(
                term,
                all_entities,
                f"Technical term '{term}' should be preserved in extracted metadata: {meta}"
            )



if __name__ == "__main__":
    unittest.main()


