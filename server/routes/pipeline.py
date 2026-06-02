from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from database.models import create_engagement_event, create_note
from modules.engagement_tracker import analyze_engagement
from modules.nlp_engine import analyze_transcript
from modules.speech_to_text import transcribe_payload

bp = Blueprint('pipeline', __name__)


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


@bp.post('/pipeline/analyze')
def analyze_pipeline():
	payload = request.get_json(silent=True) or {}
	session_id = payload.get('session_id')
	transcription = transcribe_payload(payload)
	transcript = transcription['transcript']
	nlp = analyze_transcript(transcript)['analysis']
	engagement = analyze_engagement(payload, transcript=transcript)
	response: dict[str, object] = {
		'transcription': transcription,
		'transcript': transcript,
		'analysis': nlp,
		'engagement': engagement,
	}

	if payload.get('persist') and session_id:
		note = create_note(
			_database_path(),
			session_id,
			{
				'title': payload.get('title') or nlp['summary'][:72],
				'transcript': transcript,
			},
		)
		tracked_payload = dict(payload)
		tracked_payload.setdefault('score', engagement['attention_score'])
		event = create_engagement_event(_database_path(), session_id, tracked_payload)
		response['note'] = note
		response['event'] = event

	return jsonify(response), 200