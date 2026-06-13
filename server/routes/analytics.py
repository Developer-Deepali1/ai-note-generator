from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from database.models import analytics_overview
import modules.eye_contact as eye_contact
from utils.logger import get_logger

bp = Blueprint('analytics', __name__)
_LOGGER = get_logger('ai_note_generator.routes.analytics')


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


@bp.get('/analytics/overview')
def get_overview():
	return jsonify({'overview': analytics_overview(_database_path())}), 200


@bp.post('/analytics/eye-contact')
def track_eye_contact():
	payload = request.get_json(silent=True) or {}
	frame = payload.get('frame')
	if not isinstance(frame, str) or not frame.strip():
		return jsonify({'success': False, 'error': 'frame is required'}), 400

	try:
		result = eye_contact.analyze_webcam_frame(frame)
	except eye_contact.EyeContactAnalysisError as exc:
		message = str(exc)
		status_code = 503 if 'unavailable' in message.lower() or 'missing' in message.lower() else 422
		_LOGGER.warning('Eye contact analysis rejected.', error=message, status_code=status_code)
		return jsonify({'success': False, 'error': message}), status_code
	except Exception as exc:  # noqa: BLE001 - production boundary
		_LOGGER.exception('Unexpected eye contact analysis failure.', error=str(exc))
		return jsonify({'success': False, 'error': 'Unable to analyze webcam eye contact.'}), 500

	return jsonify(result), 200

