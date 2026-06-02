from __future__ import annotations

import os

from flask import Flask, jsonify, send_from_directory

from config import Config
from database.models import ensure_database
from routes.analytics import bp as analytics_bp
from routes.audio import bp as audio_bp
from routes.engagement import bp as engagement_bp
from routes.health import bp as health_bp
from routes.notes import bp as notes_bp
from routes.pipeline import bp as pipeline_bp
from routes.sessions import bp as sessions_bp


def create_app(test_config: dict | None = None) -> Flask:
	static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client', 'dist'))
	app = Flask(__name__, static_folder=static_dir, static_url_path='')
	app.config.from_object(Config)
	if test_config:
		app.config.update(test_config)

	@app.after_request
	def add_cors_headers(response):
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
		response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
		return response

	ensure_database(app.config['DATABASE_PATH'])

	app.register_blueprint(health_bp, url_prefix='/api')
	app.register_blueprint(sessions_bp, url_prefix='/api')
	app.register_blueprint(notes_bp, url_prefix='/api')
	app.register_blueprint(engagement_bp, url_prefix='/api')
	app.register_blueprint(pipeline_bp, url_prefix='/api')
	app.register_blueprint(analytics_bp, url_prefix='/api')
	app.register_blueprint(audio_bp, url_prefix='/api')

	# Serve the frontend index.html at the root and provide SPA fallback for client-side routes
	@app.get('/')
	def index():
		if os.path.exists(os.path.join(app.static_folder, 'index.html')):
			return app.send_static_file('index.html')
		return (
			jsonify(
				{
					'name': app.config['API_TITLE'],
					'status': 'running',
					'endpoints': [
						'/api/health',
						'/api/sessions',
						'/api/sessions/<session_id>/notes',
						'/api/engagement/track',
						'/api/pipeline/analyze',
						'/api/analytics/overview',
						'/api/audio/transcribe',
					],
				}
			),
			200,
		)

	@app.route('/<path:path>')
	def spa_fallback(path: str):
		# If a static file exists (assets, JS, CSS), serve it. Otherwise return index.html
		requested = os.path.join(app.static_folder, path)
		if os.path.exists(requested) and os.path.isfile(requested):
			return send_from_directory(app.static_folder, path)
		if os.path.exists(os.path.join(app.static_folder, 'index.html')):
			return app.send_static_file('index.html')
		return jsonify({'error': 'Not found'}), 404

	return app


app = create_app()


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=True)

