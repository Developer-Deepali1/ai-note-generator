from __future__ import annotations

from typing import Any


def _coerce_score(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _normalize_score(value: float) -> float:
	return max(0.0, min(1.0, value))


def analyze_engagement(payload: dict[str, Any], transcript: str = '') -> dict[str, Any]:
	face_detected = bool(payload.get('face_detected', True))
	eye_contact = _coerce_score(payload.get('eye_contact', payload.get('eye_contact_score', 0.7)), 0.7)
	emotion = str(payload.get('emotion', payload.get('sentiment', 'neutral'))).lower()
	speaking = _coerce_score(payload.get('speaking_ratio', payload.get('speech_ratio', 0.6)), 0.6)
	attenuation = _coerce_score(payload.get('attention_score', payload.get('score', 0.0)), 0.0)

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
	emotion_score = emotion_map.get(emotion, 0.65)

	face_score = 1.0 if face_detected else 0.2
	eye_score = _normalize_score(eye_contact)
	speaking_score = _normalize_score(speaking)

	composite = (
		face_score * 0.25
		+ eye_score * 0.3
		+ emotion_score * 0.2
		+ speaking_score * 0.15
		+ _normalize_score(attenuation) * 0.1
	)
	composite = _normalize_score(composite)

	if transcript.strip():
		composite = _normalize_score(min(1.0, composite + 0.05))

	return {
		'face_detected': face_detected,
		'face_eye_score': round((face_score + eye_score) / 2, 2),
		'emotion': emotion,
		'emotion_score': round(emotion_score, 2),
		'attention_score': round(composite, 2),
		'classification': 'high' if composite >= 0.75 else 'medium' if composite >= 0.45 else 'low',
		'signals': {
			'eye_contact': round(eye_score, 2),
			'speaking_ratio': round(speaking_score, 2),
		},
	}
