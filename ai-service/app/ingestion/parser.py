import os
from pypdf import PdfReader
from docx import Document as DocxDocument
import logging

logger = logging.getLogger(__name__)

class DocumentParser:
    """Extracts text from various file formats."""
    
    @staticmethod
    def parse(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return DocumentParser._parse_pdf(file_path)
        elif ext == ".docx":
            return DocumentParser._parse_docx(file_path)
        elif ext == ".txt":
            return DocumentParser._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        doc = DocxDocument(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def _parse_txt(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
