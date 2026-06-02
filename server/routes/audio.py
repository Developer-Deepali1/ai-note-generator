from __future__ import annotations

from flask import Blueprint, jsonify, request

from modules.nlp_engine import analyze_transcript, summarize_transcript
from modules.speech_to_text import transcribe_payload

bp = Blueprint('audio', __name__)


@bp.post('/audio/transcribe')
def transcribe_audio():
	payload = request.get_json(silent=True) or {}
	transcription = transcribe_payload(payload)
	transcript = transcription['transcript']
	nlp_artifacts = analyze_transcript(transcript)['analysis']
	return (
		jsonify(
			{
				'transcription': transcription,
				'transcript': transcript,
				'summary': nlp_artifacts['summary'],
				'key_points': nlp_artifacts['key_points'],
				'action_items': nlp_artifacts['action_items'],
				'keywords': nlp_artifacts['keywords'],
			}
		),
		200,
	)

