from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from database.models import analytics_overview

bp = Blueprint('analytics', __name__)


def _database_path() -> str:
	return current_app.config['DATABASE_PATH']


@bp.get('/analytics/overview')
def get_overview():
	return jsonify({'overview': analytics_overview(_database_path())}), 200

