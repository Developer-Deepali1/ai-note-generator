from __future__ import annotations

from modules.auth_service import hash_password, verify_password


def _registration_payload(email: str = 'ava@example.com') -> dict[str, str]:
	return {
		'name': 'Ava Patel',
		'email': email,
		'password': 'StrongPass123',
	}


def test_password_hashing_uses_bcrypt():
	password_hash = hash_password('StrongPass123')

	assert password_hash.startswith('$2')
	assert verify_password('StrongPass123', password_hash) is True
	assert verify_password('wrong-password', password_hash) is False


def test_user_can_register_login_and_fetch_profile(client):
	register_response = client.post('/api/auth/register', json=_registration_payload())
	register_payload = register_response.get_json()

	assert register_response.status_code == 201
	assert register_payload['user']['email'] == 'ava@example.com'
	assert 'password_hash' not in register_payload['user']
	assert register_payload['access_token']

	me_response = client.get(
		'/api/auth/me',
		headers={'Authorization': f"Bearer {register_payload['access_token']}"},
	)
	assert me_response.status_code == 200
	assert me_response.get_json()['user']['email'] == 'ava@example.com'

	login_response = client.post(
		'/api/auth/login',
		json={'email': 'ava@example.com', 'password': 'StrongPass123'},
	)
	assert login_response.status_code == 200
	assert login_response.get_json()['access_token']


def test_registration_rejects_duplicate_email(client):
	client.post('/api/auth/register', json=_registration_payload())
	duplicate_response = client.post('/api/auth/register', json=_registration_payload())

	assert duplicate_response.status_code == 409


def test_login_rejects_invalid_credentials(client):
	client.post('/api/auth/register', json=_registration_payload())
	response = client.post(
		'/api/auth/login',
		json={'email': 'ava@example.com', 'password': 'WrongPass123'},
	)

	assert response.status_code == 401


def test_auth_middleware_rejects_missing_and_invalid_token(client):
	missing_response = client.get('/api/auth/me')
	invalid_response = client.get(
		'/api/auth/me',
		headers={'Authorization': 'Bearer not-a-real-token'},
	)

	assert missing_response.status_code == 401
	assert invalid_response.status_code == 401
