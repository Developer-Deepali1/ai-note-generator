from __future__ import annotations

import base64
import binascii
import re
from datetime import datetime, timezone
from typing import Any

from utils.logger import get_logger

try:  # pragma: no cover - optional production dependency
	import numpy as np
except Exception:  # noqa: BLE001 - optional dependency guard
	np = None

try:  # pragma: no cover - optional production dependency
	import cv2
except Exception:  # noqa: BLE001 - optional dependency guard
	cv2 = None

try:  # pragma: no cover - optional production dependency
	from deepface import DeepFace
except Exception:  # noqa: BLE001 - optional dependency guard
	DeepFace = None

_LOGGER = get_logger('ai_note_generator.modules.emotion_ai')
_DATA_URL_PREFIX = re.compile(r'^data:image/[^;]+;base64,', re.IGNORECASE)


class EmotionAnalysisError(RuntimeError):
	"""Raised when webcam emotion analysis cannot be completed."""


def analyze_webcam_frame(frame: str) -> dict[str, Any]:
	"""Analyze a Base64 webcam frame and return the dominant emotion."""
	if cv2 is None or DeepFace is None:
		raise EmotionAnalysisError('DeepFace/OpenCV dependencies are unavailable.')

	image = _decode_base64_frame(frame)
	result = _run_deepface_analysis(image)
	emotion = _extract_emotion_label(result)
	confidence = _extract_confidence(result, emotion)
	timestamp = datetime.now(timezone.utc).isoformat()

	payload = {
		'emotion': emotion,
		'confidence': confidence,
		'source': 'deepface',
		'timestamp': timestamp,
	}
	_LOGGER.info('Webcam emotion analyzed.', emotion=emotion, confidence=confidence)
	return payload


def _decode_base64_frame(frame: str) -> np.ndarray:
	if not isinstance(frame, str) or not frame.strip():
		raise EmotionAnalysisError('frame must be a non-empty base64 string.')
	if np is None or cv2 is None:
		raise EmotionAnalysisError('NumPy/OpenCV dependencies are unavailable.')

	cleaned = _DATA_URL_PREFIX.sub('', frame.strip())
	cleaned = _pad_base64(cleaned)

	try:
		decoded = base64.b64decode(cleaned, validate=True)
	except (ValueError, binascii.Error) as exc:
		raise EmotionAnalysisError('Invalid base64 frame payload.') from exc

	array = np.frombuffer(decoded, dtype=np.uint8)
	array_size = getattr(array, 'size', len(array))
	if array_size == 0:
		raise EmotionAnalysisError('Decoded frame payload is empty.')

	image = cv2.imdecode(array, cv2.IMREAD_COLOR)
	if image is None:
		raise EmotionAnalysisError('Unable to decode webcam frame into an image.')
	return image


def _pad_base64(value: str) -> str:
	missing = len(value) % 4
	if missing:
		value += '=' * (4 - missing)
	return value


def _run_deepface_analysis(image: np.ndarray) -> dict[str, Any]:
	try:
		analysis = DeepFace.analyze(
			image,
			actions=['emotion'],
			detector_backend='opencv',
			enforce_detection=True,
		)
	except Exception as exc:  # noqa: BLE001 - DeepFace raises several exception types
		raise EmotionAnalysisError(_normalize_deepface_error(exc)) from exc

	if isinstance(analysis, list):
		analysis = analysis[0] if analysis else {}

	if not isinstance(analysis, dict):
		raise EmotionAnalysisError('DeepFace returned an unexpected analysis payload.')
	return analysis


def _extract_emotion_label(result: dict[str, Any]) -> str:
	dominant = str(result.get('dominant_emotion') or '').strip().lower()
	if dominant:
		return dominant

	emotions = result.get('emotion')
	if isinstance(emotions, dict) and emotions:
		return max(emotions, key=lambda key: float(emotions.get(key, 0) or 0)).lower()

	raise EmotionAnalysisError('No emotion could be determined from the frame.')


def _extract_confidence(result: dict[str, Any], emotion: str) -> float:
	emotions = result.get('emotion')
	if not isinstance(emotions, dict) or emotion not in emotions:
		return 0.0

	try:
		value = float(emotions[emotion])
	except (TypeError, ValueError):
		return 0.0

	if value > 1:
		value /= 100.0
	return max(0.0, min(value, 1.0))


def _normalize_deepface_error(error: Exception) -> str:
	message = str(error).strip()
	if not message:
		return 'Unable to analyze webcam frame.'

	lowered = message.lower()
	if 'face' in lowered and ('not' in lowered or 'no' in lowered or 'could not' in lowered):
		return 'No face detected in webcam frame.'
	return message