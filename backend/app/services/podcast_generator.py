"""
Podcast generation pipeline:
  source content → podcast script (Gemini LLM) → multi-speaker TTS (Gemini) → WAV
"""
from __future__ import annotations

import json
import logging
import os
import re
import wave
from dataclasses import dataclass
from typing import TYPE_CHECKING

from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_postgres import PGVector

from app.core.config import settings
from app.services.embedding_service import get_embeddings

if TYPE_CHECKING:
    from app.models.podcast import Podcast

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Dialogue dataclass
# ------------------------------------------------------------------


@dataclass
class DialogueTurn:
    speaker: str  # "Host" or "Guest"
    text: str


# ------------------------------------------------------------------
# Format-specific prompt templates
# ------------------------------------------------------------------

_FORMAT_PROMPTS: dict[str, str] = {
    "deep_dive": (
        "Create an in-depth podcast conversation between a Host and a Guest. "
        "The Host guides the discussion with insightful questions and summaries. "
        "The Guest provides detailed explanations, examples, and analysis. "
        "Cover the material thoroughly with natural back-and-forth dialogue, "
        "follow-up questions, and occasional tangents that add depth."
    ),
    "brief": (
        "Create a concise podcast conversation between a Host and a Guest. "
        "The Host asks focused questions and keeps the discussion on track. "
        "The Guest gives clear, succinct answers hitting only the key points. "
        "Keep it short and to the point — no filler or lengthy tangents."
    ),
    "debate": (
        "Create a lively debate-style podcast between a Host and a Guest. "
        "The Host takes one position and the Guest takes the opposing view. "
        "Both speakers present strong arguments, challenge each other's points, "
        "and use evidence from the source material. Keep it respectful but spirited."
    ),
    "critique": (
        "Create a critical analysis podcast between a Host and a Guest. "
        "The Host presents the source material's claims and findings. "
        "The Guest critically examines them — pointing out strengths, weaknesses, "
        "gaps, assumptions, and areas for improvement. "
        "The Host occasionally pushes back or asks for clarification."
    ),
}

_LENGTH_INSTRUCTIONS: dict[str, str] = {
    "short": "Keep the conversation to roughly 8-12 dialogue turns total.",
    "default": "Aim for roughly 20-30 dialogue turns total for a full episode.",
}

# ------------------------------------------------------------------
# Main generator class
# ------------------------------------------------------------------


class PodcastGenerator:
    def __init__(self, podcast: "Podcast", notebook_id: str, output_dir: str) -> None:
        self.podcast = podcast
        self.notebook_id = notebook_id
        self.output_dir = output_dir

        self._genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
        )

    def generate(self) -> str:
        """Run the full pipeline. Returns path to output .wav file."""
        logger.info("Step 1: Fetching source content")
        content = self._get_source_content()

        logger.info("Step 2: Generating podcast script via LLM")
        dialogue = self._generate_script(content)

        if self.podcast.test_mode:
            logger.info("test_mode=True: truncating to 4 turns")
            dialogue = dialogue[:4]

        logger.info("Step 3: Generating multi-speaker TTS (%d turns)", len(dialogue))
        wav_path = self._generate_multi_speaker_tts(dialogue)

        return wav_path

    # ------------------------------------------------------------------
    # Step 1: Fetch source content from PGVector
    # ------------------------------------------------------------------

    def _get_source_content(self) -> str:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from app.models.source import Source

        engine = create_engine(settings.SYNC_DATABASE_URL)
        embeddings = get_embeddings()

        with Session(engine) as db:
            sources = (
                db.query(Source)
                .filter(
                    Source.notebook_id == self.notebook_id,
                    Source.status == "ready",
                )
                .all()
            )

        all_docs = []
        for source in sources:
            store = PGVector(
                embeddings=embeddings,
                collection_name=f"source_{source.id}",
                connection=settings.SYNC_DATABASE_URL,
            )
            docs = store.similarity_search("key concepts and main points", k=5)
            all_docs.extend(docs)

        if not all_docs:
            return "No content available."

        return "\n\n---\n\n".join(doc.page_content for doc in all_docs)

    # ------------------------------------------------------------------
    # Step 2: Generate podcast script via LLM
    # ------------------------------------------------------------------

    def _generate_script(self, content: str) -> list[DialogueTurn]:
        podcast_format = self.podcast.format
        length = self.podcast.length
        language = self.podcast.language
        custom_prompt = self.podcast.custom_prompt

        format_instruction = _FORMAT_PROMPTS.get(
            podcast_format, _FORMAT_PROMPTS["deep_dive"]
        )
        length_instruction = _LENGTH_INSTRUCTIONS.get(
            length, _LENGTH_INSTRUCTIONS["default"]
        )
        custom_instruction = (
            f"\n\nAdditional instruction from user: {custom_prompt}"
            if custom_prompt
            else ""
        )

        prompt = (
            f"{format_instruction}\n\n"
            f"{length_instruction}\n\n"
            f"Language: produce the dialogue in {language}.\n\n"
            "Rules:\n"
            "- Use exactly two speakers: 'Host' and 'Guest'\n"
            "- Each turn should be 1-3 natural sentences\n"
            "- Make the conversation feel natural with reactions, "
            "  acknowledgments, and transitions\n"
            "- Start with the Host introducing the topic\n"
            "- End with a brief wrap-up from the Host\n\n"
            'Return ONLY a valid JSON object: {"dialogue": [{"speaker": "Host", "text": "..."}, ...]}\n\n'
            f"SOURCE CONTENT:\n{content[:8000]}"
            f"{custom_instruction}"
        )

        response = self._llm.invoke(prompt)
        raw = response.content if hasattr(response, "content") else str(response)

        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError(f"LLM did not return valid JSON: {raw[:200]}")

        data = json.loads(json_match.group())
        turns: list[DialogueTurn] = []
        for entry in data.get("dialogue", []):
            speaker = entry.get("speaker", "Host")
            text = entry.get("text", "")
            if text.strip():
                turns.append(DialogueTurn(speaker=speaker, text=text))

        if not turns:
            raise ValueError("LLM produced empty dialogue")

        return turns

    # ------------------------------------------------------------------
    # Step 3: Multi-speaker TTS via Gemini
    # ------------------------------------------------------------------

    def _generate_multi_speaker_tts(self, dialogue: list[DialogueTurn]) -> str:
        """Generate multi-speaker audio using Gemini TTS with MultiSpeakerMarkup."""

        # Build the turn-based text: "Speaker: text\nSpeaker: text\n..."
        conversation_text = "\n".join(
            f"{turn.speaker}: {turn.text}" for turn in dialogue
        )

        # TTS prompt for natural conversation delivery
        tts_prompt = (
            "Read the following as a natural, engaging podcast conversation. "
            "The Host is warm and curious. The Guest is knowledgeable and articulate."
        )

        response = self._genai_client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=f"{tts_prompt}\n\n{conversation_text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Host",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=self.podcast.host_voice or "Kore",
                                    )
                                ),
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Guest",
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=self.podcast.guest_voice or "Puck",
                                    )
                                ),
                            ),
                        ]
                    )
                ),
            ),
        )

        pcm_data = b""
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                pcm_data += part.inline_data.data

        if not pcm_data:
            raise ValueError("TTS returned no audio data")

        output_path = os.path.join(self.output_dir, "podcast.wav")
        _save_pcm_as_wav(pcm_data, output_path)
        return output_path


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _save_pcm_as_wav(pcm_data: bytes, path: str, sample_rate: int = 24000) -> None:
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
