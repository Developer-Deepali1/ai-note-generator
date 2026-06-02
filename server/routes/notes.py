from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from database.models import create_note, list_notes

bp = Blueprint('notes', __name__)


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


@bp.get('/sessions/<session_id>/notes')
def get_session_notes(session_id: str):
	return jsonify({'notes': list_notes(_database_path(), session_id)}), 200


@bp.post('/sessions/<session_id>/notes')
def post_session_note(session_id: str):
	payload = request.get_json(silent=True) or {}
	note = create_note(_database_path(), session_id, payload)
	return jsonify({'note': note}), 201

