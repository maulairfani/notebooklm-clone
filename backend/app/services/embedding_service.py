from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

_embeddings: GoogleGenerativeAIEmbeddings | None = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            GEMINI_API_KEY=settings.GEMINI_API_KEY,
        )
    return _embeddings
