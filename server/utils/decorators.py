from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import current_app, g, jsonify, request

from modules.auth_service import AuthenticationError, decode_access_token


F = TypeVar('F', bound=Callable[..., Any])


def _extract_bearer_token() -> str | None:
	header = request.headers.get('Authorization', '')
	if not header:
		return None
	parts = header.split()
	if len(parts) != 2 or parts[0].lower() != 'bearer':
		return None
	return parts[1]


def auth_required(*roles: str) -> Callable[[F], F]:
	def decorator(view: F) -> F:
		@wraps(view)
		def wrapped(*args: Any, **kwargs: Any):
			token = _extract_bearer_token()
			if not token:
				return jsonify({'error': 'Authorization bearer token is required.'}), 401

			try:
				claims = decode_access_token(token, current_app.config)
			except AuthenticationError as exc:
				return jsonify({'error': str(exc)}), 401

			repository = current_app.extensions['user_repository']
			user = repository.find_by_id(str(claims['sub']))
			if user is None or not user.is_active:
				return jsonify({'error': 'Authenticated user was not found.'}), 401
			if roles and user.role not in roles:
				return jsonify({'error': 'Insufficient permissions.'}), 403

			g.current_user = user
			g.jwt_claims = claims
			return view(*args, **kwargs)

		return wrapped  # type: ignore[return-value]

	return decorator
