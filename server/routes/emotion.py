from __future__ import annotations

from flask import Blueprint, jsonify, request

import modules.emotion_ai as emotion_ai
from utils.logger import get_logger

bp = Blueprint('emotion', __name__)
_LOGGER = get_logger('ai_note_generator.routes.emotion')


@bp.post('/emotion/webcam')
def analyze_webcam_emotion():
	payload = request.get_json(silent=True) or {}
	frame = payload.get('frame')
	if not isinstance(frame, str) or not frame.strip():
		return jsonify({'error': 'frame is required'}), 400

	try:
		result = emotion_ai.analyze_webcam_frame(frame)
	except emotion_ai.EmotionAnalysisError as exc:
		message = str(exc)
		status_code = 503 if 'unavailable' in message.lower() or 'missing' in message.lower() else 422
		_LOGGER.warning('Webcam emotion analysis rejected.', error=message, status_code=status_code)
		return jsonify({'error': message}), status_code
	except Exception as exc:  # noqa: BLE001 - production boundary
		_LOGGER.exception('Unexpected webcam emotion analysis failure.', error=str(exc))
		return jsonify({'error': 'Unable to analyze webcam emotion.'}), 500

	return jsonify(result), 200