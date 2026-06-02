"""Audio processing helpers for validation, metadata, and upload handling.

Examples:
    >>> validate_audio_extension('meeting.mp3')
    '.mp3'
    >>> detect_audio_format(filename='clip.wav')
    'wav'
"""

from __future__ import annotations

import base64
import io
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Protocol

from utils.constants import MAX_AUDIO_FILE_SIZE_BYTES, SUPPORTED_AUDIO_EXTENSIONS


class AudioProcessingError(ValueError):
    """Base exception for audio processing failures."""


class AudioValidationError(AudioProcessingError):
    """Raised when uploaded audio does not satisfy validation rules."""


@dataclass(slots=True)
class AudioMetadata:
    """Normalized metadata extracted from an audio payload."""

    format: str
    file_size_bytes: int
    duration_seconds: float | None
    bitrate_kbps: int | None
    channels: int | None
    sample_rate_hz: int | None


class UploadFileLike(Protocol):
    """Minimal protocol for Flask/Django file upload objects."""

    filename: str
    mimetype: str

    def save(self, dst: str) -> None:
        """Persist uploaded file to destination path."""


_AUDIO_SIGNATURES: dict[bytes, str] = {
    b'ID3': 'mp3',
    b'fLaC': 'flac',
    b'OggS': 'ogg',
    b'RIFF': 'wav',
}

_MIME_TO_FORMAT: dict[str, str] = {
    'audio/mpeg': 'mp3',
    'audio/mp3': 'mp3',
    'audio/wav': 'wav',
    'audio/x-wav': 'wav',
    'audio/flac': 'flac',
    'audio/ogg': 'ogg',
    'audio/mp4': 'm4a',
    'audio/x-m4a': 'm4a',
}


def validate_audio_extension(filename: str) -> str:
    """Validate extension for supported audio formats.

    Args:
        filename: Source filename.

    Returns:
        Normalized extension.
    """
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        allowed = ', '.join(SUPPORTED_AUDIO_EXTENSIONS)
        raise AudioValidationError(f'Unsupported audio format: {extension}. Allowed: {allowed}.')
    return extension


def detect_audio_format(
    *,
    filename: str | None = None,
    mimetype: str | None = None,
    header_bytes: bytes | None = None,
) -> str:
    """Detect best-effort audio format from extension, mime-type, or magic bytes."""
    if header_bytes:
        for signature, fmt in _AUDIO_SIGNATURES.items():
            if header_bytes.startswith(signature):
                return fmt
        if len(header_bytes) >= 12 and header_bytes[4:8] == b'ftyp':
            return 'm4a'

    if mimetype:
        mapped = _MIME_TO_FORMAT.get(mimetype.lower())
        if mapped:
            return mapped

    if filename:
        return validate_audio_extension(filename).lstrip('.')

    raise AudioValidationError('Unable to detect audio format.')


def validate_audio_content(data: bytes, *, filename: str = 'audio.bin') -> str:
    """Validate raw audio bytes for size and basic integrity checks."""
    if not data:
        raise AudioValidationError('Audio file is empty.')
    if len(data) > MAX_AUDIO_FILE_SIZE_BYTES:
        raise AudioValidationError('Audio file exceeds size limit.')
    detected = detect_audio_format(filename=filename, header_bytes=data[:16])
    if detected == 'wav' and len(data) < 44:
        raise AudioValidationError('Corrupted WAV file: missing header.')
    return detected


def extract_audio_metadata(data: bytes, *, filename: str) -> AudioMetadata:
    """Extract metadata from bytes.

    Uses ``soundfile`` when available and falls back to safe defaults.
    """
    fmt = validate_audio_content(data, filename=filename)
    duration_seconds: float | None = None
    channels: int | None = None
    sample_rate_hz: int | None = None

    try:  # pragma: no cover - optional dependency behavior
        import soundfile as sf

        with sf.SoundFile(io.BytesIO(data)) as audio_file:
            channels = int(audio_file.channels)
            sample_rate_hz = int(audio_file.samplerate)
            frames = int(audio_file.frames)
            duration_seconds = (frames / sample_rate_hz) if sample_rate_hz else None
    except Exception:
        duration_seconds = None

    bitrate_kbps: int | None = None
    if duration_seconds and duration_seconds > 0:
        bitrate_kbps = int((len(data) * 8) / duration_seconds / 1000)

    return AudioMetadata(
        format=fmt,
        file_size_bytes=len(data),
        duration_seconds=duration_seconds,
        bitrate_kbps=bitrate_kbps,
        channels=channels,
        sample_rate_hz=sample_rate_hz,
    )


def generate_audio_preview(data: bytes, *, byte_count: int = 24) -> str:
    """Generate a small base64 preview for debugging/inspection."""
    preview = data[: max(1, byte_count)]
    return base64.b64encode(preview).decode('ascii')


def handle_audio_upload(upload: UploadFileLike, destination_dir: str) -> dict[str, object]:
    """Validate and persist an uploaded audio file safely."""
    extension = validate_audio_extension(upload.filename)
    Path(destination_dir).mkdir(parents=True, exist_ok=True)

    safe_name = f'{Path(upload.filename).stem}{extension}'.replace('..', '').replace('/', '_')
    output_path = Path(destination_dir) / safe_name
    upload.save(str(output_path))

    file_bytes = output_path.read_bytes()
    metadata = extract_audio_metadata(file_bytes, filename=safe_name)
    return {
        'path': str(output_path),
        'metadata': metadata,
        'preview': generate_audio_preview(file_bytes),
    }


def stream_audio_chunks(stream: BinaryIO, *, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    """Yield audio chunks from a binary stream for streaming workflows."""
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        yield chunk


def transcribe_with_whisper_placeholder(
    data: bytes,
    *,
    filename: str,
    language: str = 'en',
) -> dict[str, object]:
    """Placeholder response for future Whisper integration."""
    metadata = extract_audio_metadata(data, filename=filename)
    return {
        'status': 'pending_provider',
        'provider': 'whisper',
        'language': language,
        'transcript': '',
        'confidence': 0.0,
        'audio_metadata': metadata.__dict__,
    }


def remove_temporary_audio_files(paths: Iterable[str]) -> None:
    """Best-effort cleanup for temporary files and folders."""
    for path in paths:
        target = Path(path)
        if target.is_file():
            target.unlink(missing_ok=True)
        elif target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
