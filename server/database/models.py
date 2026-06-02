from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from database.connection import get_connection, initialize_schema
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
	return {
		'id': row['id'],
		'title': row['title'],
		'context': row['context'],
		'status': row['status'],
		'participants': parse_json(row['participants_json'], []),
		'created_at': row['created_at'],
		'updated_at': row['updated_at'],
		'note_count': note_count,
		'engagement_count': engagement_count,
		'transcript_excerpt': row['transcript'][:240] if row['transcript'] else '',
	}


def note_to_dict(row: sqlite3.Row) -> dict[str, Any]:
	return {
		'id': row['id'],
		'session_id': row['session_id'],
		'title': row['title'],
		'transcript': row['transcript'],
		'summary': row['summary'],
		'key_points': parse_json(row['key_points_json'], []),
		'action_items': parse_json(row['action_items_json'], []),
		'keywords': parse_json(row['keywords_json'], []),
		'created_at': row['created_at'],
	}


def engagement_to_dict(row: sqlite3.Row) -> dict[str, Any]:
	return {
		'id': row['id'],
		'session_id': row['session_id'],
		'participant_name': row['participant_name'],
		'event_type': row['event_type'],
		'score': row['score'],
		'created_at': row['created_at'],
	}


def ensure_database(database_path: str) -> None:
	initialize_schema(database_path)


def create_session(database_path: str, payload: dict[str, Any]) -> dict[str, Any]:
	session_id = generate_id()
	timestamp = utc_now()
	participants = payload.get('participants', [])
	with get_connection(database_path) as connection:
		connection.execute(
			'''
			INSERT INTO sessions (id, title, context, status, participants_json, transcript, created_at, updated_at)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			''',
			(
				session_id,
				payload.get('title', 'Untitled Session'),
				payload.get('context', ''),
				payload.get('status', 'active'),
				normalize_json(participants),
				payload.get('transcript', ''),
				timestamp,
				timestamp,
			),
		)
	return get_session(database_path, session_id)


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
	note_id = generate_id()
	transcript = payload.get('transcript', '')
	artifacts = summarize_transcript(transcript)
	note_title = payload.get('title') or artifacts['summary'][:72]
	timestamp = utc_now()

	with get_connection(database_path) as connection:
		connection.execute(
			'''
			INSERT INTO notes (
				id, session_id, title, transcript, summary,
				key_points_json, action_items_json, keywords_json, created_at
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			''',
			(
				note_id,
				session_id,
				note_title,
				transcript,
				artifacts['summary'],
				normalize_json(artifacts['key_points']),
				normalize_json(artifacts['action_items']),
				normalize_json(artifacts['keywords']),
				timestamp,
			),
		)
		if transcript:
			connection.execute(
				'UPDATE sessions SET transcript = ?, status = ?, updated_at = ? WHERE id = ?',
				(transcript, 'analyzed', timestamp, session_id),
			)

	return get_note(database_path, note_id)


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
	event_id = generate_id()
	timestamp = utc_now()
	with get_connection(database_path) as connection:
		connection.execute(
			'''
			INSERT INTO engagement_events (id, session_id, participant_name, event_type, score, created_at)
			VALUES (?, ?, ?, ?, ?, ?)
			''',
			(
				event_id,
				session_id,
				payload.get('participant_name', 'Participant'),
				payload.get('event_type', 'attended'),
				float(payload.get('score', 0.0)),
				timestamp,
			),
		)
	with get_connection(database_path) as connection:
		row = connection.execute('SELECT * FROM engagement_events WHERE id = ?', (event_id,)).fetchone()
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

