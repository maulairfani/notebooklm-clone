from app.services.processors.base import BaseProcessor
from app.services.processors.pdf_processor import PdfProcessor


def get_processor(source_type: str) -> BaseProcessor:
    if source_type == "pdf":
        return PdfProcessor()
    raise ValueError(f"Unsupported source type: {source_type}")
