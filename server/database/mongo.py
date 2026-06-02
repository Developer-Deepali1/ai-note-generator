from __future__ import annotations

from typing import Any, Protocol

from models.user import User, utc_now
from utils.logger import get_logger


class UserRepository(Protocol):
	def create_user(self, user: User) -> User: ...
	def find_by_email(self, email: str) -> User | None: ...
	def find_by_id(self, user_id: str) -> User | None: ...
	def update_login_timestamp(self, user_id: str) -> None: ...


class InMemoryUserRepository:
	def __init__(self) -> None:
		self._users_by_id: dict[str, dict[str, Any]] = {}
		self._ids_by_email: dict[str, str] = {}

	def create_user(self, user: User) -> User:
		email_key = user.email.casefold()
		if email_key in self._ids_by_email:
			raise ValueError('A user with this email already exists.')
		document = user.to_document()
		self._users_by_id[user.id] = document
		self._ids_by_email[email_key] = user.id
		return User.from_dict(document)  # type: ignore[return-value]

	def find_by_email(self, email: str) -> User | None:
		user_id = self._ids_by_email.get(email.casefold())
		if not user_id:
			return None
		return User.from_dict(self._users_by_id.get(user_id))

	def find_by_id(self, user_id: str) -> User | None:
		return User.from_dict(self._users_by_id.get(user_id))

	def update_login_timestamp(self, user_id: str) -> None:
		document = self._users_by_id.get(user_id)
		if document:
			timestamp = utc_now()
			document['last_login_at'] = timestamp
			document['updated_at'] = timestamp


class MongoUserRepository:
	def __init__(self, mongo_uri: str, database_name: str, collection_name: str) -> None:
		try:
			from pymongo import ASCENDING, MongoClient
			from pymongo.errors import DuplicateKeyError
		except ImportError as exc:
			raise RuntimeError(
				'pymongo is required for MongoDB authentication. Install server requirements first.'
			) from exc

		self._duplicate_key_error = DuplicateKeyError
		self._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
		self._collection = self._client[database_name][collection_name]
		self._collection.create_index([('email', ASCENDING)], unique=True)
		self._collection.create_index([('id', ASCENDING)], unique=True)
		get_logger(__name__).info('MongoDB user repository initialized', database=database_name)

	def create_user(self, user: User) -> User:
		try:
			self._collection.insert_one(user.to_document())
		except self._duplicate_key_error as exc:
			raise ValueError('A user with this email already exists.') from exc
		return user

	def find_by_email(self, email: str) -> User | None:
		return User.from_dict(self._collection.find_one({'email': email.casefold()}))

	def find_by_id(self, user_id: str) -> User | None:
		return User.from_dict(self._collection.find_one({'id': user_id}))

	def update_login_timestamp(self, user_id: str) -> None:
		timestamp = utc_now()
		self._collection.update_one(
			{'id': user_id},
			{'$set': {'last_login_at': timestamp, 'updated_at': timestamp}},
		)


def create_user_repository(config: dict[str, Any]) -> UserRepository:
	if config.get('TESTING'):
		return InMemoryUserRepository()
	return MongoUserRepository(
		str(config['MONGO_URI']),
		str(config['MONGO_DATABASE']),
		str(config['MONGO_USERS_COLLECTION']),
	)
