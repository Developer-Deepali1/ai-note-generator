"""Speech-to-text utilities with placeholder Whisper integration."""

from __future__ import annotations

import time
from typing import Any

from modules.audio_processor import AudioValidationError, transcribe_with_whisper_placeholder
from utils.constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


class TranscriptionError(RuntimeError):
    """Raised when transcription cannot be completed."""



def detect_language(text: str) -> str:
    """Very small heuristic language detector used for placeholders."""
    lowered = text.lower()
    if any(token in lowered for token in (' el ', ' la ', ' que ', ' para ')):
        return 'es'
    if any(token in lowered for token in (' le ', ' la ', ' merci ', ' bonjour ')):
        return 'fr'
    if any(token in lowered for token in (' und ', ' der ', ' die ', ' ist ')):
        return 'de'
    return DEFAULT_LANGUAGE



def _text_quality_metrics(transcript: str) -> dict[str, Any]:
    words = transcript.split()
    word_count = len(words)
    unique_ratio = (len(set(word.lower() for word in words)) / word_count) if word_count else 0.0
    quality = min(1.0, 0.35 + (word_count / 200) + (unique_ratio * 0.3)) if word_count else 0.0
    return {
        'word_count': word_count,
        'unique_word_ratio': round(unique_ratio, 3),
        'quality_score': round(quality, 3),
    }



def transcribe_text(text: str, *, language: str | None = None) -> dict[str, Any]:
    """Process direct text payload as a transcript."""
    transcript = str(text or '').strip()
    resolved_language = language or detect_language(transcript)
    metrics = _text_quality_metrics(transcript)
    confidence = 1.0 if transcript else 0.0
    return {
        'source': 'text',
        'transcript': transcript,
        'confidence': confidence,
        'language': resolved_language,
        'quality_metrics': metrics,
        'is_partial': False,
        'notes': 'Transcript supplied directly in the request payload.',
    }



def transcribe_audio_reference(
    audio_reference: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    retries: int = 2,
    retry_delay_seconds: float = 0.1,
) -> dict[str, Any]:
    """Placeholder Whisper flow for path/identifier based audio input."""
    if not audio_reference:
        raise TranscriptionError('Audio reference is required for audio transcription.')

    last_error: Exception | None = None
    for _ in range(max(1, retries + 1)):
        try:
            placeholder_payload = transcribe_with_whisper_placeholder(
                b'RIFF0000WAVEfmt ',
                filename=audio_reference,
                language=language,
            )
            return {
                'source': 'audio',
                'transcript': '',
                'confidence': 0.0,
                'language': language,
                'audio_reference': audio_reference,
                'quality_metrics': {'word_count': 0, 'unique_word_ratio': 0.0, 'quality_score': 0.0},
                'is_partial': False,
                'notes': 'Whisper integration placeholder response.',
                'provider_payload': placeholder_payload,
            }
        except AudioValidationError as exc:
            last_error = exc
            time.sleep(retry_delay_seconds)

    raise TranscriptionError('Audio transcription failed after retries.') from last_error



def transcribe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Transcribe request payload supporting text, partial chunks and audio placeholders."""
    transcript = str(payload.get('transcript') or payload.get('text') or '').strip()
    language_hint = str(payload.get('language') or '').lower().strip() or None
    if language_hint and language_hint not in SUPPORTED_LANGUAGES:
        language_hint = DEFAULT_LANGUAGE

    partial_chunks = payload.get('partial_transcripts')
    if isinstance(partial_chunks, list) and partial_chunks:
        combined = ' '.join(str(chunk).strip() for chunk in partial_chunks if str(chunk).strip()).strip()
        result = transcribe_text(combined, language=language_hint)
        result['is_partial'] = True
        result['chunk_count'] = len(partial_chunks)
        return result

    if transcript:
        return transcribe_text(transcript, language=language_hint)

    audio_reference = (
        payload.get('audio_url')
        or payload.get('audio_file')
        or payload.get('filename')
        or payload.get('path')
        or ''
    )
    if audio_reference:
        return transcribe_audio_reference(audio_reference, language=language_hint or DEFAULT_LANGUAGE)

    return {
        'source': 'unknown',
        'transcript': '',
        'confidence': 0.0,
        'language': language_hint or DEFAULT_LANGUAGE,
        'quality_metrics': {'word_count': 0, 'unique_word_ratio': 0.0, 'quality_score': 0.0},
        'is_partial': False,
        'notes': 'No transcript or audio reference provided.',
    }
