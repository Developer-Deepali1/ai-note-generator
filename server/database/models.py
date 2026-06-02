from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from database.connection import get_connection, initialize_schema
from models.engagement import EngagementEvent
from models.note import Note
from models.session import Session
from modules.nlp_engine import summarize_transcript


def utc_now() -> str:
	return datetime.now(timezone.utc).isoformat(timespec='seconds')


def generate_id() -> str:
	return str(uuid.uuid4())


def normalize_json(value: Any) -> str:
	return json.dumps(value, ensure_ascii=False)


def parse_json(value: str | None, default: Any) -> Any:
	if not value:
		return default
	return json.loads(value)


def session_to_dict(row: sqlite3.Row, note_count: int = 0, engagement_count: int = 0) -> dict[str, Any]:
	session = Session.from_row(row, note_count=note_count, engagement_count=engagement_count)
	return session.to_dict() if session else {}


def note_to_dict(row: sqlite3.Row) -> dict[str, Any]:
	note = Note.from_row(row)
	return note.to_dict() if note else {}


def engagement_to_dict(row: sqlite3.Row) -> dict[str, Any]:
	event = EngagementEvent.from_row(row)
	if event is None:
		return {}
	payload = event.to_dict()
	payload.pop('participant_id', None)
	payload.pop('emotion_label', None)
	payload.pop('metadata', None)
	payload.pop('updated_at', None)
	return payload


def ensure_database(database_path: str) -> None:
	initialize_schema(database_path)


def create_session(database_path: str, payload: dict[str, Any]) -> dict[str, Any]:
	session = Session.from_payload(payload)
	with get_connection(database_path) as connection:
		connection.execute(
			'''
			INSERT INTO sessions (
				id, user_id, title, context, status, participants_json, transcript,
				started_at, ended_at, created_at, updated_at
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			''',
			session.to_insert_tuple(),
		)
	return get_session(database_path, session.id)


def list_sessions(database_path: str) -> list[dict[str, Any]]:
	with get_connection(database_path) as connection:
		rows = connection.execute('SELECT * FROM sessions ORDER BY created_at DESC').fetchall()
		note_rows = connection.execute(
			'SELECT session_id, COUNT(*) AS note_count FROM notes GROUP BY session_id'
		).fetchall()
		engagement_rows = connection.execute(
			'SELECT session_id, COUNT(*) AS engagement_count FROM engagement_events GROUP BY session_id'
		).fetchall()

	note_counts = {row['session_id']: row['note_count'] for row in note_rows}
	engagement_counts = {
		row['session_id']: row['engagement_count'] for row in engagement_rows
	}
	return [
		session_to_dict(
			row,
			note_counts.get(row['id'], 0),
			engagement_counts.get(row['id'], 0),
		)
		for row in rows
	]


def get_session(database_path: str, session_id: str) -> dict[str, Any] | None:
	with get_connection(database_path) as connection:
		row = connection.execute('SELECT * FROM sessions WHERE id = ?', (session_id,)).fetchone()
		if row is None:
			return None
		note_count = connection.execute(
			'SELECT COUNT(*) AS count FROM notes WHERE session_id = ?', (session_id,)
		).fetchone()['count']
		engagement_count = connection.execute(
			'SELECT COUNT(*) AS count FROM engagement_events WHERE session_id = ?',
			(session_id,),
		).fetchone()['count']
	return session_to_dict(row, note_count, engagement_count)


def update_session_transcript(database_path: str, session_id: str, transcript: str) -> None:
	with get_connection(database_path) as connection:
		connection.execute(
			'UPDATE sessions SET transcript = ?, status = ?, updated_at = ? WHERE id = ?',
			(transcript, 'active', utc_now(), session_id),
		)


def create_note(database_path: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	transcript = payload.get('transcript', '')
	artifacts = summarize_transcript(transcript)
	note = Note.from_artifacts(session_id, payload, artifacts)

	with get_connection(database_path) as connection:
		connection.execute(
			'''
			INSERT INTO notes (
				id, session_id, title, transcript, summary,
				key_points_json, action_items_json, keywords_json,
				confidence_score, language_code, created_at, updated_at
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			''',
			note.to_insert_tuple(),
		)
		if transcript:
			connection.execute(
				'UPDATE sessions SET transcript = ?, status = ?, updated_at = ? WHERE id = ?',
				(transcript, 'analyzed', note.updated_at, session_id),
			)

	return get_note(database_path, note.id)


def get_note(database_path: str, note_id: str) -> dict[str, Any] | None:
	with get_connection(database_path) as connection:
		row = connection.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
	return note_to_dict(row) if row is not None else None


def list_notes(database_path: str, session_id: str) -> list[dict[str, Any]]:
	with get_connection(database_path) as connection:
		rows = connection.execute(
			'SELECT * FROM notes WHERE session_id = ? ORDER BY created_at DESC',
			(session_id,),
		).fetchall()
	return [note_to_dict(row) for row in rows]


def create_engagement_event(database_path: str, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	event = EngagementEvent.from_payload(session_id, payload)
	with get_connection(database_path) as connection:
		connection.execute(
			'''
			INSERT INTO engagement_events (
				id, session_id, participant_name, participant_id, event_type,
				score, emotion_label, metadata_json, created_at, updated_at
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			''',
			event.to_insert_tuple(),
		)
	with get_connection(database_path) as connection:
		row = connection.execute('SELECT * FROM engagement_events WHERE id = ?', (event.id,)).fetchone()
	return engagement_to_dict(row)


def list_engagement_events(database_path: str, session_id: str) -> list[dict[str, Any]]:
	with get_connection(database_path) as connection:
		rows = connection.execute(
			'SELECT * FROM engagement_events WHERE session_id = ? ORDER BY created_at DESC',
			(session_id,),
		).fetchall()
	return [engagement_to_dict(row) for row in rows]


def analytics_overview(database_path: str) -> dict[str, Any]:
	with get_connection(database_path) as connection:
		session_count = connection.execute('SELECT COUNT(*) AS count FROM sessions').fetchone()['count']
		note_count = connection.execute('SELECT COUNT(*) AS count FROM notes').fetchone()['count']
		engagement_count = connection.execute(
			'SELECT COUNT(*) AS count FROM engagement_events'
		).fetchone()['count']
		average_score_row = connection.execute(
			'SELECT AVG(score) AS average_score FROM engagement_events'
		).fetchone()
		top_participants = connection.execute(
			'''
			SELECT participant_name, COUNT(*) AS events, AVG(score) AS average_score
			FROM engagement_events
			GROUP BY participant_name
			ORDER BY events DESC, average_score DESC
			LIMIT 5
			'''
		).fetchall()

	return {
		'session_count': session_count,
		'note_count': note_count,
		'engagement_event_count': engagement_count,
		'average_engagement_score': round(average_score_row['average_score'] or 0.0, 2),
		'top_participants': [
			{
				'participant_name': row['participant_name'],
				'events': row['events'],
				'average_score': round(row['average_score'] or 0.0, 2),
			}
			for row in top_participants
		],
	}

