"""Validation and sanitization helpers for request payloads."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence
from uuid import UUID

from utils.constants import (
    DEFAULT_LANGUAGE,
    EMOTION_SCORES,
    ERROR_MESSAGES,
    MAX_AUDIO_FILE_SIZE_BYTES,
    MAX_ENGAGEMENT_SCORE,
    MAX_PARTICIPANT_NAME_LENGTH,
    MAX_PARTICIPANTS_PER_SESSION,
    MAX_SESSION_TITLE_LENGTH,
    MAX_TRANSCRIPT_LENGTH,
    MIN_AUDIO_FILE_SIZE_BYTES,
    MIN_ENGAGEMENT_SCORE,
    MIN_PARTICIPANTS_PER_SESSION,
    MIN_SESSION_TITLE_LENGTH,
    MIN_TRANSCRIPT_LENGTH,
    SUPPORTED_AUDIO_EXTENSIONS,
    SUPPORTED_LANGUAGES,
    SessionStatus,
)

_EMAIL_PATTERN = re.compile(
    r'^[A-Za-z0-9](?:[A-Za-z0-9._%+\-]{0,62}[A-Za-z0-9])?@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+$'
)
_CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x1F\x7F]')


class ValidationError(ValueError):
    """Raised when user input fails validation rules."""


def sanitize_string(value: str, *, preserve_newlines: bool = True) -> str:
    """Strip dangerous/control characters and normalize whitespace.

    Args:
        value: Raw input string.
        preserve_newlines: Whether to keep line breaks.

    Returns:
        Sanitized string safe for storage and further processing.
    """
    if not isinstance(value, str):
        raise ValidationError('Expected a string value.')

    cleaned = _CONTROL_CHAR_PATTERN.sub('', value)
    if preserve_newlines:
        cleaned = '\n'.join(segment.strip() for segment in cleaned.splitlines())
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    else:
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return html.escape(cleaned, quote=False)


def sanitize_json_input(payload: Any) -> Any:
    """Recursively sanitize JSON-like payloads.

    Args:
        payload: Dict/list/scalar payload.

    Returns:
        Sanitized payload preserving original structure.
    """
    if isinstance(payload, dict):
        return {str(key): sanitize_json_input(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_json_input(item) for item in payload]
    if isinstance(payload, str):
        return sanitize_string(payload)
    return payload


def validate_email(email: str) -> str:
    """Validate and normalize an email address."""
    normalized = sanitize_string(email, preserve_newlines=False).lower()
    if len(normalized) > 254 or not _EMAIL_PATTERN.match(normalized):
        raise ValidationError(ERROR_MESSAGES['invalid_email'])
    return normalized


def validate_session_title(title: str) -> str:
    """Validate a session title."""
    cleaned = sanitize_string(title, preserve_newlines=False)
    if not (MIN_SESSION_TITLE_LENGTH <= len(cleaned) <= MAX_SESSION_TITLE_LENGTH):
        raise ValidationError(
            f"{ERROR_MESSAGES['invalid_title']} "
            f'Length must be {MIN_SESSION_TITLE_LENGTH}-{MAX_SESSION_TITLE_LENGTH} characters.'
        )
    return cleaned


def validate_transcript(transcript: str) -> str:
    """Validate transcript content."""
    cleaned = sanitize_string(transcript, preserve_newlines=True)
    if not (MIN_TRANSCRIPT_LENGTH <= len(cleaned) <= MAX_TRANSCRIPT_LENGTH):
        raise ValidationError(
            f"{ERROR_MESSAGES['invalid_transcript']} "
            f'Length must be {MIN_TRANSCRIPT_LENGTH}-{MAX_TRANSCRIPT_LENGTH} characters.'
        )
    return cleaned


def validate_participants(participants: Sequence[str] | None) -> list[str]:
    """Validate a participant list and return unique normalized names."""
    if participants is None:
        return []
    if not isinstance(participants, Sequence) or isinstance(participants, (str, bytes)):
        raise ValidationError(ERROR_MESSAGES['invalid_participants'])

    cleaned: list[str] = []
    seen: set[str] = set()
    for index, participant in enumerate(participants):
        if not isinstance(participant, str):
            raise ValidationError(
                f"{ERROR_MESSAGES['invalid_participants']} Item at index {index} must be a string."
            )
        name = sanitize_string(participant, preserve_newlines=False)
        if not name:
            raise ValidationError(
                f"{ERROR_MESSAGES['invalid_participants']} Item at index {index} is empty."
            )
        if len(name) > MAX_PARTICIPANT_NAME_LENGTH:
            raise ValidationError(
                f"{ERROR_MESSAGES['invalid_participants']} "
                f'Participant names must be at most {MAX_PARTICIPANT_NAME_LENGTH} characters.'
            )
        dedupe_key = name.casefold()
        if dedupe_key not in seen:
            seen.add(dedupe_key)
            cleaned.append(name)

    if len(cleaned) > MAX_PARTICIPANTS_PER_SESSION:
        raise ValidationError(
            f"{ERROR_MESSAGES['invalid_participants']} "
            f'Maximum allowed participants: {MAX_PARTICIPANTS_PER_SESSION}.'
        )
    if len(cleaned) < MIN_PARTICIPANTS_PER_SESSION:
        raise ValidationError(
            f"{ERROR_MESSAGES['invalid_participants']} "
            f'Minimum required participants: {MIN_PARTICIPANTS_PER_SESSION}.'
        )

    return cleaned


def validate_engagement_score(score: int | float) -> float:
    """Validate engagement score boundaries."""
    try:
        numeric_score = float(score)
    except (TypeError, ValueError) as exc:
        raise ValidationError(ERROR_MESSAGES['invalid_score']) from exc

    if not (MIN_ENGAGEMENT_SCORE <= numeric_score <= MAX_ENGAGEMENT_SCORE):
        raise ValidationError(ERROR_MESSAGES['invalid_score'])
    return numeric_score


def validate_emotion(emotion: str) -> str:
    """Validate emotion label."""
    normalized = sanitize_string(emotion, preserve_newlines=False).lower()
    if normalized not in EMOTION_SCORES:
        raise ValidationError(ERROR_MESSAGES['invalid_emotion'])
    return normalized


def validate_session_status(status: str) -> str:
    """Validate session status values."""
    normalized = sanitize_string(status, preserve_newlines=False).lower()
    allowed = {item.value for item in SessionStatus}
    if normalized not in allowed:
        raise ValidationError(ERROR_MESSAGES['invalid_status'])
    return normalized


def validate_audio_format(file_name: str) -> str:
    """Validate supported audio extension and return normalized extension."""
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValidationError(
            f"{ERROR_MESSAGES['invalid_audio_format']} "
            f"Allowed formats: {', '.join(SUPPORTED_AUDIO_EXTENSIONS)}."
        )
    return suffix


def validate_audio_file_size(file_size_bytes: int) -> int:
    """Validate uploaded audio file size limits."""
    if not isinstance(file_size_bytes, int):
        raise ValidationError(ERROR_MESSAGES['invalid_audio_size'])
    if not (MIN_AUDIO_FILE_SIZE_BYTES <= file_size_bytes <= MAX_AUDIO_FILE_SIZE_BYTES):
        raise ValidationError(
            f"{ERROR_MESSAGES['invalid_audio_size']} "
            f'File size must be between {MIN_AUDIO_FILE_SIZE_BYTES} and {MAX_AUDIO_FILE_SIZE_BYTES} bytes.'
        )
    return file_size_bytes


def validate_uuid(value: str) -> str:
    """Validate UUID string and return canonical representation."""
    try:
        return str(UUID(value))
    except (ValueError, TypeError) as exc:
        raise ValidationError(ERROR_MESSAGES['invalid_uuid']) from exc


def validate_iso_datetime(value: str) -> str:
    """Validate ISO-8601 date/datetime string."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(ERROR_MESSAGES['invalid_date'])

    normalized = value.replace('Z', '+00:00')
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(ERROR_MESSAGES['invalid_date']) from exc

    return value


def validate_language(language_code: str | None) -> str:
    """Validate language code against supported languages."""
    if language_code is None:
        return DEFAULT_LANGUAGE
    normalized = sanitize_string(language_code, preserve_newlines=False).lower()
    if normalized not in SUPPORTED_LANGUAGES:
        supported = ', '.join(sorted(SUPPORTED_LANGUAGES))
        raise ValidationError(f'Unsupported language code. Supported values: {supported}.')
    return normalized


def validate_request_payload(
    payload: dict[str, Any] | None,
    *,
    required_fields: Iterable[str] = (),
    optional_fields: Iterable[str] = (),
    allow_extra_fields: bool = False,
) -> dict[str, Any]:
    """Validate request payload shape and sanitize JSON values.

    Args:
        payload: Incoming request JSON.
        required_fields: Required keys.
        optional_fields: Optional keys.
        allow_extra_fields: Whether unknown keys are accepted.

    Returns:
        Sanitized payload dict.
    """
    if payload is None or not isinstance(payload, dict):
        raise ValidationError(ERROR_MESSAGES['invalid_payload'])

    required_set = set(required_fields)
    optional_set = set(optional_fields)
    provided = set(payload.keys())

    missing_fields = sorted(required_set - provided)
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    if not allow_extra_fields:
        unexpected = sorted(provided - (required_set | optional_set))
        if unexpected:
            raise ValidationError(f"Unexpected fields: {', '.join(unexpected)}")

    return sanitize_json_input(payload)


def serialize_validated_payload(payload: dict[str, Any]) -> str:
    """Serialize sanitized payload into deterministic JSON string."""
    try:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError) as exc:
        raise ValidationError(ERROR_MESSAGES['invalid_payload']) from exc
