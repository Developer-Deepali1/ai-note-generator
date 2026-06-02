from __future__ import annotations

import mimetypes
import wave
from pathlib import Path
from typing import Any

from modules.speech_to_text import transcribe_payload
from utils.constants import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_AUDIO_MIME_TYPES


def inspect_audio_reference(reference: str) -> dict[str, Any]:
    path = Path(str(reference or '').strip())
    suffix = path.suffix.lower()
    mime_type = mimetypes.guess_type(path.name)[0]

    result: dict[str, Any] = {
        'reference': str(reference or '').strip(),
        'extension': suffix,
        'mime_type': mime_type,
        'is_supported': suffix in SUPPORTED_AUDIO_EXTENSIONS
        or (mime_type in SUPPORTED_AUDIO_MIME_TYPES if mime_type else False),
        'exists': path.exists() if str(reference or '').strip() else False,
        'size_bytes': None,
        'duration_seconds': None,
        'sample_rate': None,
        'channels': None,
    }

    if result['exists'] and path.is_file():
        result['size_bytes'] = path.stat().st_size
        if suffix == '.wav':
            try:
                with wave.open(str(path), 'rb') as audio:
                    frame_count = audio.getnframes()
                    sample_rate = audio.getframerate()
                    result['duration_seconds'] = round(frame_count / float(sample_rate), 2) if sample_rate else None
                    result['sample_rate'] = sample_rate
                    result['channels'] = audio.getnchannels()
            except wave.Error:
                result['warning'] = 'WAV metadata could not be read.'

    return result


def process_audio_payload(payload: dict[str, Any]) -> dict[str, Any]:
    reference = (
        payload.get('audio_url')
        or payload.get('audio_file')
        or payload.get('filename')
        or payload.get('path')
        or ''
    )
    metadata = inspect_audio_reference(str(reference)) if reference else None
    transcription = transcribe_payload(payload)

    return {
        'audio': metadata,
        'transcription': transcription,
        'status': transcription.get('status', 'pending'),
    }
