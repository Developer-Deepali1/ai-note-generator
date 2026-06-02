from __future__ import annotations

from typing import Any


def transcribe_payload(payload: dict[str, Any]) -> dict[str, Any]:
	transcript = str(payload.get('transcript') or payload.get('text') or '').strip()
	if transcript:
		return {
			'source': 'text',
			'transcript': transcript,
			'confidence': 1.0,
			'notes': 'Transcript supplied directly in the request payload.',
		}

	audio_reference = (
		payload.get('audio_url')
		or payload.get('audio_file')
		or payload.get('filename')
		or payload.get('path')
		or ''
	)
	return {
		'source': 'audio',
		'transcript': '',
		'confidence': 0.0,
		'audio_reference': audio_reference,
		'notes': 'No text transcript provided. Hook this module up to a real STT provider for audio decoding.',
	}


def transcribe_text(text: str) -> dict[str, Any]:
	return transcribe_payload({'text': text})
