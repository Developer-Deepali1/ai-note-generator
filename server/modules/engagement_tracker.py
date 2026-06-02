from __future__ import annotations

import re
from statistics import mean
from typing import Any

from utils.constants import EMOTION_SCORES, ENGAGEMENT_THRESHOLDS, ENGAGEMENT_WEIGHTS


def _coerce_score(value: Any, default: float = 0.0) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    if score > 1.0:
        score = score / 100.0
    return _normalize_score(score)


def _normalize_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'1', 'true', 'yes', 'y', 'present', 'detected'}:
            return True
        if normalized in {'0', 'false', 'no', 'n', 'absent', 'missing'}:
            return False
    return default


def _extract_series(payload: dict[str, Any], keys: tuple[str, ...]) -> list[float]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [_coerce_score(item) for item in value]
    return []


def _presence_score(payload: dict[str, Any]) -> float:
    face_series = _extract_series(payload, ('face_detected_samples', 'presence_samples'))
    if face_series:
        return mean(face_series)

    face_detected = _coerce_bool(payload.get('face_detected', payload.get('present')), True)
    if face_detected:
        return 1.0
    return 0.2


def _eye_contact_score(payload: dict[str, Any]) -> float:
    samples = _extract_series(payload, ('eye_contact_samples', 'gaze_samples'))
    if samples:
        return mean(samples)
    return _coerce_score(payload.get('eye_contact', payload.get('eye_contact_score', 0.7)), 0.7)


def _participation_score(payload: dict[str, Any], transcript: str) -> float:
    explicit = payload.get('participation_score', payload.get('participation'))
    if explicit is not None:
        return _coerce_score(explicit)

    speaking = _coerce_score(payload.get('speaking_ratio', payload.get('speech_ratio', 0.0)), 0.0)
    chat = _coerce_score(payload.get('chat_activity', payload.get('message_ratio', 0.0)), 0.0)
    questions = _coerce_score(payload.get('question_ratio', payload.get('questions_asked', 0.0)), 0.0)

    transcript_boost = 0.0
    if transcript.strip():
        participant_name = str(payload.get('participant_name', '')).strip()
        if participant_name:
            turns = len(re.findall(rf'^\s*{re.escape(participant_name)}\s*:', transcript, flags=re.I | re.M))
            transcript_boost = min(0.25, turns * 0.05)
        else:
            transcript_boost = 0.1

    if speaking == 0.0 and chat == 0.0 and questions == 0.0 and transcript_boost == 0.0:
        return 0.6

    return _normalize_score((speaking * 0.65) + (chat * 0.2) + (questions * 0.15) + transcript_boost)


def _emotion_score(payload: dict[str, Any]) -> tuple[str, float]:
    emotion = str(payload.get('emotion', payload.get('sentiment', 'neutral')) or 'neutral').lower()
    aliases = {
        'positive': 'happy',
        'attentive': 'focused',
        'confused': 'confused',
        'negative': 'frustrated',
    }
    normalized = aliases.get(emotion, emotion)
    return normalized, _normalize_score(EMOTION_SCORES.get(normalized, 0.65))


def _classification(score: float) -> str:
    percentage = score * 100.0
    if percentage >= ENGAGEMENT_THRESHOLDS['excellent']:
        return 'excellent'
    if percentage >= ENGAGEMENT_THRESHOLDS['high']:
        return 'high'
    if percentage >= ENGAGEMENT_THRESHOLDS['moderate']:
        return 'medium'
    return 'low'


def analyze_engagement(payload: dict[str, Any], transcript: str = '') -> dict[str, Any]:
    presence = _presence_score(payload)
    eye_contact = _eye_contact_score(payload)
    participation = _participation_score(payload, transcript)
    emotion, emotion_score = _emotion_score(payload)
    supplied_attention = payload.get('attention_score', payload.get('score'))

    weighted_score = (
        presence * ENGAGEMENT_WEIGHTS['presence']
        + eye_contact * ENGAGEMENT_WEIGHTS['eye_contact']
        + participation * ENGAGEMENT_WEIGHTS['participation']
        + emotion_score * ENGAGEMENT_WEIGHTS['emotion']
    )

    if supplied_attention is not None:
        weighted_score = (weighted_score * 0.85) + (_coerce_score(supplied_attention) * 0.15)

    weighted_score = _normalize_score(weighted_score)
    face_detected = presence >= 0.5

    return {
        'face_detected': face_detected,
        'face_eye_score': round((presence + eye_contact) / 2, 2),
        'emotion': emotion,
        'emotion_score': round(emotion_score, 2),
        'attention_score': round(weighted_score, 2),
        'attention_score_percent': round(weighted_score * 100, 1),
        'classification': _classification(weighted_score),
        'signals': {
            'presence': round(presence, 2),
            'eye_contact': round(eye_contact, 2),
            'speaking_ratio': round(_coerce_score(payload.get('speaking_ratio', payload.get('speech_ratio', 0.0))), 2),
            'participation': round(participation, 2),
        },
        'weights': ENGAGEMENT_WEIGHTS,
    }
