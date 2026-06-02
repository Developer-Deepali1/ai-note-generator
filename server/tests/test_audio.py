from __future__ import annotations

import wave

from modules.audio_processor import inspect_audio_reference, process_audio_payload
from modules.speech_to_text import transcribe_payload


def test_transcribe_payload_accepts_direct_text():
	result = transcribe_payload({'text': '  We discussed the roadmap.  '})

	assert result['status'] == 'completed'
	assert result['source'] == 'text'
	assert result['transcript'] == 'We discussed the roadmap.'


def test_transcribe_payload_reports_invalid_audio_format():
	result = transcribe_payload({'audio_file': 'meeting.txt'})

	assert result['status'] == 'failed'
	assert 'Unsupported audio format' in result['error']


def test_audio_processor_reads_wav_metadata(tmp_path):
	path = tmp_path / 'sample.wav'
	with wave.open(str(path), 'wb') as audio:
		audio.setnchannels(1)
		audio.setsampwidth(2)
		audio.setframerate(8000)
		audio.writeframes(b'\x00\x00' * 8000)

	metadata = inspect_audio_reference(str(path))
	processed = process_audio_payload({'audio_file': str(path)})

	assert metadata['is_supported'] is True
	assert metadata['duration_seconds'] == 1.0
	assert metadata['sample_rate'] == 8000
	assert processed['transcription']['status'] in {'queued', 'completed'}
