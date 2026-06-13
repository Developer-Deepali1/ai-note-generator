from __future__ import annotations

from base64 import b64encode
from types import SimpleNamespace

import pytest

import modules.eye_contact as eye_contact


VALID_FRAME = b64encode(b'frame-bytes').decode('ascii')


class _FakeImage:
	shape = (480, 640, 3)


class _FakeFaceMeshResult:
	def __init__(self, faces):
		self.multi_face_landmarks = faces


class _FakeFaceMesh:
	def __init__(self, faces):
		self._faces = faces

	def process(self, image):
		return _FakeFaceMeshResult(self._faces)


def _make_landmarks(points: dict[int, tuple[float, float]]) -> list[SimpleNamespace]:
	landmarks = [SimpleNamespace(x=0.5, y=0.5, z=0.0) for _ in range(478)]
	for index, coordinates in points.items():
		landmarks[index] = SimpleNamespace(x=coordinates[0], y=coordinates[1], z=0.0)
	return landmarks


def _make_face_landmarks(points: dict[int, tuple[float, float]]) -> SimpleNamespace:
	return SimpleNamespace(landmark=_make_landmarks(points))


def test_analyze_webcam_frame_detects_center_gaze(monkeypatch):
	monkeypatch.setattr(eye_contact, 'np', SimpleNamespace())
	monkeypatch.setattr(eye_contact, 'mp', SimpleNamespace())
	monkeypatch.setattr(eye_contact, 'cv2', SimpleNamespace(COLOR_BGR2RGB=1, cvtColor=lambda image, code: image))
	monkeypatch.setattr(eye_contact, '_decode_base64_frame', lambda frame: _FakeImage())
	monkeypatch.setattr(eye_contact, '_resize_frame', lambda image: image)
	monkeypatch.setattr(
		eye_contact,
		'_create_face_mesh',
		lambda: _FakeFaceMesh([
			_make_face_landmarks(
				{
					1: (0.50, 0.38),
					152: (0.50, 0.78),
					33: (0.32, 0.42),
					263: (0.68, 0.42),
					61: (0.42, 0.70),
					291: (0.58, 0.70),
					159: (0.36, 0.38),
					145: (0.36, 0.46),
					386: (0.64, 0.38),
					374: (0.64, 0.46),
					468: (0.49, 0.42),
					469: (0.50, 0.42),
					470: (0.51, 0.42),
					471: (0.50, 0.43),
					472: (0.49, 0.43),
					473: (0.51, 0.42),
					474: (0.52, 0.42),
					475: (0.53, 0.42),
					476: (0.52, 0.43),
					477: (0.51, 0.43),
				}
			),
		]),
	)
	monkeypatch.setattr(eye_contact, '_estimate_head_pose', lambda landmarks, width, height: ('forward', 0.0, 0.0, 0.0))

	result = eye_contact.analyze_webcam_frame(f'data:image/jpeg;base64,{VALID_FRAME}')

	assert result['success'] is True
	assert result['face_detected'] is True
	assert result['eye_contact'] is True
	assert result['gaze_direction'] == 'center'
	assert result['head_pose'] == 'forward'
	assert result['eye_contact_score'] > 0
	assert result['session_stats']['total_frames'] == 1
	assert result['session_stats']['eye_contact_frames'] == 1


def test_analyze_webcam_frame_marks_off_screen_gaze(monkeypatch):
	monkeypatch.setattr(eye_contact, 'np', SimpleNamespace())
	monkeypatch.setattr(eye_contact, 'mp', SimpleNamespace())
	monkeypatch.setattr(eye_contact, 'cv2', SimpleNamespace(COLOR_BGR2RGB=1, cvtColor=lambda image, code: image))
	monkeypatch.setattr(eye_contact, '_decode_base64_frame', lambda frame: _FakeImage())
	monkeypatch.setattr(eye_contact, '_resize_frame', lambda image: image)
	monkeypatch.setattr(
		eye_contact,
		'_create_face_mesh',
		lambda: _FakeFaceMesh([
			_make_face_landmarks(
				{
					1: (0.50, 0.38),
					152: (0.50, 0.78),
					33: (0.32, 0.42),
					263: (0.68, 0.42),
					61: (0.42, 0.70),
					291: (0.58, 0.70),
					159: (0.36, 0.38),
					145: (0.36, 0.46),
					386: (0.64, 0.38),
					374: (0.64, 0.46),
					468: (0.34, 0.42),
					469: (0.35, 0.42),
					470: (0.36, 0.42),
					471: (0.35, 0.43),
					472: (0.34, 0.43),
					473: (0.66, 0.42),
					474: (0.67, 0.42),
					475: (0.68, 0.42),
					476: (0.67, 0.43),
					477: (0.66, 0.43),
				}
			),
		]),
	)
	monkeypatch.setattr(eye_contact, '_estimate_head_pose', lambda landmarks, width, height: ('forward', 0.0, 0.0, 0.0))
	monkeypatch.setattr(eye_contact, '_classify_gaze', lambda left_eye, right_eye, head_pose, yaw, pitch: ('left', 0.18))

	result = eye_contact.analyze_webcam_frame(f'data:image/jpeg;base64,{VALID_FRAME}')

	assert result['success'] is True
	assert result['face_detected'] is True
	assert result['eye_contact'] is False
	assert result['gaze_direction'] == 'left'
	assert result['analysis_status'] == 'off_screen'
	assert result['session_stats']['total_frames'] == 1
	assert result['session_stats']['off_screen_frames'] == 1


def test_analyze_webcam_frame_handles_no_face(monkeypatch):
	monkeypatch.setattr(eye_contact, 'np', SimpleNamespace())
	monkeypatch.setattr(eye_contact, 'mp', SimpleNamespace())
	monkeypatch.setattr(eye_contact, 'cv2', SimpleNamespace(COLOR_BGR2RGB=1, cvtColor=lambda image, code: image))
	monkeypatch.setattr(eye_contact, '_decode_base64_frame', lambda frame: _FakeImage())
	monkeypatch.setattr(eye_contact, '_resize_frame', lambda image: image)
	monkeypatch.setattr(eye_contact, '_create_face_mesh', lambda: _FakeFaceMesh([]))

	result = eye_contact.analyze_webcam_frame(f'data:image/jpeg;base64,{VALID_FRAME}')

	assert result['success'] is True
	assert result['face_detected'] is False
	assert result['eye_contact'] is False
	assert result['gaze_direction'] == 'missing'
	assert result['analysis_status'] == 'no_face_detected'


def test_decode_base64_frame_rejects_invalid_payload(monkeypatch):
	monkeypatch.setattr(eye_contact, 'np', SimpleNamespace(frombuffer=lambda decoded, dtype: [1]))
	monkeypatch.setattr(eye_contact, 'cv2', SimpleNamespace(IMREAD_COLOR=1, imdecode=lambda array, flag: object()))

	with pytest.raises(eye_contact.EyeContactAnalysisError):
		eye_contact._decode_base64_frame('not-base64')


def test_decode_base64_frame_rejects_empty_payload(monkeypatch):
	monkeypatch.setattr(eye_contact, 'np', SimpleNamespace(frombuffer=lambda decoded, dtype: []))
	monkeypatch.setattr(eye_contact, 'cv2', SimpleNamespace(IMREAD_COLOR=1, imdecode=lambda array, flag: object()))

	with pytest.raises(eye_contact.EyeContactAnalysisError):
		eye_contact._decode_base64_frame('')


def test_eye_contact_endpoint_returns_success_payload(client, monkeypatch):
	monkeypatch.setattr(
		eye_contact,
		'analyze_webcam_frame',
		lambda frame: {
			'success': True,
			'face_detected': True,
			'face_count': 1,
			'eyes_visible': True,
			'eye_contact': True,
			'eye_contact_score': 87,
			'gaze_direction': 'center',
			'head_pose': 'forward',
			'analysis_status': 'focused',
			'confidence': 0.91,
			'timestamp': '2026-06-12T12:00:00+00:00',
			'session_stats': {
				'total_frames': 1,
				'eye_contact_frames': 1,
				'off_screen_frames': 0,
				'average_eye_contact_score': 87.0,
				'eye_contact_percentage': 100.0,
				'history': [],
			},
		},
	)

	response = client.post('/api/analytics/eye-contact', json={'frame': VALID_FRAME})
	payload = response.get_json()

	assert response.status_code == 200
	assert payload['eye_contact'] is True
	assert payload['eye_contact_score'] == 87
	assert payload['gaze_direction'] == 'center'
	assert payload['head_pose'] == 'forward'
	assert payload['session_stats']['eye_contact_percentage'] == 100.0


def test_eye_contact_endpoint_rejects_missing_frame(client):
	response = client.post('/api/analytics/eye-contact', json={})

	assert response.status_code == 400
	assert response.get_json()['error'] == 'frame is required'


def test_eye_contact_endpoint_handles_multiple_faces(client, monkeypatch):
	monkeypatch.setattr(
		eye_contact,
		'analyze_webcam_frame',
		lambda frame: (_ for _ in ()).throw(eye_contact.EyeContactAnalysisError('Multiple faces detected in webcam frame.')),
	)

	response = client.post('/api/analytics/eye-contact', json={'frame': VALID_FRAME})

	assert response.status_code == 422
	assert response.get_json()['error'] == 'Multiple faces detected in webcam frame.'
