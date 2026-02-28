import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Cleans, chunks, and anonymizes clinical text."""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def remove_phi(self, text: str) -> str:
        """Anonymize PHI using Presidio."""
        results = self.analyzer.analyze(text=text, entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "DATE_TIME"], language='en')
        anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized_result.text

    def chunk_text(self, text: str) -> list[str]:
        """Split text into optimized chunks."""
        return self.text_splitter.split_text(text)
