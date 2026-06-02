from __future__ import annotations

from flask import Blueprint, current_app, jsonify

bp = Blueprint('health', __name__)


@bp.get('/health')
def health() -> tuple[object, int]:
	return (
		jsonify(
			{
				'status': 'ok',
				'service': current_app.config.get('API_TITLE', 'AI Note Generator'),
			}
		),
		200,
	)

