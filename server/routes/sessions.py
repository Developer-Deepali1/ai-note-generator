from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from database.models import create_session, get_session, list_sessions

bp = Blueprint('sessions', __name__)


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


@bp.get('/sessions')
def get_sessions() -> tuple[object, int]:
	return jsonify({'sessions': list_sessions(_database_path())}), 200


@bp.post('/sessions')
def post_session() -> tuple[object, int]:
	payload = request.get_json(silent=True) or {}
	session = create_session(_database_path(), payload)
	return jsonify({'session': session}), 201


@bp.get('/sessions/<session_id>')
def get_single_session(session_id: str):
	session = get_session(_database_path(), session_id)
	if session is None:
		return jsonify({'error': 'session not found'}), 404
	return jsonify({'session': session}), 200

