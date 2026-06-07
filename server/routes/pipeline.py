from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, jsonify, request

from database.models import create_engagement_event, create_note
from modules.engagement_tracker import analyze_engagement
from modules.gemini_service import generate_meeting_notes
from modules.nlp_engine import analyze_transcript
from modules.speech_to_text import transcribe_payload
from utils.logger import get_logger

bp = Blueprint('pipeline', __name__)
_LOGGER = get_logger('ai_note_generator.routes.pipeline')

_REQUIRED_RESPONSE_KEYS = {'transcription', 'transcript', 'analysis', 'engagement'}
_REQUIRED_ANALYSIS_KEYS = {'summary', 'key_points', 'action_items', 'keywords', 'entities', 'metadata'}


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


def _build_analysis_payload(transcript: str) -> dict[str, Any]:
	legacy_analysis = analyze_transcript(transcript)['analysis']
	try:
		gemini_notes = generate_meeting_notes(transcript)
	except Exception as exc:  # noqa: BLE001 - production boundary
		_LOGGER.error('Gemini analysis failed; falling back to rule-based NLP.', error=str(exc))
		return legacy_analysis

	if not _is_meaningful_gemini_payload(gemini_notes):
		_LOGGER.warning('Gemini returned an empty or invalid payload; using fallback NLP.')
		return legacy_analysis

	merged = {
		**legacy_analysis,
		'summary': _coerce_summary(gemini_notes.get('summary'), legacy_analysis.get('summary', '')),
		'key_points': _merge_unique_text_lists(
			gemini_notes.get('key_points'), legacy_analysis.get('key_points', [])
		),
		'action_items': _merge_unique_text_lists(
			gemini_notes.get('action_items'), legacy_analysis.get('action_items', [])
		),
	}

	if not _is_valid_analysis_payload(merged):
		_LOGGER.warning('Merged Gemini analysis failed validation; using fallback NLP.')
		return legacy_analysis

	return merged


def _is_meaningful_gemini_payload(payload: dict[str, Any]) -> bool:
	if not isinstance(payload, dict):
		return False
	summary = str(payload.get('summary') or '').strip()
	if summary:
		return True
	return any(_normalize_text_list(payload.get(key)) for key in ('key_points', 'action_items'))


def _is_valid_analysis_payload(payload: dict[str, Any]) -> bool:
	if not isinstance(payload, dict):
		return False
	if not _REQUIRED_ANALYSIS_KEYS.issubset(payload.keys()):
		return False
	if not isinstance(payload.get('summary'), str):
		return False
	if not isinstance(payload.get('key_points'), list):
		return False
	if not isinstance(payload.get('action_items'), list):
		return False
	if not isinstance(payload.get('keywords'), list):
		return False
	if not isinstance(payload.get('entities'), list):
		return False
	if not isinstance(payload.get('metadata'), dict):
		return False
	return True


def _build_response_payload(
	transcription: dict[str, Any],
	transcript: str,
	analysis: dict[str, Any],
	engagement: dict[str, Any],
) -> dict[str, Any]:
	response: dict[str, Any] = {
		'transcription': transcription,
		'transcript': transcript,
		'analysis': analysis,
		'engagement': engagement,
	}
	if not _REQUIRED_RESPONSE_KEYS.issubset(response.keys()):
		raise ValueError('Pipeline response payload is missing required keys.')
	return response


def _normalize_text_list(value: Any) -> list[str]:
	if value is None:
		return []
	if isinstance(value, str):
		text = value.strip()
		return [text] if text else []
	if not isinstance(value, list):
		return []
	items: list[str] = []
	for item in value:
		text = str(item).strip()
		if text:
			items.append(text)
	return items


def _merge_unique_text_lists(primary: Any, fallback: list[str]) -> list[str]:
	merged: list[str] = []
	seen: set[str] = set()
	for value in _normalize_text_list(primary):
		normalized = value.casefold()
		if normalized not in seen:
			seen.add(normalized)
			merged.append(value)
	for value in fallback:
		normalized = str(value).strip().casefold()
		if normalized and normalized not in seen:
			seen.add(normalized)
			merged.append(str(value).strip())
	return merged


def _coerce_summary(primary: Any, fallback: str) -> str:
	summary = str(primary or '').strip()
	return summary or str(fallback or '').strip()


@bp.post('/pipeline/analyze')
def analyze_pipeline():
	payload = request.get_json(silent=True) or {}
	session_id = payload.get('session_id')
	transcription = transcribe_payload(payload)
	transcript = transcription['transcript']
	analysis = _build_analysis_payload(transcript)
	engagement = analyze_engagement(payload, transcript=transcript)
	response = _build_response_payload(transcription, transcript, analysis, engagement)

	if payload.get('persist') and session_id:
		note = create_note(
			_database_path(),
			session_id,
			{
				'title': payload.get('title') or analysis['summary'][:72],
				'transcript': transcript,
			},
		)
		tracked_payload = dict(payload)
		tracked_payload.setdefault('score', engagement['attention_score'])
		event = create_engagement_event(_database_path(), session_id, tracked_payload)
		response['note'] = note
		response['event'] = event

	if not _validate_pipeline_response(response):
		_LOGGER.error('Pipeline response validation failed; returning safe fallback payload.')
		response = {
			'transcription': transcription,
			'transcript': transcript,
			'analysis': analyze_transcript(transcript)['analysis'],
			'engagement': engagement,
		}

	return jsonify(response), 200


def _validate_pipeline_response(response: dict[str, Any]) -> bool:
	if not isinstance(response, dict):
		return False
	if not _REQUIRED_RESPONSE_KEYS.issubset(response.keys()):
		return False
	return _is_valid_analysis_payload(response['analysis'])