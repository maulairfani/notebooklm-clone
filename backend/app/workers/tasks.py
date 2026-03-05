import uuid

from langchain_postgres import PGVector

from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.models.source import Source
from app.services.embedding_service import get_embeddings
from app.services.processors import get_processor
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_source(self, source_id: str) -> None:
    with SyncSessionLocal() as db:
        source = db.get(Source, uuid.UUID(source_id))
        if source is None:
            return

        source.status = "processing"
        db.commit()

        try:
            processor = get_processor(source.source_type)
            docs = processor.load(source.file_path)

            embeddings = get_embeddings()
            # TODO: Consider switching to 1 collection per notebook (e.g. notebook_{notebook_id})
            # with source_id in document metadata, instead of 1 collection per source.
            # This would avoid looping queries across many collections in SearchSourcesTool.
            PGVector.from_documents(
                documents=docs,
                embedding=embeddings,
                collection_name=f"source_{source_id}",
                connection=settings.SYNC_DATABASE_URL,
                pre_delete_collection=True,
            )

            source.status = "ready"
            db.commit()
        except Exception as exc:
            source.status = "failed"
            source.error_message = str(exc)
            db.commit()
            raise self.retry(exc=exc, countdown=60)
