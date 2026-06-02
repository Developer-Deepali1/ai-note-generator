from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from database.mongo import UserRepository
from models.user import User
from utils.logger import get_logger
from utils.validators import ValidationError, sanitize_string, validate_email, validate_language


class AuthenticationError(ValueError):
	pass


class DuplicateUserError(ValueError):
	pass


def validate_password(password: str) -> str:
	if not isinstance(password, str):
		raise ValidationError('Password must be a string.')
	if len(password) < 8:
		raise ValidationError('Password must be at least 8 characters long.')
	if not any(character.isalpha() for character in password):
		raise ValidationError('Password must include at least one letter.')
	if not any(character.isdigit() for character in password):
		raise ValidationError('Password must include at least one number.')
	return password


def hash_password(password: str) -> str:
	validated = validate_password(password)
	return bcrypt.hashpw(validated.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
	if not password or not password_hash:
		return False
	try:
		return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
	except ValueError:
		return False


def create_access_token(user: User, config: dict[str, Any]) -> str:
	now = datetime.now(timezone.utc)
	expires_at = now + timedelta(minutes=int(config['JWT_ACCESS_TOKEN_EXPIRES_MINUTES']))
	payload = {
		'sub': user.id,
		'email': user.email,
		'role': user.role,
		'iat': int(now.timestamp()),
		'exp': int(expires_at.timestamp()),
		'type': 'access',
	}
	return jwt.encode(payload, str(config['JWT_SECRET_KEY']), algorithm=str(config['JWT_ALGORITHM']))


def decode_access_token(token: str, config: dict[str, Any]) -> dict[str, Any]:
	try:
		payload = jwt.decode(
			token,
			str(config['JWT_SECRET_KEY']),
			algorithms=[str(config['JWT_ALGORITHM'])],
			options={'require': ['exp', 'iat', 'sub']},
		)
	except jwt.ExpiredSignatureError as exc:
		raise AuthenticationError('Token has expired.') from exc
	except jwt.InvalidTokenError as exc:
		raise AuthenticationError('Token is invalid.') from exc

	if payload.get('type') != 'access':
		raise AuthenticationError('Token type is invalid.')
	return payload


def register_user(repository: UserRepository, payload: dict[str, Any]) -> User:
	name = sanitize_string(str(payload.get('name') or ''), preserve_newlines=False)
	email = validate_email(str(payload.get('email') or ''))
	password = validate_password(str(payload.get('password') or ''))
	role = sanitize_string(str(payload.get('role') or 'member'), preserve_newlines=False).lower()
	preferred_language = validate_language(payload.get('preferred_language'))

	if not name:
		raise ValidationError('Name is required.')
	if role not in {'member', 'admin'}:
		raise ValidationError('Role must be member or admin.')
	if repository.find_by_email(email):
		raise DuplicateUserError('A user with this email already exists.')

	user = User(
		name=name,
		email=email,
		password_hash=hash_password(password),
		role=role,
		preferred_language=preferred_language,
	)

	try:
		created = repository.create_user(user)
	except ValueError as exc:
		raise DuplicateUserError(str(exc)) from exc

	get_logger(__name__).info('User registered', user_id=created.id, email=created.email)
	return created


def login_user(repository: UserRepository, payload: dict[str, Any]) -> User:
	email = validate_email(str(payload.get('email') or ''))
	password = str(payload.get('password') or '')
	user = repository.find_by_email(email)
	if user is None or not user.is_active or not verify_password(password, user.password_hash):
		raise AuthenticationError('Invalid email or password.')

	repository.update_login_timestamp(user.id)
	refreshed_user = repository.find_by_id(user.id) or user
	get_logger(__name__).info('User logged in', user_id=user.id, email=user.email)
	return refreshed_user
