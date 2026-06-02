from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from modules.auth_service import (
	AuthenticationError,
	DuplicateUserError,
	create_access_token,
	login_user,
	register_user,
)
from utils.decorators import auth_required
from utils.validators import ValidationError

bp = Blueprint('auth', __name__)


def _repository():
	return current_app.extensions['user_repository']


def _auth_response(user, status_code: int):
	token = create_access_token(user, current_app.config)
	return (
		jsonify(
			{
				'user': user.to_public_dict(),
				'access_token': token,
				'token_type': 'Bearer',
				'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES_MINUTES']) * 60,
			}
		),
		status_code,
	)


@bp.post('/auth/register')
def register():
	payload = request.get_json(silent=True) or {}
	try:
		user = register_user(_repository(), payload)
	except DuplicateUserError as exc:
		return jsonify({'error': str(exc)}), 409
	except ValidationError as exc:
		return jsonify({'error': str(exc)}), 400

	return _auth_response(user, 201)


@bp.post('/auth/login')
def login():
	payload = request.get_json(silent=True) or {}
	try:
		user = login_user(_repository(), payload)
	except (AuthenticationError, ValidationError) as exc:
		return jsonify({'error': str(exc)}), 401

	return _auth_response(user, 200)


@bp.get('/auth/me')
@auth_required()
def me():
	return jsonify({'user': g.current_user.to_public_dict()}), 200


@bp.post('/auth/logout')
@auth_required()
def logout():
	return jsonify({'message': 'Logged out successfully.'}), 200
