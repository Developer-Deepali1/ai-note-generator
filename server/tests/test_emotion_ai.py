from __future__ import annotations

import base64

import pytest

import modules.emotion_ai as emotion_ai


VALID_FRAME = base64.b64encode(b'frame-bytes').decode('ascii')


class _FakeCv2:
	IMREAD_COLOR = 1

	@staticmethod
	def imdecode(array, flag):
		return object()


class _FakeNumpy:
	uint8 = object()

	@staticmethod
	def frombuffer(decoded, dtype):
		return [1, 2, 3]


class _FakeDeepFace:
	@staticmethod
	def analyze(image, actions, detector_backend, enforce_detection):
		assert actions == ['emotion']
		assert detector_backend == 'opencv'
		assert enforce_detection is True
		return {
			'dominant_emotion': 'happy',
			'emotion': {'happy': 93.0, 'neutral': 7.0},
		}


def test_analyze_webcam_frame_returns_normalized_emotion(monkeypatch):
	monkeypatch.setattr(emotion_ai, 'np', _FakeNumpy)
	monkeypatch.setattr(emotion_ai, 'cv2', _FakeCv2)
	monkeypatch.setattr(emotion_ai, 'DeepFace', _FakeDeepFace)

	result = emotion_ai.analyze_webcam_frame(f'data:image/jpeg;base64,{VALID_FRAME}')

	assert result['emotion'] == 'happy'
	assert result['confidence'] == pytest.approx(0.93, rel=1e-3)
	assert result['source'] == 'deepface'
	assert result['timestamp']


def test_emotion_webcam_endpoint_rejects_missing_frame(client):
	response = client.post('/api/emotion/webcam', json={})

	assert response.status_code == 400
	assert response.get_json()['error'] == 'frame is required'


def test_emotion_webcam_endpoint_returns_success_payload(client, monkeypatch):
	monkeypatch.setattr(
		emotion_ai,
		'analyze_webcam_frame',
		lambda frame: {
			'emotion': 'happy',
			'confidence': 0.93,
			'source': 'deepface',
			'timestamp': '2026-06-08T12:00:00+00:00',
		},
	)

	response = client.post('/api/emotion/webcam', json={'frame': VALID_FRAME})
	payload = response.get_json()

	assert response.status_code == 200
	assert payload == {
		'emotion': 'happy',
		'confidence': 0.93,
		'source': 'deepface',
		'timestamp': '2026-06-08T12:00:00+00:00',
	}


def test_emotion_webcam_endpoint_handles_analysis_errors(client, monkeypatch):
	monkeypatch.setattr(
		emotion_ai,
		'analyze_webcam_frame',
		lambda frame: (_ for _ in ()).throw(emotion_ai.EmotionAnalysisError('No face detected in webcam frame.')),
	)

	response = client.post('/api/emotion/webcam', json={'frame': VALID_FRAME})

	assert response.status_code == 422
	assert response.get_json()['error'] == 'No face detected in webcam frame.'