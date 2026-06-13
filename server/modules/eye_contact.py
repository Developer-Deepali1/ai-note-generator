from __future__ import annotations

import base64
import binascii
import math
import re
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from utils.logger import get_logger

try:  # pragma: no cover - optional production dependency
	import cv2
except Exception:  # noqa: BLE001 - optional dependency guard
	cv2 = None

try:  # pragma: no cover - optional production dependency
	import mediapipe as mp
except Exception:  # noqa: BLE001 - optional dependency guard
	mp = None

try:  # pragma: no cover - optional production dependency
	import numpy as np
except Exception:  # noqa: BLE001 - optional dependency guard
	np = None

_LOGGER = get_logger('ai_note_generator.modules.eye_contact')
_DATA_URL_PREFIX = re.compile(r'^data:image/[^;]+;base64,', re.IGNORECASE)
_MAX_FRAME_WIDTH = 640
_SESSION_HISTORY_LIMIT = 60
_EYE_VISIBLE_THRESHOLD = 0.08
_GAZE_CENTER_THRESHOLD = 0.18
_GAZE_OFF_SCREEN_THRESHOLD = 0.34
_HEAD_POSE_THRESHOLD = 12.0

_LEFT_EYE_OUTER = 33
_LEFT_EYE_INNER = 133
_LEFT_EYE_TOP = 159
_LEFT_EYE_BOTTOM = 145
_LEFT_IRIS = (468, 469, 470, 471, 472)

_RIGHT_EYE_OUTER = 362
_RIGHT_EYE_INNER = 263
_RIGHT_EYE_TOP = 386
_RIGHT_EYE_BOTTOM = 374
_RIGHT_IRIS = (473, 474, 475, 476, 477)

_SESSION_LOCK = threading.Lock()


class EyeContactAnalysisError(RuntimeError):
	"""Raised when webcam eye-contact analysis cannot be completed."""


@dataclass
class EyeContactSessionTracker:
	total_frames: int = 0
	eye_contact_frames: int = 0
	off_screen_frames: int = 0
	total_eye_contact_score: float = 0.0
	history: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=_SESSION_HISTORY_LIMIT))
	last_face_detected: bool | None = None
	last_eye_contact: bool | None = None

	def update(self, sample: dict[str, Any]) -> dict[str, Any]:
		self.total_frames += 1
		self.total_eye_contact_score += float(sample.get('eye_contact_score', 0) or 0)

		face_detected = bool(sample.get('face_detected'))
		eye_contact = bool(sample.get('eye_contact'))
		if eye_contact:
			self.eye_contact_frames += 1
		else:
			self.off_screen_frames += 1

		if self.last_face_detected is not None and self.last_face_detected != face_detected:
			_LOGGER.info('Face detected state changed.', face_detected=face_detected)
		if self.last_eye_contact is not None and self.last_eye_contact != eye_contact:
			_LOGGER.info('Eye contact state changed.', eye_contact=eye_contact)

		average_score = self.average_eye_contact_score
		_LOGGER.info(
			'Eye contact frame processed.',
			total_frames=self.total_frames,
			eye_contact_frames=self.eye_contact_frames,
			off_screen_frames=self.off_screen_frames,
			average_eye_contact_score=average_score,
			eye_contact_percentage=self.eye_contact_percentage,
		)

		self.history.append(
			{
				'timestamp': sample.get('timestamp'),
				'eye_contact': eye_contact,
				'eye_contact_score': sample.get('eye_contact_score', 0),
				'gaze_direction': sample.get('gaze_direction', 'unknown'),
				'head_pose': sample.get('head_pose', 'unknown'),
				'analysis_status': sample.get('analysis_status', 'unknown'),
			}
		)
		self.last_face_detected = face_detected
		self.last_eye_contact = eye_contact
		return self.snapshot()

	@property
	def average_eye_contact_score(self) -> float:
		if self.total_frames == 0:
			return 0.0
		return round(self.total_eye_contact_score / self.total_frames, 1)

	@property
	def eye_contact_percentage(self) -> float:
		if self.total_frames == 0:
			return 0.0
		return round((self.eye_contact_frames / self.total_frames) * 100.0, 1)

	def snapshot(self) -> dict[str, Any]:
		return {
			'total_frames': self.total_frames,
			'eye_contact_frames': self.eye_contact_frames,
			'off_screen_frames': self.off_screen_frames,
			'average_eye_contact_score': self.average_eye_contact_score,
			'eye_contact_percentage': self.eye_contact_percentage,
			'history': list(self.history),
		}


_SESSION_TRACKER = EyeContactSessionTracker()


def reset_eye_contact_session() -> None:
	global _SESSION_TRACKER
	with _SESSION_LOCK:
		_SESSION_TRACKER = EyeContactSessionTracker()


def analyze_webcam_frame(frame: str) -> dict[str, Any]:
	"""Analyze a Base64 webcam frame and return eye-contact analytics."""
	if cv2 is None or np is None or mp is None:
		raise EyeContactAnalysisError('MediaPipe/OpenCV dependencies are unavailable.')

	image = _decode_base64_frame(frame)
	prepared = _resize_frame(image)
	face_mesh = _create_face_mesh()
	rgb_frame = cv2.cvtColor(prepared, cv2.COLOR_BGR2RGB)
	analysis = face_mesh.process(rgb_frame)
	faces = list(getattr(analysis, 'multi_face_landmarks', []) or [])
	timestamp = datetime.now(timezone.utc).isoformat()

	if len(faces) > 1:
		raise EyeContactAnalysisError('Multiple faces detected in webcam frame.')

	if not faces:
		sample = {
			'success': True,
			'face_detected': False,
			'face_count': 0,
			'eyes_visible': False,
			'eye_contact': False,
			'eye_contact_score': 0,
			'gaze_direction': 'missing',
			'head_pose': 'missing',
			'analysis_status': 'no_face_detected',
			'confidence': 0.0,
			'timestamp': timestamp,
		}
		with _SESSION_LOCK:
			session_stats = _SESSION_TRACKER.update(sample)
		return {**sample, 'session_stats': session_stats}

	landmarks = getattr(faces[0], 'landmark', None)
	if not landmarks:
		raise EyeContactAnalysisError('Face landmarks are unavailable.')

	face_metrics = _analyze_face_landmarks(landmarks, prepared.shape[1], prepared.shape[0])
	face_metrics['face_detected'] = True
	face_metrics['face_count'] = 1
	eye_contact = _is_eye_contact(face_metrics)
	confidence = _compute_confidence(face_metrics, eye_contact)
	status = _derive_status(face_metrics, eye_contact, confidence)
	score = _compute_eye_contact_score(face_metrics, eye_contact, confidence)
	sample = {
		'success': True,
		'face_detected': True,
		'face_count': 1,
		'eyes_visible': face_metrics['eyes_visible'],
		'eye_contact': eye_contact,
		'eye_contact_score': score,
		'gaze_direction': face_metrics['gaze_direction'],
		'head_pose': face_metrics['head_pose'],
		'analysis_status': status,
		'confidence': confidence,
		'timestamp': timestamp,
	}

	with _SESSION_LOCK:
		session_stats = _SESSION_TRACKER.update(sample)

	_LOGGER.info(
		'Eye contact analysis completed.',
		face_detected=True,
		eye_contact=eye_contact,
		gaze_direction=face_metrics['gaze_direction'],
		head_pose=face_metrics['head_pose'],
		eye_contact_score=score,
		average_session_score=session_stats['average_eye_contact_score'],
	)
	return {**sample, 'session_stats': session_stats}


def _decode_base64_frame(frame: str) -> Any:
	if not isinstance(frame, str) or not frame.strip():
		raise EyeContactAnalysisError('frame must be a non-empty base64 string.')
	if np is None or cv2 is None:
		raise EyeContactAnalysisError('NumPy/OpenCV dependencies are unavailable.')

	cleaned = _DATA_URL_PREFIX.sub('', frame.strip())
	cleaned = _pad_base64(cleaned)

	try:
		decoded = base64.b64decode(cleaned, validate=True)
	except (ValueError, binascii.Error) as exc:
		raise EyeContactAnalysisError('Invalid base64 frame payload.') from exc

	array = np.frombuffer(decoded, dtype=np.uint8)
	if getattr(array, 'size', len(array)) == 0:
		raise EyeContactAnalysisError('Decoded frame payload is empty.')

	image = cv2.imdecode(array, cv2.IMREAD_COLOR)
	if image is None:
		raise EyeContactAnalysisError('Unable to decode webcam frame into an image.')
	return image


def _pad_base64(value: str) -> str:
	missing = len(value) % 4
	if missing:
		value += '=' * (4 - missing)
	return value


def _resize_frame(image: Any) -> Any:
	height, width = image.shape[:2]
	if width <= _MAX_FRAME_WIDTH:
		return image
	scale = _MAX_FRAME_WIDTH / float(width)
	new_height = max(1, int(height * scale))
	return cv2.resize(image, (_MAX_FRAME_WIDTH, new_height), interpolation=cv2.INTER_AREA)


def _create_face_mesh() -> Any:
	solutions = getattr(mp, 'solutions', None) if mp is not None else None
	face_mesh_module = getattr(solutions, 'face_mesh', None)
	if face_mesh_module is None:
		raise EyeContactAnalysisError('MediaPipe face mesh solution is unavailable.')
	return face_mesh_module.FaceMesh(
		static_image_mode=True,
		max_num_faces=2,
		refine_landmarks=True,
		min_detection_confidence=0.5,
		min_tracking_confidence=0.5,
	)


def _analyze_face_landmarks(landmarks: Any, width: int, height: int) -> dict[str, Any]:
	left_eye = _eye_geometry(
		landmarks,
		outer_index=_LEFT_EYE_OUTER,
		inner_index=_LEFT_EYE_INNER,
		top_index=_LEFT_EYE_TOP,
		bottom_index=_LEFT_EYE_BOTTOM,
		iris_indices=_LEFT_IRIS,
		width=width,
		height=height,
	)
	right_eye = _eye_geometry(
		landmarks,
		outer_index=_RIGHT_EYE_OUTER,
		inner_index=_RIGHT_EYE_INNER,
		top_index=_RIGHT_EYE_TOP,
		bottom_index=_RIGHT_EYE_BOTTOM,
		iris_indices=_RIGHT_IRIS,
		width=width,
		height=height,
	)
	head_pose, yaw, pitch, roll = _estimate_head_pose(landmarks, width, height)
	gaze_direction, gaze_alignment = _classify_gaze(left_eye, right_eye, head_pose, yaw, pitch)
	eyes_visible = left_eye['visible'] and right_eye['visible']
	return {
		'left_eye': left_eye,
		'right_eye': right_eye,
		'eyes_visible': eyes_visible,
		'gaze_direction': gaze_direction,
		'gaze_alignment': gaze_alignment,
		'head_pose': head_pose,
		'head_pose_angles': {'yaw': yaw, 'pitch': pitch, 'roll': roll},
	}


def _eye_geometry(
	landmarks: Any,
	*,
	outer_index: int,
	inner_index: int,
	top_index: int,
	bottom_index: int,
	iris_indices: tuple[int, ...],
	width: int,
	height: int,
) -> dict[str, Any]:
	outer = _landmark_point(landmarks, outer_index, width, height)
	inner = _landmark_point(landmarks, inner_index, width, height)
	top = _landmark_point(landmarks, top_index, width, height)
	bottom = _landmark_point(landmarks, bottom_index, width, height)
	iris_points = [_landmark_point(landmarks, index, width, height) for index in iris_indices]
	iris_center = _average_point(iris_points)
	eye_width = max(_distance(outer, inner), 1.0)
	eye_opening = _distance(top, bottom)
	visible = (eye_opening / eye_width) >= _EYE_VISIBLE_THRESHOLD
	x_min = min(outer['x'], inner['x'])
	x_max = max(outer['x'], inner['x'])
	y_min = min(top['y'], bottom['y'])
	y_max = max(top['y'], bottom['y'])
	horizontal_ratio = (iris_center['x'] - x_min) / max(x_max - x_min, 1.0)
	vertical_ratio = (iris_center['y'] - y_min) / max(y_max - y_min, 1.0)
	return {
		'outer': outer,
		'inner': inner,
		'top': top,
		'bottom': bottom,
		'iris_center': iris_center,
		'eye_width': eye_width,
		'eye_opening': eye_opening,
		'visible': visible,
		'horizontal_ratio': _clamp(horizontal_ratio, 0.0, 1.0),
		'vertical_ratio': _clamp(vertical_ratio, 0.0, 1.0),
	}


def _estimate_head_pose(landmarks: Any, width: int, height: int) -> tuple[str, float, float, float]:
	if cv2 is None or np is None:
		raise EyeContactAnalysisError('OpenCV/NumPy dependencies are unavailable.')

	image_points = np.array(
		[
			_landmark_point(landmarks, 1, width, height),
			_landmark_point(landmarks, 152, width, height),
			_landmark_point(landmarks, 33, width, height),
			_landmark_point(landmarks, 263, width, height),
			_landmark_point(landmarks, 61, width, height),
			_landmark_point(landmarks, 291, width, height),
		],
		dtype=np.float64,
	)
	model_points = np.array(
		[
			(0.0, 0.0, 0.0),
			(0.0, -63.6, -12.5),
			(-43.3, 32.7, -26.0),
			(43.3, 32.7, -26.0),
			(-28.9, -28.9, -24.1),
			(28.9, -28.9, -24.1),
		],
		dtype=np.float64,
	)
	center = (width / 2.0, height / 2.0)
	focal_length = float(width)
	camera_matrix = np.array(
		[
			[focal_length, 0.0, center[0]],
			[0.0, focal_length, center[1]],
			[0.0, 0.0, 1.0],
		],
		dtype=np.float64,
	)
	dist_coeffs = np.zeros((4, 1), dtype=np.float64)
	success, rotation_vector, _translation_vector = cv2.solvePnP(
		model_points,
		image_points,
		camera_matrix,
		dist_coeffs,
		flags=cv2.SOLVEPNP_ITERATIVE,
	)
	if not success:
		raise EyeContactAnalysisError('Unable to estimate head pose from the current frame.')
	rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
	pitch, yaw, roll = _rotation_matrix_to_euler(rotation_matrix)
	return _classify_head_pose(yaw, pitch), yaw, pitch, roll


def _rotation_matrix_to_euler(rotation_matrix: Any) -> tuple[float, float, float]:
	sy = math.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] + rotation_matrix[1, 0] * rotation_matrix[1, 0])
	singular = sy < 1e-6
	if not singular:
		x_angle = math.atan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
		y_angle = math.atan2(-rotation_matrix[2, 0], sy)
		z_angle = math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
	else:
		x_angle = math.atan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
		y_angle = math.atan2(-rotation_matrix[2, 0], sy)
		z_angle = 0.0
	return (
		math.degrees(x_angle),
		math.degrees(y_angle),
		math.degrees(z_angle),
	)


def _classify_head_pose(yaw: float, pitch: float) -> str:
	if pitch <= -_HEAD_POSE_THRESHOLD:
		return 'up'
	if pitch >= _HEAD_POSE_THRESHOLD:
		return 'down'
	if yaw <= -_HEAD_POSE_THRESHOLD:
		return 'left'
	if yaw >= _HEAD_POSE_THRESHOLD:
		return 'right'
	return 'forward'


def _classify_gaze(left_eye: dict[str, Any], right_eye: dict[str, Any], head_pose: str, yaw: float, pitch: float) -> tuple[str, float]:
	horizontal_ratio = (left_eye['horizontal_ratio'] + right_eye['horizontal_ratio']) / 2.0
	vertical_ratio = (left_eye['vertical_ratio'] + right_eye['vertical_ratio']) / 2.0
	horizontal_offset = abs(horizontal_ratio - 0.5)
	vertical_offset = abs(vertical_ratio - 0.5)
	horizontal_alignment = max(0.0, 1.0 - min(1.0, horizontal_offset / _GAZE_OFF_SCREEN_THRESHOLD))
	vertical_alignment = max(0.0, 1.0 - min(1.0, vertical_offset / _GAZE_OFF_SCREEN_THRESHOLD))
	gaze_alignment = round((horizontal_alignment * 0.68) + (vertical_alignment * 0.32), 3)

	if gaze_alignment >= (1.0 - _GAZE_CENTER_THRESHOLD) and head_pose == 'forward':
		return 'center', gaze_alignment
	if pitch <= -_HEAD_POSE_THRESHOLD or vertical_ratio <= 0.3:
		return 'up', gaze_alignment
	if pitch >= _HEAD_POSE_THRESHOLD or vertical_ratio >= 0.7:
		return 'down', gaze_alignment
	if yaw <= -_HEAD_POSE_THRESHOLD or horizontal_ratio <= 0.35:
		return 'left', gaze_alignment
	if yaw >= _HEAD_POSE_THRESHOLD or horizontal_ratio >= 0.65:
		return 'right', gaze_alignment
	return 'center', gaze_alignment


def _is_eye_contact(metrics: dict[str, Any]) -> bool:
	return (
		metrics['eyes_visible']
		and metrics['head_pose'] == 'forward'
		and metrics['gaze_direction'] == 'center'
		and metrics['gaze_alignment'] >= 0.65
	)


def _compute_confidence(metrics: dict[str, Any], eye_contact: bool) -> float:
	eye_visibility = 1.0 if metrics['eyes_visible'] else 0.2
	head_alignment = 1.0 if metrics['head_pose'] == 'forward' else 0.25
	gaze_alignment = float(metrics['gaze_alignment'])
	contact_bonus = 0.15 if eye_contact else 0.0
	confidence = (eye_visibility * 0.25) + (head_alignment * 0.25) + (gaze_alignment * 0.5) + contact_bonus
	return round(_clamp(confidence, 0.0, 1.0), 3)


def _compute_eye_contact_score(metrics: dict[str, Any], eye_contact: bool, confidence: float) -> int:
	face_score = 1.0
	eye_visibility = 1.0 if metrics['eyes_visible'] else 0.2
	gaze_alignment = float(metrics['gaze_alignment'])
	head_alignment = 1.0 if metrics['head_pose'] == 'forward' else 0.3
	contact_multiplier = 1.0 if eye_contact else 0.35
	raw_score = (
		(face_score * 0.2)
		+ (eye_visibility * 0.25)
		+ (gaze_alignment * 0.35)
		+ (head_alignment * 0.2)
	)
	raw_score = (raw_score * 0.85) + (confidence * 0.15)
	return int(round(_clamp(raw_score * contact_multiplier, 0.0, 1.0) * 100))


def _derive_status(metrics: dict[str, Any], eye_contact: bool, confidence: float) -> str:
	if eye_contact:
		return 'focused'
	if not metrics['face_detected']:
		return 'no_face_detected'
	if not metrics['eyes_visible']:
		return 'partial_visibility'
	if confidence < 0.45:
		return 'low_confidence'
	return 'off_screen'


def _landmark_point(landmarks: Any, index: int, width: int, height: int) -> dict[str, float]:
	try:
		landmark = landmarks[index]
	except (IndexError, TypeError) as exc:
		raise EyeContactAnalysisError('Face landmarks are incomplete.') from exc
	return {
		'x': float(getattr(landmark, 'x')) * float(width),
		'y': float(getattr(landmark, 'y')) * float(height),
		'z': float(getattr(landmark, 'z', 0.0)),
	}


def _average_point(points: list[dict[str, float]]) -> dict[str, float]:
	return {
		'x': sum(point['x'] for point in points) / len(points),
		'y': sum(point['y'] for point in points) / len(points),
		'z': sum(point['z'] for point in points) / len(points),
	}


def _distance(first: dict[str, float], second: dict[str, float]) -> float:
	return math.sqrt((first['x'] - second['x']) ** 2 + (first['y'] - second['y']) ** 2)


def _clamp(value: float, minimum: float, maximum: float) -> float:
	return max(minimum, min(maximum, value))
