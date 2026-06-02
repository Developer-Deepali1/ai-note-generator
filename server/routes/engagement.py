from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from database.models import create_engagement_event, list_engagement_events
from modules.engagement_tracker import analyze_engagement

bp = Blueprint('engagement', __name__)


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


@bp.get('/sessions/<session_id>/engagement')
def get_session_engagement(session_id: str):
	return jsonify({'events': list_engagement_events(_database_path(), session_id)}), 200


@bp.post('/engagement/track')
def track_engagement():
	payload = request.get_json(silent=True) or {}
	session_id = payload.get('session_id')
	if not session_id:
		return jsonify({'error': 'session_id is required'}), 400
	analysis = analyze_engagement(payload, transcript=str(payload.get('transcript', '')))
	tracked_payload = dict(payload)
	tracked_payload.setdefault('score', analysis['attention_score'])
	event = create_engagement_event(_database_path(), session_id, tracked_payload)
	return jsonify({'event': event, 'analysis': analysis}), 201

