from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from utils.constants import SUPPORTED_AUDIO_EXTENSIONS


def _clean_text(text: Any) -> str:
    return ' '.join(str(text or '').replace('\r', '\n').split()).strip()


def _audio_reference(payload: dict[str, Any]) -> str:
    return str(
        payload.get('audio_url')
        or payload.get('audio_file')
        or payload.get('filename')
        or payload.get('path')
        or ''
    ).strip()


def _validate_audio_reference(reference: str) -> tuple[bool, str | None]:
    if not reference:
        return False, 'No audio reference was supplied.'

    suffix = Path(reference.split('?', 1)[0]).suffix.lower()
    if suffix and suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        return False, f'Unsupported audio format: {suffix}.'

    if not reference.startswith(('http://', 'https://')) and suffix:
        path = Path(reference)
        if path.exists() and path.is_file():
            return True, None
        return False, 'Audio file path does not exist on the server.'

    return True, None


def _transcribe_with_openai(reference: str, language: str | None = None) -> dict[str, Any] | None:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or reference.startswith(('http://', 'https://')):
        return None

    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None

    path = Path(reference)
    if not path.exists():
        return None

    client = OpenAI(api_key=api_key)
    with path.open('rb') as audio_file:
        result = client.audio.transcriptions.create(
            model=os.getenv('OPENAI_TRANSCRIPTION_MODEL', 'whisper-1'),
            file=audio_file,
            language=language,
        )

    text = _clean_text(getattr(result, 'text', ''))
    return {
        'source': 'audio',
        'provider': 'openai',
        'transcript': text,
        'confidence': 0.85 if text else 0.0,
        'audio_reference': reference,
        'status': 'completed' if text else 'failed',
        'notes': 'Transcribed audio with the configured OpenAI transcription provider.',
    }


def transcribe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    transcript = _clean_text(payload.get('transcript') or payload.get('text') or '')
    if transcript:
        return {
            'source': 'text',
            'provider': 'direct',
            'transcript': transcript,
            'confidence': 1.0,
            'status': 'completed',
            'language': payload.get('language', 'en'),
            'notes': 'Transcript supplied directly in the request payload.',
        }

    reference = _audio_reference(payload)
    is_valid_reference, validation_error = _validate_audio_reference(reference)
    if not is_valid_reference:
        return {
            'source': 'audio',
            'provider': 'none',
            'transcript': '',
            'confidence': 0.0,
            'audio_reference': reference,
            'status': 'failed',
            'error': validation_error,
            'notes': 'Provide transcript text or a supported audio file reference.',
        }

    provider_result = _transcribe_with_openai(reference, payload.get('language'))
    if provider_result is not None:
        return provider_result

    return {
        'source': 'audio',
        'provider': 'pending',
        'transcript': '',
        'confidence': 0.0,
        'audio_reference': reference,
        'status': 'queued',
        'supported_formats': list(SUPPORTED_AUDIO_EXTENSIONS),
        'notes': (
            'Audio reference accepted. Configure OPENAI_API_KEY and the openai package for '
            'server-side transcription, or send a transcript field for immediate analysis.'
        ),
    }


def transcribe_text(text: str) -> dict[str, Any]:
    return transcribe_payload({'text': text})
