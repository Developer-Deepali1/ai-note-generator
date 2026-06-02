from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
	return datetime.now(timezone.utc).isoformat(timespec='seconds')


@dataclass(slots=True)
class User:
	id: str = field(default_factory=lambda: str(uuid4()))
	name: str = ''
	email: str = ''
	password_hash: str = ''
	role: str = 'member'
	is_active: bool = True
	preferred_language: str = 'en'
	last_login_at: str | None = None
	created_at: str = field(default_factory=utc_now)
	updated_at: str = field(default_factory=utc_now)

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> 'User | None':
		if not payload:
			return None
		return cls(
			id=str(payload.get('id') or payload.get('_id') or uuid4()),
			name=str(payload.get('name') or ''),
			email=str(payload.get('email') or ''),
			password_hash=str(payload.get('password_hash') or ''),
			role=str(payload.get('role') or 'member'),
			is_active=bool(payload.get('is_active', True)),
			preferred_language=str(payload.get('preferred_language') or 'en'),
			last_login_at=payload.get('last_login_at'),
			created_at=str(payload.get('created_at') or utc_now()),
			updated_at=str(payload.get('updated_at') or utc_now()),
		)

	def to_document(self) -> dict[str, Any]:
		return {
			'id': self.id,
			'name': self.name,
			'email': self.email,
			'password_hash': self.password_hash,
			'role': self.role,
			'is_active': self.is_active,
			'preferred_language': self.preferred_language,
			'last_login_at': self.last_login_at,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
		}

	def to_public_dict(self) -> dict[str, Any]:
		return {
			'id': self.id,
			'name': self.name,
			'email': self.email,
			'role': self.role,
			'is_active': self.is_active,
			'preferred_language': self.preferred_language,
			'last_login_at': self.last_login_at,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
		}
