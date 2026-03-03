from abc import ABC, abstractmethod

from langchain_core.documents import Document


class BaseProcessor(ABC):
    @abstractmethod
    def load(self, file_path: str) -> list[Document]:
        """Load and chunk a file into LangChain Documents."""
        ...
