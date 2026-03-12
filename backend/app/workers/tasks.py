import os
import uuid

from langchain_postgres import PGVector

from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.models.source import Source
from app.models.podcast import Podcast
from app.models.video import Video
from app.services.embedding_service import get_embeddings
from app.services.podcast_generator import PodcastGenerator
from app.services.processors import get_processor
from app.services.video_generator import VideoGenerator
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

            # Strip NUL bytes — PostgreSQL rejects strings containing \x00
            for doc in docs:
                doc.page_content = doc.page_content.replace("\x00", "")

            embeddings = get_embeddings()
            # TODO(perf): Saat ini 1 collection per source → SearchSourcesTool harus loop N queries
            # untuk N sources. Ganti ke 1 collection per notebook (`notebook_{notebook_id}`) dengan
            # `source_id` di metadata dokumen, lalu filter via `search_kwargs`. Breaking change —
            # perlu migrasi ulang semua embedding yang sudah ada.
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


@celery_app.task(bind=True, max_retries=1)
def generate_video(self, video_id: str) -> None:
    with SyncSessionLocal() as db:
        video = db.get(Video, uuid.UUID(video_id))
        if video is None:
            return

        video.status = "processing"
        db.commit()

        output_dir = os.path.join(
            settings.UPLOAD_DIR,
            "videos",
            str(video.notebook_id),
            video_id,
        )
        os.makedirs(output_dir, exist_ok=True)

        try:
            generator = VideoGenerator(
                video=video,
                notebook_id=str(video.notebook_id),
                output_dir=output_dir,
            )
            mp4_path = generator.generate()

            video.status = "ready"
            video.file_path = mp4_path
            db.commit()
        except Exception as exc:
            video.status = "failed"
            video.error_message = str(exc)
            db.commit()
            raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=1)
def generate_podcast(self, podcast_id: str) -> None:
    with SyncSessionLocal() as db:
        podcast = db.get(Podcast, uuid.UUID(podcast_id))
        if podcast is None:
            return

        podcast.status = "processing"
        db.commit()

        output_dir = os.path.join(
            settings.UPLOAD_DIR,
            "podcasts",
            str(podcast.notebook_id),
            podcast_id,
        )
        os.makedirs(output_dir, exist_ok=True)

        try:
            generator = PodcastGenerator(
                podcast=podcast,
                notebook_id=str(podcast.notebook_id),
                output_dir=output_dir,
            )
            wav_path = generator.generate()

            podcast.status = "ready"
            podcast.file_path = wav_path
            db.commit()
        except Exception as exc:
            podcast.status = "failed"
            podcast.error_message = str(exc)
            db.commit()
            raise self.retry(exc=exc, countdown=60)
