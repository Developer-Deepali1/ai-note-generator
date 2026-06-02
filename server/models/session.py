from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from models.user import utc_now
from utils.constants import SessionStatus
from utils.validators import sanitize_string, validate_participants, validate_session_status


def _parse_json_list(value: Any) -> list[Any]:
	if isinstance(value, list):
		return value
	if not value:
		return []
	if isinstance(value, str):
		try:
			parsed = json.loads(value)
		except json.JSONDecodeError:
			return []
		return parsed if isinstance(parsed, list) else []
	return []


@dataclass(slots=True)
class Session:
	id: str = field(default_factory=lambda: str(uuid4()))
	title: str = 'Untitled Session'
	context: str = ''
	status: str = SessionStatus.ACTIVE.value
	participants: list[str] = field(default_factory=list)
	transcript: str = ''
	user_id: str | None = None
	started_at: str | None = None
	ended_at: str | None = None
	created_at: str = field(default_factory=utc_now)
	updated_at: str = field(default_factory=utc_now)
	note_count: int = 0
	engagement_count: int = 0

	@classmethod
	def from_payload(cls, payload: dict[str, Any]) -> 'Session':
		title = sanitize_string(str(payload.get('title') or 'Untitled Session'), preserve_newlines=False)
		context = sanitize_string(str(payload.get('context') or ''), preserve_newlines=True)
		status = validate_session_status(str(payload.get('status') or SessionStatus.ACTIVE.value))
		participants = validate_participants(payload.get('participants', []))
		transcript = sanitize_string(str(payload.get('transcript') or ''), preserve_newlines=True)
		return cls(
			id=str(payload.get('id') or uuid4()),
			title=title,
			context=context,
			status=status,
			participants=participants,
			transcript=transcript,
			user_id=payload.get('user_id'),
			started_at=payload.get('started_at'),
			ended_at=payload.get('ended_at'),
		)

	@classmethod
	def from_row(cls, row: Any, note_count: int = 0, engagement_count: int = 0) -> 'Session | None':
		if row is None:
			return None
		return cls(
			id=str(row['id']),
			title=str(row['title']),
			context=str(row['context'] or ''),
			status=str(row['status']),
			participants=[str(item) for item in _parse_json_list(row['participants_json'])],
			transcript=str(row['transcript'] or ''),
			user_id=row['user_id'] if 'user_id' in row.keys() else None,
			started_at=row['started_at'] if 'started_at' in row.keys() else None,
			ended_at=row['ended_at'] if 'ended_at' in row.keys() else None,
			created_at=str(row['created_at']),
			updated_at=str(row['updated_at']),
			note_count=note_count,
			engagement_count=engagement_count,
		)

	def to_insert_tuple(self) -> tuple[Any, ...]:
		return (
			self.id,
			self.user_id,
			self.title,
			self.context,
			self.status,
			json.dumps(self.participants, ensure_ascii=False),
			self.transcript,
			self.started_at,
			self.ended_at,
			self.created_at,
			self.updated_at,
		)

	def to_dict(self, *, include_transcript: bool = False) -> dict[str, Any]:
		payload = {
			'id': self.id,
			'title': self.title,
			'context': self.context,
			'status': self.status,
			'participants': self.participants,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
			'note_count': self.note_count,
			'engagement_count': self.engagement_count,
			'transcript_excerpt': self.transcript[:240] if self.transcript else '',
		}
		if include_transcript:
			payload['transcript'] = self.transcript
		return payload
