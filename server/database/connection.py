from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def _database_path(database_path: str | Path) -> Path:
	path = Path(database_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	return path


@contextmanager
def get_connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
	path = _database_path(database_path)
	connection = sqlite3.connect(path)
	connection.row_factory = sqlite3.Row
	connection.execute('PRAGMA foreign_keys = ON')
	try:
		yield connection
		connection.commit()
	finally:
		connection.close()


def initialize_schema(database_path: str | Path) -> None:
	schema = Path(__file__).resolve().parent / 'migrations' / 'init.sql'
	with get_connection(database_path) as connection:
		connection.executescript(schema.read_text(encoding='utf-8'))

