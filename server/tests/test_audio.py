from __future__ import annotations

from modules.audio_processor import detect_audio_format, extract_audio_metadata, validate_audio_content



def test_audio_validation_and_format_detection():
    payload = b'ID3' + b'\x00' * 100
    fmt = validate_audio_content(payload, filename='demo.mp3')
    assert fmt == 'mp3'
    assert detect_audio_format(filename='demo.mp3') == 'mp3'



def test_audio_metadata_contains_basics():
    payload = b'ID3' + b'\x00' * 200
    metadata = extract_audio_metadata(payload, filename='demo.mp3')
    assert metadata.format == 'mp3'
    assert metadata.file_size_bytes == len(payload)
