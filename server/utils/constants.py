"""Global constants for the AI Note Generator backend."""

from __future__ import annotations

from enum import Enum
from http import HTTPStatus


class SessionStatus(str, Enum):
    """Supported lifecycle states for a session."""

    CREATED = 'created'
    ACTIVE = 'active'
    ANALYZED = 'analyzed'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'
    FAILED = 'failed'


class NoteStatus(str, Enum):
    """Supported lifecycle states for a note."""

    DRAFT = 'draft'
    GENERATED = 'generated'
    REVIEWED = 'reviewed'
    PUBLISHED = 'published'
    FAILED = 'failed'


class EngagementEventType(str, Enum):
    """Supported engagement event categories."""

    ATTENDED = 'attended'
    SPOKE = 'spoke'
    QUESTION = 'question'
    RESPONSE = 'response'
    FOCUS = 'focus'
    DISTRACTED = 'distracted'
    EMOTION = 'emotion'


class ActionItemStatus(str, Enum):
    """Supported states for extracted action items."""

    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class ActionItemPriority(str, Enum):
    """Supported action item priorities."""

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class AudioProcessingStatus(str, Enum):
    """Audio processing states."""

    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class TranscriptStatus(str, Enum):
    """Transcript generation states."""

    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class EmotionLabel(str, Enum):
    """Supported emotion labels from CV/NLP processors."""

    FOCUSED = 'focused'
    ENGAGED = 'engaged'
    NEUTRAL = 'neutral'
    CONFUSED = 'confused'
    DISTRACTED = 'distracted'
    FRUSTRATED = 'frustrated'
    HAPPY = 'happy'
    SAD = 'sad'


EMOTION_SCORES: dict[str, float] = {
    EmotionLabel.FOCUSED.value: 1.0,
    EmotionLabel.ENGAGED.value: 0.95,
    EmotionLabel.HAPPY.value: 0.9,
    EmotionLabel.NEUTRAL.value: 0.75,
    EmotionLabel.CONFUSED.value: 0.45,
    EmotionLabel.DISTRACTED.value: 0.25,
    EmotionLabel.FRUSTRATED.value: 0.2,
    EmotionLabel.SAD.value: 0.2,
}


class EntityType(str, Enum):
    """Named-entity categories produced by NLP."""

    PERSON = 'PERSON'
    ORG = 'ORG'
    GPE = 'GPE'
    LOC = 'LOC'
    DATE = 'DATE'
    TIME = 'TIME'
    MONEY = 'MONEY'
    PERCENT = 'PERCENT'
    PRODUCT = 'PRODUCT'
    EVENT = 'EVENT'
    LAW = 'LAW'
    LANGUAGE = 'LANGUAGE'
    WORK_OF_ART = 'WORK_OF_ART'
    OTHER = 'OTHER'


ENGAGEMENT_WEIGHTS: dict[str, float] = {
    'presence': 0.40,
    'eye_contact': 0.30,
    'participation': 0.20,
    'emotion': 0.10,
}

ENGAGEMENT_THRESHOLDS: dict[str, float] = {
    'low': 40.0,
    'moderate': 65.0,
    'high': 80.0,
    'excellent': 92.0,
}

MAX_SESSION_TITLE_LENGTH = 200
MIN_SESSION_TITLE_LENGTH = 3
MAX_TRANSCRIPT_LENGTH = 250_000
MIN_TRANSCRIPT_LENGTH = 1
MIN_PARTICIPANTS_PER_SESSION = 0
MAX_PARTICIPANTS_PER_SESSION = 500
MAX_PARTICIPANT_NAME_LENGTH = 120
MAX_ACTION_ITEM_LENGTH = 1_000
MAX_SUMMARY_LENGTH = 8_000
MAX_KEYWORD_LENGTH = 80

MIN_ENGAGEMENT_SCORE = 0.0
MAX_ENGAGEMENT_SCORE = 100.0
MIN_PERCENTAGE = 0.0
MAX_PERCENTAGE = 100.0

SUPPORTED_AUDIO_EXTENSIONS: tuple[str, ...] = (
    '.mp3',
    '.wav',
    '.m4a',
    '.flac',
    '.ogg',
)
SUPPORTED_AUDIO_MIME_TYPES: tuple[str, ...] = (
    'audio/mpeg',
    'audio/wav',
    'audio/x-wav',
    'audio/mp4',
    'audio/flac',
    'audio/ogg',
)
MAX_AUDIO_FILE_SIZE_BYTES = 100 * 1024 * 1024
MIN_AUDIO_FILE_SIZE_BYTES = 1024

SUPPORTED_LANGUAGES: dict[str, str] = {
    'en': 'English',
    'hi': 'Hindi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'pt': 'Portuguese',
}
DEFAULT_LANGUAGE = 'en'

HTTP_STATUS_CODES: dict[str, int] = {
    'ok': HTTPStatus.OK,
    'created': HTTPStatus.CREATED,
    'accepted': HTTPStatus.ACCEPTED,
    'bad_request': HTTPStatus.BAD_REQUEST,
    'unauthorized': HTTPStatus.UNAUTHORIZED,
    'forbidden': HTTPStatus.FORBIDDEN,
    'not_found': HTTPStatus.NOT_FOUND,
    'conflict': HTTPStatus.CONFLICT,
    'payload_too_large': HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    'unprocessable_entity': HTTPStatus.UNPROCESSABLE_ENTITY,
    'too_many_requests': HTTPStatus.TOO_MANY_REQUESTS,
    'internal_server_error': HTTPStatus.INTERNAL_SERVER_ERROR,
    'service_unavailable': HTTPStatus.SERVICE_UNAVAILABLE,
}

ERROR_MESSAGES: dict[str, str] = {
    'invalid_email': 'Email address is not valid.',
    'invalid_uuid': 'Invalid UUID format.',
    'invalid_date': 'Invalid ISO-8601 date/time format.',
    'invalid_title': 'Session title is invalid.',
    'invalid_transcript': 'Transcript content is invalid.',
    'invalid_participants': 'Participants payload is invalid.',
    'invalid_score': 'Engagement score must be between 0 and 100.',
    'invalid_emotion': 'Emotion label is not supported.',
    'invalid_status': 'Session status is not supported.',
    'invalid_audio_format': 'Audio format is not supported.',
    'invalid_audio_size': 'Audio file size is outside allowed limits.',
    'invalid_payload': 'Request payload is invalid.',
}

FEATURE_FLAGS: dict[str, bool] = {
    'enable_realtime_transcription': False,
    'enable_multilingual_summaries': False,
    'enable_advanced_ner': True,
    'enable_report_pdf_download': True,
    'enable_emotion_tracking': True,
    'enable_api_audit_logs': True,
}

DEFAULT_PAGINATION_LIMIT = 50
MAX_PAGINATION_LIMIT = 200
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_DATE_FORMAT = '%Y-%m-%d'
DEFAULT_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
REQUEST_ID_HEADER = 'X-Request-ID'

__all__ = [
    'ActionItemPriority',
    'ActionItemStatus',
    'AudioProcessingStatus',
    'DEFAULT_DATE_FORMAT',
    'DEFAULT_DATETIME_FORMAT',
    'DEFAULT_LANGUAGE',
    'DEFAULT_LOG_LEVEL',
    'DEFAULT_PAGINATION_LIMIT',
    'EMOTION_SCORES',
    'ENGAGEMENT_THRESHOLDS',
    'ENGAGEMENT_WEIGHTS',
    'EngagementEventType',
    'EmotionLabel',
    'EntityType',
    'ERROR_MESSAGES',
    'FEATURE_FLAGS',
    'HTTP_STATUS_CODES',
    'MAX_ACTION_ITEM_LENGTH',
    'MAX_AUDIO_FILE_SIZE_BYTES',
    'MAX_ENGAGEMENT_SCORE',
    'MAX_KEYWORD_LENGTH',
    'MAX_PAGINATION_LIMIT',
    'MAX_PARTICIPANT_NAME_LENGTH',
    'MAX_PARTICIPANTS_PER_SESSION',
    'MAX_PERCENTAGE',
    'MAX_SESSION_TITLE_LENGTH',
    'MAX_SUMMARY_LENGTH',
    'MAX_TRANSCRIPT_LENGTH',
    'MIN_AUDIO_FILE_SIZE_BYTES',
    'MIN_ENGAGEMENT_SCORE',
    'MIN_PARTICIPANTS_PER_SESSION',
    'MIN_PERCENTAGE',
    'MIN_SESSION_TITLE_LENGTH',
    'MIN_TRANSCRIPT_LENGTH',
    'NoteStatus',
    'REQUEST_ID_HEADER',
    'SUPPORTED_AUDIO_EXTENSIONS',
    'SUPPORTED_AUDIO_MIME_TYPES',
    'SUPPORTED_LANGUAGES',
    'SessionStatus',
    'TranscriptStatus',
]
