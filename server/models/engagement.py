from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from models.user import utc_now
from utils.constants import EngagementEventType
from utils.validators import sanitize_string


def _coerce_score(score: Any) -> float:
	try:
		value = float(score)
	except (TypeError, ValueError):
		return 0.0
	if value > 1.0:
		value /= 100.0
	return max(0.0, min(1.0, value))


@dataclass(slots=True)
class EngagementEvent:
	id: str = field(default_factory=lambda: str(uuid4()))
	session_id: str = ''
	participant_name: str = 'Participant'
	event_type: str = EngagementEventType.ATTENDED.value
	score: float = 0.0
	participant_id: str | None = None
	emotion_label: str | None = None
	metadata: dict[str, Any] = field(default_factory=dict)
	created_at: str = field(default_factory=utc_now)
	updated_at: str = field(default_factory=utc_now)

	@classmethod
	def from_payload(cls, session_id: str, payload: dict[str, Any]) -> 'EngagementEvent':
		participant_name = sanitize_string(
			str(payload.get('participant_name') or 'Participant'),
			preserve_newlines=False,
		)
		event_type = str(payload.get('event_type') or EngagementEventType.ATTENDED.value).lower()
		allowed = {item.value for item in EngagementEventType}
		if event_type not in allowed:
			event_type = EngagementEventType.ATTENDED.value

		metadata = {
			key: value
			for key, value in payload.items()
			if key
			not in {
				'id',
				'session_id',
				'participant_name',
				'participant_id',
				'event_type',
				'score',
				'emotion',
				'emotion_label',
			}
		}
		return cls(
			id=str(payload.get('id') or uuid4()),
			session_id=session_id,
			participant_name=participant_name,
			participant_id=payload.get('participant_id'),
			event_type=event_type,
			score=_coerce_score(payload.get('score', payload.get('attention_score', 0.0))),
			emotion_label=payload.get('emotion_label') or payload.get('emotion'),
			metadata=metadata,
		)

	@classmethod
	def from_row(cls, row: Any) -> 'EngagementEvent | None':
		if row is None:
			return None
		metadata: dict[str, Any] = {}
		if 'metadata_json' in row.keys() and row['metadata_json']:
			try:
				parsed = json.loads(row['metadata_json'])
				metadata = parsed if isinstance(parsed, dict) else {}
			except json.JSONDecodeError:
				metadata = {}
		return cls(
			id=str(row['id']),
			session_id=str(row['session_id']),
			participant_name=str(row['participant_name']),
			participant_id=row['participant_id'] if 'participant_id' in row.keys() else None,
			event_type=str(row['event_type']),
			score=float(row['score'] or 0.0),
			emotion_label=row['emotion_label'] if 'emotion_label' in row.keys() else None,
			metadata=metadata,
			created_at=str(row['created_at']),
			updated_at=str(row['updated_at']) if 'updated_at' in row.keys() else str(row['created_at']),
		)

	def to_insert_tuple(self) -> tuple[Any, ...]:
		return (
			self.id,
			self.session_id,
			self.participant_name,
			self.participant_id,
			self.event_type,
			self.score,
			self.emotion_label,
			json.dumps(self.metadata, ensure_ascii=False),
			self.created_at,
			self.updated_at,
		)

	def to_dict(self) -> dict[str, Any]:
		return {
			'id': self.id,
			'session_id': self.session_id,
			'participant_name': self.participant_name,
			'participant_id': self.participant_id,
			'event_type': self.event_type,
			'score': self.score,
			'emotion_label': self.emotion_label,
			'metadata': self.metadata,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
		}
