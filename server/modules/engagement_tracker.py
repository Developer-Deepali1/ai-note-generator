"""Enhanced engagement tracking logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.emotion_detector import detect_emotions
from utils.constants import ENGAGEMENT_THRESHOLDS, ENGAGEMENT_WEIGHTS


@dataclass(slots=True)
class ParticipantEngagementMetrics:
    """Atomic engagement metrics represented as normalized fractions [0, 1]."""

    presence: float
    eye_contact: float
    participation: float
    emotion: float



def _coerce_score(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default



def _normalize_score(value: float) -> float:
    return max(0.0, min(1.0, value))



def _classify_percentage(score_pct: float) -> str:
    if score_pct >= ENGAGEMENT_THRESHOLDS['excellent']:
        return 'excellent'
    if score_pct >= ENGAGEMENT_THRESHOLDS['high']:
        return 'high'
    if score_pct >= ENGAGEMENT_THRESHOLDS['moderate']:
        return 'medium'
    return 'low'



def calculate_engagement_score(metrics: ParticipantEngagementMetrics) -> float:
    """Calculate weighted engagement score on a 0-100 scale."""
    weighted = (
        _normalize_score(metrics.presence) * ENGAGEMENT_WEIGHTS['presence']
        + _normalize_score(metrics.eye_contact) * ENGAGEMENT_WEIGHTS['eye_contact']
        + _normalize_score(metrics.participation) * ENGAGEMENT_WEIGHTS['participation']
        + _normalize_score(metrics.emotion) * ENGAGEMENT_WEIGHTS['emotion']
    )
    return round(weighted * 100, 2)



def calculate_group_engagement(participants: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate aggregate metrics for a participant group."""
    if not participants:
        return {'average_score': 0.0, 'highest_score': 0.0, 'lowest_score': 0.0, 'participant_count': 0}

    scores = [float(item.get('engagement_score', 0.0)) for item in participants]
    return {
        'average_score': round(sum(scores) / len(scores), 2),
        'highest_score': round(max(scores), 2),
        'lowest_score': round(min(scores), 2),
        'participant_count': len(scores),
    }



def calculate_engagement_trend(previous_scores: list[float], current_score: float) -> dict[str, Any]:
    """Calculate trend details for real-time or post-session comparisons."""
    if not previous_scores:
        return {'trend': 'stable', 'delta': 0.0}
    baseline = sum(previous_scores) / len(previous_scores)
    delta = round(current_score - baseline, 2)
    if delta > 2:
        trend = 'improving'
    elif delta < -2:
        trend = 'declining'
    else:
        trend = 'stable'
    return {'trend': trend, 'delta': delta}



def analyze_engagement(payload: dict[str, Any], transcript: str = '') -> dict[str, Any]:
    """Analyze individual engagement from face, eye-contact, participation and emotion signals."""
    face_detected = bool(payload.get('face_detected', True))
    presence = _normalize_score(_coerce_score(payload.get('presence_ratio', 1.0 if face_detected else 0.2), 1.0 if face_detected else 0.2))
    eye_contact = _normalize_score(_coerce_score(payload.get('eye_contact', payload.get('eye_contact_score', 0.7)), 0.7))
    participation = _normalize_score(_coerce_score(payload.get('speaking_ratio', payload.get('speech_ratio', 0.6)), 0.6))

    emotion_hint = str(payload.get('emotion', payload.get('sentiment', 'neutral'))).lower()
    emotion_map = {
        'positive': 0.9,
        'happy': 0.9,
        'focused': 0.85,
        'neutral': 0.7,
        'bored': 0.25,
        'sad': 0.35,
        'frustrated': 0.3,
        'distracted': 0.2,
    }
    emotion_score = _normalize_score(_coerce_score(payload.get('emotion_score', emotion_map.get(emotion_hint, 0.65)), 0.65))

    attention_signal = _normalize_score(_coerce_score(payload.get('attention_score', payload.get('score', 0.0)), 0.0))
    if attention_signal > 0:
        participation = _normalize_score((participation + attention_signal) / 2)

    metrics = ParticipantEngagementMetrics(
        presence=presence,
        eye_contact=eye_contact,
        participation=participation,
        emotion=emotion_score,
    )
    engagement_score = calculate_engagement_score(metrics)

    if transcript.strip():
        transcript_bonus = min(3.0, max(0.0, len(transcript.split()) / 150))
        engagement_score = round(min(100.0, engagement_score + transcript_bonus), 2)

    normalized_attention = round(engagement_score / 100, 2)
    emotion_analysis = detect_emotions(transcript, engagement_score=normalized_attention) if transcript else None

    previous_scores = [float(score) for score in payload.get('historical_scores', []) if isinstance(score, (int, float))]
    trend = calculate_engagement_trend(previous_scores, engagement_score)

    return {
        'face_detected': face_detected,
        'face_eye_score': round((presence + eye_contact) / 2, 2),
        'emotion': emotion_hint,
        'emotion_score': round(emotion_score, 2),
        'attention_score': normalized_attention,
        'engagement_score': engagement_score,
        'classification': _classify_percentage(engagement_score),
        'signals': {
            'presence': round(presence, 2),
            'eye_contact': round(eye_contact, 2),
            'participation': round(participation, 2),
            'emotion': round(emotion_score, 2),
        },
        'trend': trend,
        'analysis_mode': 'realtime' if payload.get('realtime', False) else 'post_session',
        'emotion_analysis': emotion_analysis,
    }
