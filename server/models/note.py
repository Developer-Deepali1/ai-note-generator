from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from models.user import utc_now
from utils.validators import sanitize_string


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
class Note:
	id: str = field(default_factory=lambda: str(uuid4()))
	session_id: str = ''
	title: str = 'Generated Notes'
	transcript: str = ''
	summary: str = ''
	key_points: list[str] = field(default_factory=list)
	action_items: list[str] = field(default_factory=list)
	keywords: list[str] = field(default_factory=list)
	confidence_score: float | None = None
	language_code: str = 'en'
	created_at: str = field(default_factory=utc_now)
	updated_at: str = field(default_factory=utc_now)

	@classmethod
	def from_artifacts(
		cls,
		session_id: str,
		payload: dict[str, Any],
		artifacts: dict[str, Any],
	) -> 'Note':
		title = sanitize_string(
			str(payload.get('title') or artifacts.get('summary', 'Generated Notes')[:72] or 'Generated Notes'),
			preserve_newlines=False,
		)
		return cls(
			id=str(payload.get('id') or uuid4()),
			session_id=session_id,
			title=title,
			transcript=sanitize_string(str(payload.get('transcript') or ''), preserve_newlines=True),
			summary=str(artifacts.get('summary') or ''),
			key_points=[str(item) for item in artifacts.get('key_points', [])],
			action_items=[str(item) for item in artifacts.get('action_items', [])],
			keywords=[str(item) for item in artifacts.get('keywords', [])],
			confidence_score=payload.get('confidence_score'),
			language_code=str(payload.get('language_code') or payload.get('language') or 'en'),
		)

	@classmethod
	def from_row(cls, row: Any) -> 'Note | None':
		if row is None:
			return None
		return cls(
			id=str(row['id']),
			session_id=str(row['session_id']),
			title=str(row['title']),
			transcript=str(row['transcript'] or ''),
			summary=str(row['summary'] or ''),
			key_points=[str(item) for item in _parse_json_list(row['key_points_json'])],
			action_items=[str(item) for item in _parse_json_list(row['action_items_json'])],
			keywords=[str(item) for item in _parse_json_list(row['keywords_json'])],
			confidence_score=row['confidence_score'] if 'confidence_score' in row.keys() else None,
			language_code=str(row['language_code']) if 'language_code' in row.keys() else 'en',
			created_at=str(row['created_at']),
			updated_at=str(row['updated_at']) if 'updated_at' in row.keys() else str(row['created_at']),
		)

	def to_insert_tuple(self) -> tuple[Any, ...]:
		return (
			self.id,
			self.session_id,
			self.title,
			self.transcript,
			self.summary,
			json.dumps(self.key_points, ensure_ascii=False),
			json.dumps(self.action_items, ensure_ascii=False),
			json.dumps(self.keywords, ensure_ascii=False),
			self.confidence_score,
			self.language_code,
			self.created_at,
			self.updated_at,
		)

	def to_dict(self) -> dict[str, Any]:
		return {
			'id': self.id,
			'session_id': self.session_id,
			'title': self.title,
			'transcript': self.transcript,
			'summary': self.summary,
			'key_points': self.key_points,
			'action_items': self.action_items,
			'keywords': self.keywords,
			'confidence_score': self.confidence_score,
			'language_code': self.language_code,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
		}
